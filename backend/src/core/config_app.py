import os
from pathlib import Path
from typing import Optional
from dotenv import find_dotenv, load_dotenv
from urllib.parse import quote_plus

from .config_log import logger


class Settings:
    """Конфигурация приложения, загруженная из переменных окружения"""
    
    PROJECT_NAME = "Pet Core"
    PROJECT_VERSION = "8.5.1"

    def __init__(self):
        if not load_dotenv(find_dotenv(), override=True):
            logger.warning("[ConfigApp] Не найден .env файл, используются переменные окружения или значения по умолчанию")

        # База Данных
        self.POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD")
        self.POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
        self.POSTGRES_DB: str = os.getenv("POSTGRES_DB", "PetCore_db")

        # Redis
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.REDIS_TTL: int = int(os.getenv("REDIS_TTL", 600))
        
        # CORS & SECURITY
        self.ALLOWED_ORIGINS: list = os.getenv(
            "ALLOWED_ORIGINS", 
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
        ).split(",")
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "")
        self.ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        self.PASSWORD_PEPPER: str = os.getenv("PASSWORD_PEPPER", "")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        # Пути и директории
        self.BACKEND_DIR = Path(__file__).resolve().parent.parent.parent 
        self.PROJECT_ROOT = self.BACKEND_DIR.parent
        upload_env = os.getenv("UPLOAD_DIR", "./uploads")
        base_upload_dir = Path(upload_env)
        if not base_upload_dir.is_absolute():
            self.UPLOAD_DIR = (self.PROJECT_ROOT / base_upload_dir).resolve()
        else:
            self.UPLOAD_DIR = base_upload_dir

        avatar_env = os.getenv("AVATAR_DIR", "./uploads/avatars")
        avatar_dir = Path(avatar_env)
        if not avatar_dir.is_absolute():
            self.AVATAR_DIR = (self.PROJECT_ROOT / avatar_dir).resolve()
        else:
            self.AVATAR_DIR = avatar_dir

        # ADMIN
        self.ADMIN_IMAGES: str = os.getenv("ADMIN_IMAGES", "avatars/user-1-admin.jpg")
        self.ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")
        self.ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")

        # Режим COOKIES
        self.COOKIE_MODE: bool = os.getenv("COOKIE_MODE", "false").lower() == "true"

        # URLs
        self.FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
        
        # EMAIL (SMTP)
        self.SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
        self.SMTP_USER: str = os.getenv("SMTP_USER", "")
        self.SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
        self.SMTP_FROM: str = os.getenv("SMTP_FROM", self.SMTP_USER)
        self.SMTP_USE_STARTTLS: bool = os.getenv("SMTP_USE_STARTTLS", "false").lower() == "true"
        self.SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
        
        # Токены
        self.TOKEN_TTL_SECONDS: int = int(os.getenv("TOKEN_TTL_SECONDS", "86400"))
        self.TOKEN_RESEND_MAX: int = int(os.getenv("TOKEN_RESEND_MAX", "5"))
        self.TOKEN_RESEND_WINDOW_SECONDS: int = int(os.getenv("TOKEN_RESEND_WINDOW_SECONDS", "86400"))
        self.RESET_PASSWORD_TTL_SECONDS: int = int(os.getenv("RESET_PASSWORD_TTL_SECONDS", "3600"))
        self.DELETE_USER_TTL_SECONDS: int = int(os.getenv("DELETE_USER_TTL_SECONDS", "604800"))
        self.VERIFICATION_TTL_SECONDS: int = int(os.getenv("VERIFICATION_TTL_SECONDS", "86400"))
        
        # Кэширование изображений
        self.IMAGE_CACHE_TTL: int = int(os.getenv("IMAGE_CACHE_TTL", "3600"))
        self.IMAGE_CACHE_MAX_BYTES: int = int(os.getenv("IMAGE_CACHE_MAX_BYTES", "500000"))

        # Валидация после инициализации
        self._validate_critical_settings()

    def _validate_critical_settings(self) -> None:
        """Проверяет критические настройки"""
        if not self.SECRET_KEY:
            logger.error("[ConfigApp] SECRET_KEY не задан в переменных окружения")
            raise ValueError("SECRET_KEY обязателен для продакшена")
        if not self.PASSWORD_PEPPER:
            logger.warning("[ConfigApp] PASSWORD_PEPPER не задан, используется пустое значение")
        if not self.POSTGRES_PASSWORD:
            logger.warning("[ConfigApp] POSTGRES_PASSWORD не задан")

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Формирует URL для асинхронного подключения к БД"""
        password = quote_plus(self.POSTGRES_PASSWORD) if self.POSTGRES_PASSWORD else ""
        if password:
            auth = f"{self.POSTGRES_USER}:{password}@"
        else:
            auth = f"{self.POSTGRES_USER}@"
        return f"postgresql+asyncpg://{auth}{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Формирует URL для синхронного подключения к БД"""
        password = quote_plus(self.POSTGRES_PASSWORD) if self.POSTGRES_PASSWORD else ""
        if password:
            auth = f"{self.POSTGRES_USER}:{password}@"
        else:
            auth = f"{self.POSTGRES_USER}@"
        return f"postgresql://{auth}{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        

settings = Settings()
