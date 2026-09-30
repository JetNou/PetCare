import functools
from enum import Enum, IntEnum
import hashlib
from typing import Callable, Any, Tuple, TypeVar, Optional

from fastapi import Request, HTTPException
from src.core.exceptions import AuthenticationError, AuthorizationError, TooManyRequestsError
from src.core.config_log import logger
from src.cache.redis_service import redis_service


F = TypeVar("F", bound=Callable[..., Any])

BAD_USER_AGENTS = {"sqlmap", "nikto", "burp", "nmap", "shell", "python-requests", "nessus", "acunetix"}

class UserStatus(str, Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    BANNED = "banned"
    DELETED = "deleted"

class UserRole(IntEnum):
    ADMIN = 1
    USER = 3
    
    
def _get_context_data(kwargs: dict) -> tuple[Optional[Request], Optional[Any]]:
    """
    Быстрое извлечение Request и current_user из kwargs.
    В FastAPI зависимости (Depends) всегда попадают в kwargs
    """
    request = kwargs.get("request")
    user = kwargs.get("current_user")
    return request, user

def security_headers_check(func: F) -> F:
    """
    Базовая защита: проверка User-Agent и IP (если требуется).
    Желательно применять как Middleware, но можно и как декоратор
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request, _ = _get_context_data(kwargs)

        if request:
            user_agent = request.headers.get("user-agent", "").lower()
            client_ip = request.client.host if request.client else "unknown"

            if any(agent in user_agent for agent in BAD_USER_AGENTS):
                logger.warning(f"[Security Alert] Блокировка {user_agent} с {client_ip}")
                raise AuthorizationError()

        return await func(*args, **kwargs)
    return wrapper

def rate_limit(limit: int = 5, period: int = 60) -> Callable[[F], F]:
    """
    Ограничение частоты запросов (Redis).
    Ключ формируется по: User ID -> Login -> IP
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request, user = _get_context_data(kwargs)
            
            key_part = None
            if user and hasattr(user, "user_id"):
                key_part = f"u:{user.user_id}"
            elif request and request.client:
                key_part = f"ip:{request.client.host}"
            
            if not key_part:
                return await func(*args, **kwargs)

            redis_key = f"rl:{func.__name__}:{key_part}"

            if not redis_service.is_connected:
                return await func(*args, **kwargs)

            try:
                current_count = await redis_service.incr(redis_key, amount=1, ttl=period)
                
                if current_count > limit:
                    logger.warning(f"[Rate Limit] Hit: {redis_key} ({current_count}/{limit})")
                    raise TooManyRequestsError("Слишком много запросов. Пожалуйста, попробуйте позже.")
            except (HTTPException, TooManyRequestsError):
                raise
            except Exception as e:
                logger.error(f"[Rate Limit] Ошибка (Redis упал?): {e}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def active_user_required(func: F) -> F:
    """Проверяет, что пользователь активен (ACTIVE) и не забанен/удален"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        _, user = _get_context_data(kwargs)

        if not user:
            raise AuthenticationError()
            
        user_status = getattr(user, "status", None)

        if user_status == UserStatus.REGISTERED:
             raise AuthorizationError("Email не подтвержден. Пожалуйста, подтвердите email для активации аккаунта.")

        if user_status == UserStatus.BANNED:
             logger.warning(f"[ActiveUserRequired] Попытка доступа заблокированного пользователя: ID {user.user_id}")
             raise AuthorizationError("Ваш аккаунт заблокирован")

        if user_status == UserStatus.DELETED:
             raise AuthorizationError("Ваш аккаунт удален")

        return await func(*args, **kwargs)
    return wrapper

def admin_required(func: F) -> F:
    """Требует роль ADMIN (1)"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        _, user = _get_context_data(kwargs)
        
        if not user or getattr(user, "role_id", 0) != UserRole.ADMIN:
            uid = user.user_id if user else "anon"
            logger.warning(f"[AdminRequired] Отказ в админском доступе: ID= {uid}")
            raise AuthorizationError("Требуются права администратора")
            
        return await func(*args, **kwargs)
    return wrapper

def registered_user_required(func: F) -> F:
    """Проверяет, что пользователь зарегистрирован (REGISTERED) и не забанен/удален"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        _, user = _get_context_data(kwargs)

        if not user:
            raise AuthenticationError()
            
        if user.status != UserStatus.REGISTERED:
             raise AuthorizationError("Вы уже подтвердили почту.")

        if user.is_deleted:
             logger.warning(f"[RegisteredUserRequired] Попытка доступа заблокированного пользователя: ID {user.user_id}")
             raise AuthorizationError("Ваш аккаунт заблокирован")

        if user.status == UserStatus.DELETED:
             raise AuthorizationError("Ваш аккаунт удален")

        return await func(*args, **kwargs)
    return wrapper

def cache(ttl: int, key_prefix: str = "", ignore_args: Tuple[str, ...] = ()):
    """Декоратор для кэширования результатов асинхронных функций"""
    from src.cache.redis_service import redis_service
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not redis_service.is_connected:
                return await func(*args, **kwargs)

            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ignore_args}

            filtered_args = args[1:] if args and hasattr(args[0], '__dict__') else args
            
            hash_data = f"{filtered_args}{filtered_kwargs}"
            args_hash = hashlib.blake2b(hash_data.encode(), digest_size=16).hexdigest()
            cache_key = f"{prefix}:{args_hash}"

            cached = await redis_service.get_json(cache_key)
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)

            if result is not None:
                await redis_service.set_json(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator

