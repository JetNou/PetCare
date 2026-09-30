import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Form, Request, UploadFile, File, Query
from pydantic import EmailStr, ValidationError as PydanticValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config_app import settings
from src.core.config_log import logger
from src.auth import get_current_user
from src.db.database import get_db
from src.db.models import User, UserStatus, UserToken
from src.users.schemas import ResetPasswordConfirm, UserProfile, UserUpdate, LOGIN_REGEX, NAME_REGEX
from src.cache.redis_service import redis_service
from src.images.utils import save_uploaded_file
from src.utils.user import _validate_file_upload
from src.utils.decorators import active_user_required, cache, rate_limit, security_headers_check, registered_user_required
from src.core.exceptions import AuthorizationError, ValidationError, NotFoundError, ConflictError, InternalServerError
from src.utils.email import EmailService
from src.users.services import ActionService
from src.utils.token import TokenManager
from src.utils.password import pwd_manager


router = APIRouter()

@router.get("/", response_model=UserProfile,  status_code=200)
@security_headers_check
@active_user_required
@cache(ttl=600, key_prefix="user_profile")
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает профиль"""
    
    try:
        result = await db.execute(select(User).where(User.user_id == current_user.user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("Пользователь")

        return UserProfile.model_validate(user)
    
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Не удалось получить профиль: {e}")
        raise InternalServerError("Ошибка при получении профиля")

@router.patch("/", response_model=UserProfile,  status_code=200)
@security_headers_check
@rate_limit(limit=10, period=60)
@active_user_required
async def update_profile(
    request: Request,
    user_login: Optional[str] = Form(None),
    user_full_name: Optional[str] = Form(None),
    user_email: Optional[EmailStr] = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновляет профиль"""
    
    user_id = current_user.user_id
    updates: Dict[str, Any] = {}

    user_login_clean = user_login.strip() if user_login else None
    user_full_name_clean = user_full_name.strip() if user_full_name else None
    user_email_clean = user_email.strip() if user_email else None

    try:
        UserUpdate(
            user_login=user_login_clean,
            user_full_name=user_full_name_clean,
            user_email=user_email_clean,
        )
    except PydanticValidationError as e:
        raise ValidationError(str(e))

    if user_login_clean and user_login_clean != current_user.user_login:
        exists = await db.execute(select(User.user_id).where(User.user_login == user_login_clean).limit(1))
        if exists.scalar():
            raise ConflictError("Логин уже занят")
        updates["user_login"] = user_login_clean

    if user_full_name_clean and user_full_name_clean != current_user.user_full_name:
        updates["user_full_name"] = user_full_name_clean

    email_changed = False
    if user_email_clean and user_email_clean != current_user.user_email:
        exists = await db.execute(select(User.user_id).where(User.user_email == user_email_clean).limit(1))
        if exists.scalar():
            raise ConflictError("Email уже занят")
        
        updates["user_email"] = user_email_clean
        updates["status"] = UserStatus.REGISTERED
        email_changed = True

    if photo:
        await _validate_file_upload(photo)
        updates["user_avatar"] = await save_uploaded_file(photo, user_id, settings.AVATAR_DIR, "user")

    if not updates:
        return UserProfile.model_validate(current_user)

    try:
        stmt = update(User).where(User.user_id == user_id).values(**updates).returning(User)
        result = await db.execute(stmt)
        updated_user = result.scalar_one()
        await db.commit()

        if email_changed:
            raw_token = await TokenManager.create_user_token(db, user_id, "email_verification", settings.TOKEN_TTL_SECONDS)
            await EmailService.send_verification_email(updated_user.user_email, updated_user.user_full_name, raw_token)

        await redis_service.delete(f"user_profile")
        await redis_service.cache_user_profile(user_obj=updated_user, force=True)
        await ActionService.log_action(db, current_user.user_id, "Обновлен профиль")
        
        return UserProfile.model_validate(updated_user)

    except Exception as e:
        await db.rollback()
        logger.error(f"Не удалось обновить профиль: {e}")
        raise InternalServerError("Не удалось обновить данные")

