import re
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from src.db.models import UserStatus


LOGIN_REGEX = r'^[a-zA-Z0-9_]+$'
NAME_REGEX = r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$'
PASS_REGEX = r'^(?=.*[a-zа-яё])(?=.*[A-ZА-ЯЁ])(?=.*\d)(?=.*[!@#$%^_&*])[A-Za-zА-Яа-яёЁ\d!@#$%^_&*]{8,}$'

class UserBase(BaseModel):
    """Общие методы валидации для всех схем пользователя"""
    
    @classmethod
    def _validate_regex(cls, value: Optional[str], pattern: str, error_msg: str) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if value and not re.match(pattern, value):
            raise ValueError(error_msg)
        return value

class UserProfile(BaseModel):
    """Схема профиля (Response)"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    user_id: int
    user_login: str
    user_full_name: str
    user_email: EmailStr
    user_avatar: str = Field(default="avatars/user-standart.png")
    role_id: int
    registered_at: datetime
    is_deleted: bool
    status: UserStatus
    ban_reason: Optional[str] = None
    banned_at: Optional[datetime] = None

    @field_validator("user_avatar", mode="before")
    @classmethod
    def format_avatar_path(cls, v: Optional[str]) -> str:
        if not v:
            return "avatars/user-standart.png"
        return v if v.startswith("avatars/") else f"avatars/{v}"

class UserUpdate(UserBase):
    """Схема обновления профиля"""
    user_login: Optional[str] = Field(None, min_length=3, max_length=50)
    user_full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    user_email: Optional[EmailStr] = None

    @field_validator("user_login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        return cls._validate_regex(v, LOGIN_REGEX, "Логин может содержать только английские буквы, цифры и подчеркивание")

    @field_validator("user_full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        return cls._validate_regex(v, NAME_REGEX, "Имя может содержать только буквы, пробелы и дефис")

class UserRestoreRequest(UserBase):
    """Схема восстановления аккаунта"""
    full_name: str
    login: str
    password: str

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        return cls._validate_regex(v, LOGIN_REGEX, "Некорректный формат логина")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        return cls._validate_regex(v, NAME_REGEX, "Некорректный формат имени")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return cls._validate_regex(v, PASS_REGEX, "Пароль не соответствует требованиям безопасности")

class UserSearchFilters(BaseModel):
    """Фильтры для поиска пользователей (Admin)"""
    user_login: Optional[str] = None
    user_full_name: Optional[str] = None
    user_email: Optional[str] = None
    role_id: Optional[int] = None
    limit: int = Field(default=10, ge=1, le=100)

class ResetPasswordConfirm(UserBase):
    """Подтверждение сброса пароля"""
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return cls._validate_regex(v, PASS_REGEX, "Пароль слишком слабый")

class SystemStatistics(BaseModel):
    """Статистика системы для администратора"""
    total_users: int
    active_users: int
    total_pets: int
    active_pets: int
    medical_events_by_status: Dict[str, int] = Field(default_factory=dict)