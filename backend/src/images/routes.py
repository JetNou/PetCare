from pathlib import Path
import re
from typing import Optional
from fastapi import APIRouter, Depends, Request

from src.auth.auth import get_current_user
from src.db.models import User
from src.core.config_app import settings
from src.core.config_log import logger
from src.core.exceptions import AuthorizationError, ValidationError
from src.images.utils import _serve_file
from src.utils.decorators import cache, security_headers_check


router = APIRouter()

STANDARD_FILES = {
    "user-standart.png",
    "pet-standart.png",
}

def validate_file_path(file_path: str, allowed_extensions: set[str]) -> bool:
    """
    Проверка безопасности пути и расширения.
    """
    if not file_path or len(file_path) > 255:
        return False

    if '..' in file_path or file_path.startswith(('/', '\\')):
        return False

    dangerous_patterns = r'[<>:"|?*]'
    if re.search(dangerous_patterns, file_path):
        return False

    ext = Path(file_path).suffix.lower()
    if ext not in allowed_extensions:
        return False

    return True


def _is_admin(user: User) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return getattr(user, "role_id", None) == 1


def _is_standard_file(filename: str) -> bool:
    """Проверяет, является ли файл стандартным"""
    return filename in STANDARD_FILES

def _check_image_access_permission(
    file_type: str,
    actual_file: str,
    current_user: User,
) -> None:
    """
    Проверяет доступ к приватным изображениям.
    Стандартные файлы должны отсеиваться раньше, до вызова этой функции
    """
    is_admin = _is_admin(current_user)

    if file_type == "pets":
        if not actual_file.startswith("pet_"):
            raise AuthorizationError("Доступ запрещен")

        if not is_admin:
            expected_prefix = f"pet_{current_user.user_id}_"
            if not actual_file.startswith(expected_prefix):
                logger.warning(f"Доступ запрещён: пользователь {current_user.user_id} попытался получить доступ к изображению питомца {actual_file}")
                raise AuthorizationError("Доступ запрещен")

    elif file_type == "avatars":
        if not actual_file.startswith("user-"):
            raise AuthorizationError("Доступ запрещен")

        if not is_admin and not actual_file.startswith(f"user-{current_user.user_id}-"):
            logger.warning(f"Доступ запрещён: пользователь {current_user.user_id} попытался получить доступ к аватару {actual_file}")
            raise AuthorizationError("Доступ запрещен")

    else:
        raise AuthorizationError("Доступ запрещен")


@router.get("/public/{file:path}", status_code=200)
@security_headers_check
@cache(ttl=60, key_prefix="public_photo")
async def public_image(file: str, request: Request):
    """
    Публичные изображения: только файлы из корня uploads/ без подпапок
    logo.png, favicon.ico и т.п. доступны всем, но не допускаются пути типа pets/pet-standart.png или avatars/user-standart.png
    """
    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico"}

    if not validate_file_path(file, allowed_ext):
        logger.warning(f"Безопасность: Попытка указать недопустимый публичный путь: {file}")
        raise ValidationError("Неверный путь к файлу")

    if "/" in file or "\\" in file:
        logger.warning(f"Доступ запрещен: Попытка доступа к общедоступному файлу в подкаталоге: {file}")
        raise AuthorizationError("Доступ запрещен")

    return await _serve_file(Path(settings.UPLOAD_DIR), file)

@router.get("/private/{file:path}", status_code=200)
@security_headers_check
async def private_image(
    file: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Приватные изображения питомцев и аватарок.

    Правила:
    - avatars/user-standart.png доступен всем
    - pets/pet-standart.png доступен всем
    - остальные файлы доступны только владельцу или админу
    """
    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}

    if not validate_file_path(file, allowed_ext):
        user_id = getattr(current_user, "user_id", "anonymous")
        logger.warning(f"Безопасность: попытка доступа к недопустимому приватному пути {file} пользователем с User_ID {user_id}")
        raise ValidationError("Неверный путь к файлу")

    if file.startswith("avatars/"):
        actual_file = file.removeprefix("avatars/")

        if _is_standard_file(actual_file):
            return await _serve_file(Path(settings.AVATAR_DIR), actual_file)

        if current_user is None:
            raise ValidationError("Требуется аутентификация")

        _check_image_access_permission("avatars", actual_file, current_user)
        return await _serve_file(Path(settings.AVATAR_DIR), actual_file)

    if file.startswith("pets/"):
        actual_file = file.removeprefix("pets/")

        if _is_standard_file(actual_file):
            return await _serve_file(Path(settings.UPLOAD_DIR) / "pets", actual_file)

        if current_user is None:
            raise ValidationError("Требуется аутентификация")

        _check_image_access_permission("pets", actual_file, current_user)
        return await _serve_file(Path(settings.UPLOAD_DIR) / "pets", actual_file)

    logger.warning(f"Доступ запрещен: Неверная структура пути {file} пользователем с User_ID {current_user.user_id}")
    raise AuthorizationError("Доступ запрещен - используйте pets/ или avatars/ префикс")