import traceback
import uuid
from typing import Any, Dict, Optional, Union
from contextvars import ContextVar
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError as PydanticValidationError

from src.core.config_log import logger


request_id_ctx: ContextVar[str] = ContextVar("request_id", default="system")

class PetCoreException(Exception):
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        details: Any = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers
        super().__init__(self.message)

class ValidationError(PetCoreException):
    def __init__(self, message: str, field: Optional[str] = None, details: Any = None):
        final_details = details or ({"field": field} if field else None)
        super().__init__(message=message, status_code=400, details=final_details)

class AuthenticationError(PetCoreException):
    def __init__(self, message: str = "Необходима авторизация"):
        super().__init__(message=message, status_code=401, headers={"WWW-Authenticate": "Bearer"})

class AuthorizationError(PetCoreException):
    def __init__(self, message: str = "Доступ запрещен"):
        super().__init__(message=message, status_code=403)

class NotFoundError(PetCoreException):
    def __init__(self, resource: str = "Ресурс", multiple: bool = False):
        if multiple:
            super().__init__(message=f"{resource} не найдены", status_code=200)
        else:
            super().__init__(message=f"{resource} не найден", status_code=200)

class ConflictError(PetCoreException):
    def __init__(self, message: str, details: Any = None):
        super().__init__(message=message, status_code=409, details=details)

class InternalServerError(PetCoreException):
    def __init__(self, message: str = "Внутренняя ошибка сервера"):
        super().__init__(message=message, status_code=500)

class TooManyRequestsError(PetCoreException):
    def __init__(self, message: str = "Слишком много запросов"):
        super().__init__(message=message, status_code=429)

def translate_pydantic_error(error: Dict[str, Any]) -> str:
    """Перевод ошибок Pydantic V2 на человеческий русский"""
    err_type = error.get("type")
    msg = error.get("msg", "")
    ctx = error.get("ctx", {})

    if any(c in msg for c in "а-яА-Я"):
        return msg.replace("Value error, ", "").replace("Assertion failed, ", "")

    translations = {
        "json_invalid": "Некорректный формат JSON",
        "missing": "Поле обязательно для заполнения",
        "email_type": "Некорректный адрес электронной почты",
        "string_too_short": f"Минимальная длина — {ctx.get('min_length')} симв." if ctx else "Слишком короткое значение",
        "string_too_long": f"Максимальная длина — {ctx.get('max_length')} симв." if ctx else "Слишком длинное значение",
        "too_short": "Слишком короткое значение",
        "enum": f"Допустимые значения: {ctx.get('expected')}" if ctx else "Выберите значение из списка",
        "int_parsing": "Ожидалось целое число",
        "float_parsing": "Ожидалось число",
        "bool_parsing": "Ожидалось логическое значение (true/false)",
        "date_parsing": "Некорректный формат даты",
        "datetime_parsing": "Некорректный формат даты и времени",
        "greater_than": f"Значение должно быть больше {ctx.get('gt')}" if ctx else "Значение слишком мало",
        "less_than": f"Значение должно быть меньше {ctx.get('lt')}" if ctx else "Значение слишком велико",
        "date_from_datetime_inexact": "В полях, предназначенных для отображения дат, время должно быть равно нулю — например, это должны быть точные даты."
    }

    return translations.get(err_type, msg.replace("Value error, ", ""))

def create_error_response(status_code: int, message: str, details: Any = None) -> JSONResponse:
    """Унифицированный формат ответа с ошибкой, включая request_id для трассировки"""
    req_id = request_id_ctx.get()
    content = {
        "error": {
            "code": status_code,
            "message": message,
            "request_id": req_id
        }
    }
    if details:
        content["error"]["details"] = details
        
    return JSONResponse(status_code=status_code, content=content)


async def validation_exception_handler(request: Request, exc: Union[RequestValidationError, PydanticValidationError]):
    """Обрабатывает ошибки валидации данных и возвращает структурированный ответ с переводом сообщений"""
    formatted_errors = []
    for error in exc.errors():
        loc = list(error.get("loc", []))
        field_path = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else ".".join(str(x) for x in loc)
        
        formatted_errors.append({
            "field": field_path or "non_field_error",
            "message": translate_pydantic_error(error),
            "type": error.get("type")
        })

    log_message = f"Validation Error on {request.url.path}: fields={[e['field'] for e in formatted_errors]}"
    logger.info(log_message)
    return create_error_response(422, "Ошибка валидации данных", formatted_errors)

async def user_api_exception_handler(request: Request, exc: PetCoreException):
    """Обрабатывает пользовательские исключения и возвращает структурированный ответ с сообщением и деталями"""
    logger.info(f"API Error on {request.url.path}: {exc.status_code} - {exc.message}")
    return create_error_response(exc.status_code, exc.message, exc.details)

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Обрабатывает HTTP-исключения и возвращает структурированный ответ"""
    msg = {404: "Ресурс не найден", 405: "Метод не разрешен"}.get(exc.status_code, str(exc.detail))
    return create_error_response(exc.status_code, msg)

async def general_exception_handler(request: Request, exc: Exception):
    """Обрабатывает общие исключения и возвращает структурированный ответ"""
    logger.error(f"Критично: {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
    return create_error_response(500, "Внутренняя ошибка сервера")


async def request_id_middleware(request: Request, call_next):
    """Middleware для генерации и добавления ID запроса"""
    req_id = str(uuid.uuid4())
    token = request_id_ctx.set(req_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    finally:
        request_id_ctx.reset(token)

def setup_exception_handlers(app: FastAPI):
    """Настраивает глобальные обработчики исключений для приложения"""
    app.middleware("http")(request_id_middleware)
    app.add_exception_handler(PetCoreException, user_api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)