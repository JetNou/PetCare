import re
from pydantic import BaseModel, EmailStr, Field, field_validator


LOGIN_REGEX = r'^[a-zA-Z0-9_]+$'
NAME_REGEX = r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$'
PASS_REGEX = r'^(?=.*[a-zа-яё])(?=.*[A-ZА-ЯЁ])(?=.*\d)(?=.*[!@#$%^_&*])[A-Za-zА-Яа-яёЁ\d!@#$%^_&*]{8,}$'

class UserCreate(BaseModel):
    """Модель для регистрации нового пользователя"""
    user_login: str = Field(min_length=3, max_length=50, strip_whitespace=True)
    user_full_name: str = Field(min_length=2, max_length=100, strip_whitespace=True)
    user_email: EmailStr = Field(max_length=100)
    user_password: str = Field(min_length=8, max_length=128)

    @field_validator("user_login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        if not re.match(LOGIN_REGEX, v):
            raise ValueError("Логин может содержать только английские буквы, цифры и подчеркивание")
        return v

    @field_validator("user_full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not re.match(NAME_REGEX, v):
            raise ValueError("Имя может содержать только русские или английские буквы, пробелы и дефис")
        return v

    @field_validator("user_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(PASS_REGEX, v):
            raise ValueError(
                "Пароль должен содержать минимум 8 символов, включая заглавную букву, "
                "строчную букву, цифру и спецсимвол (!@#$%^&*)"
            )
        return v

class UserLogin(BaseModel):
    """Модель для входа. Увеличена длина для поддержки длинных email"""
    user_identifier: str = Field(min_length=3, max_length=255, strip_whitespace=True)
    password: str = Field(min_length=8)

class TokenResponse(BaseModel):
    """Ответ с refresh token"""
    detail: str = Field(description="Сообщение для пользователя")
    refresh_token: str = Field(description="Refresh token для обновления access token")

class RefreshTokenRequest(BaseModel):
    """Запрос на обновление access token"""
    refresh_token: str = Field(description="Refresh token для получения нового access token")

class ResendVerificationRequest(BaseModel):
    """Запрос на переотправку письма подтверждения по email"""
    user_email: EmailStr = Field(max_length=100, description="Email пользователя для отправки письма подтверждения")