@router.delete("/avatar", response_model=dict,  status_code=200)
@security_headers_check
@rate_limit(limit=10, period=60)
@active_user_required
async def delete_avatar(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить аватарку пользователя"""
    
    try:
        await db.execute(update(User).where(User.user_id == current_user.user_id).values(user_avatar="avatars/user-standart.png"))
        await db.commit()
        
        await redis_service.delete(f"user:profile:{current_user.user_id}")
        await ActionService.log_action(db, current_user.user_id, "Сброшен аватар пользователя")
        
        return {"message": "Аватарка удалена"}
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Не удалось удалить аватарку: {e}")
        raise InternalServerError("Ошибка удаления аватарки")
   
@router.delete("/", response_model=dict, status_code=200)
@security_headers_check
@rate_limit(limit=3, period=3600)
@active_user_required
async def delete_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Мягкое удаление профиля"""
    
    user_id = current_user.user_id

    try:
        await db.execute(
            update(User).where(User.user_id == user_id).values(is_deleted=True)
        )
        await db.commit()
        
        await redis_service.delete(f"user:profile:{user_id}")
        await ActionService.log_action(db, current_user.user_id, "Удален профиль пользователя")

        if current_user.user_email:
            ttl = settings.DELETE_USER_TTL_SECONDS
            raw_token = await TokenManager.create_user_token(db, user_id, "account_restore", ttl)
            expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).strftime("%Y-%m-%d %H:%M UTC")
            
            await EmailService.send_restore_email(
                current_user.user_email, 
                current_user.user_full_name, 
                raw_token, 
                expires
            )

        return {"detail": "Профиль удален. Инструкция по восстановлению отправлена на email."}
   
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка удаления профиля пользователя {user_id}: {e}")
        raise InternalServerError("Ошибка удаления профиля")


@router.post("/restore", response_model=dict, status_code=200)
@security_headers_check
@rate_limit(limit=5, period=3600)
async def restore_profile(
    request: Request,
    token: str = Query(..., description="Токен восстановления"),
    db: AsyncSession = Depends(get_db),
):
    """Восстановление профиля"""
    
    token_hash = TokenManager.hash_token(token)
    db_token = await TokenManager.get_token_by_hash(db, token_hash, "account_restore")
    
    if not db_token or db_token.consumed_at or db_token.expires_at < datetime.now(timezone.utc):
        raise ValidationError("Неверный, использованный или просроченный токен")

    try:
        user = await db.get(User, db_token.user_id)
        if not user:
            raise NotFoundError("Пользователь")

        user.is_deleted = False
        db_token.consumed_at = datetime.now(timezone.utc)
        await db.commit()
        await ActionService.log_action(db, user.user_id, "Восстановлен профиль пользователя")
            
        await redis_service.cache_user_profile(user_obj=user, force=True)
        return {"detail": "Аккаунт успешно восстановлен"}

    except NotFoundError:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка восстановления профиля: {e}")
        raise InternalServerError("Ошибка восстановления")


@router.post("/reset-password/request", response_model=dict, status_code=200)
@security_headers_check
@rate_limit(limit=3, period=3600)
@active_user_required
async def request_password_reset(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запрос на сброс пароля"""
    
    try:
        if not current_user.user_email:
            raise ValidationError("Email не привязан", field="user_email")

        raw_token = await TokenManager.create_user_token(
            db, current_user.user_id, "password_reset", settings.RESET_PASSWORD_TTL_SECONDS
        )

        await EmailService.send_reset_password_email(
            current_user.user_email,
            current_user.user_full_name,
            raw_token,
            "1 час"
        )

        await ActionService.log_action(db, current_user.user_id, "Запрошен сброс пароля")
        logger.info(f"Запрошен сброс пароля для user_id={current_user.user_id}")
        return {"detail": "Ссылка для сброса отправлена"}
    except Exception as e:
        logger.error(f"Ошибка при запросе сброса пароля: {e}")
        raise InternalServerError("Ошибка при запросе сброса пароля")

@router.post("/reset-password/confirm", response_model=dict, status_code=200)
@security_headers_check
@rate_limit(limit=5, period=3600)
async def confirm_password_reset(
    request: Request,
    form_data: ResetPasswordConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Подтверждение смены пароля"""
    
    token_hash = TokenManager.hash_token(form_data.token)
    
    try:
        q_token = select(UserToken).where(
            UserToken.token_hash == token_hash,
            UserToken.token_type == "password_reset",
            UserToken.consumed_at.is_(None)
        ).with_for_update()
        
        result = await db.execute(q_token)
        db_token = result.scalar_one_or_none()
        
        if not db_token or db_token.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Токен недействителен или просрочен")

        user = await db.get(User, db_token.user_id)
        if not user or user.is_deleted:
            raise NotFoundError("Пользователь")

        user.user_password_hash = pwd_manager.hash_password(form_data.new_password)
        db_token.consumed_at = datetime.now(timezone.utc)
        
        await db.commit()

        await asyncio.gather(
            redis_service.delete("user_profile"),
            redis_service.cache_user_profile(user_obj=user, force=True)
        )

        await ActionService.log_action(db, user.user_id, "Сброшен пароль пользователя")
        logger.info(f"Пароль изменен для user_id={user.user_id}")

        return {"detail": "Пароль изменен успешно"}
    
    except (ValidationError, NotFoundError):
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка подтверждения сброса пароля: {e}")
        raise InternalServerError("Ошибка сервера")
    

@router.get("/{user_id}", response_model=UserProfile)
@security_headers_check
@rate_limit(limit=20, period=60)
@active_user_required
@cache(ttl=600, key_prefix="user_profile_view")
async def get_user_profile(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение профиля пользователя по ID.
    - Admin: может получить профиль любого пользователя
    - User: может получить только свой профиль
    """
    if user_id <= 0:
        raise ValidationError("ID должен быть положительным числом", field="user_id")

    if current_user.role_id != 1 and current_user.user_id != user_id:
        raise AuthorizationError("Вы не имеете доступа к этому профилю")

    try:
        query = select(User).where(User.user_id == user_id, User.is_deleted == False)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("Пользователь")

        return UserProfile.model_validate(user)
    except (ValidationError, NotFoundError, AuthorizationError):
        raise
    except Exception as e:
        logger.error(f"Ошибка получения профиля пользователя (ID {user_id}): {e}")
        raise InternalServerError("Ошибка при получении профиля")
    
    

@router.put("/", response_model=UserProfile,  status_code=200)
@security_headers_check
@registered_user_required
@rate_limit(limit=10, period=60)
async def update_email(
    request: Request,
    user_email: EmailStr,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновляет email пользователя"""
    
    user_id = current_user.user_id
    updates: Dict[str, Any] = {}

    email_changed = False
    if user_email and user_email.strip() != current_user.user_email:
        user_email = user_email.strip()
        exists = await db.execute(select(User.user_id).where(User.user_email == user_email).limit(1))
        if exists.scalar():
            raise ConflictError("Email уже занят")
        
        updates["user_email"] = user_email
        updates["status"] = UserStatus.REGISTERED
        email_changed = True

    if not updates:
        return UserProfile.model_validate(current_user)

    try:
        stmt = update(User).where(User.user_id == user_id).values(**updates).returning(User)
        result = await db.execute(stmt)
        updated_user = result.scalar_one()
        await db.commit()

        if email_changed:
            raw_token = await TokenManager.create_user_token(db, user_id, "email_verification", settings.TOKEN_TTL_SECONDS)
            await EmailService.send_verification_email(updated_user.user_email, updated_user.user_full_name, raw_token)

        await redis_service.delete(f"user_profile")
        await redis_service.cache_user_profile(user_obj=updated_user, force=True)
        await ActionService.log_action(db, current_user.user_id, "Обновлен профиль")
        
        return UserProfile.model_validate(updated_user)

    except Exception as e:
        await db.rollback()
        logger.error(f"Не удалось обновить профиль: {e}")
        raise InternalServerError("Не удалось обновить данные")