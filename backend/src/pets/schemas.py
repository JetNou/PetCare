from datetime import datetime, date
import re
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationInfo

from src.db.models import TypeAction, MedicalHistoryStatus


NAME_REGEX = r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$'

class PetBase(BaseModel):
    """Базовая логика для питомца"""
    name: str = Field(..., min_length=1, max_length=100)
    gender: Optional[str] = Field(default=None, max_length=20)
    date_birth: Optional[date] = Field(default=None)
    weight: float = Field(..., gt=0, lt=1000001)
    breed: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=50)
    chip: Optional[str] = Field(default=None, max_length=25)

    @field_validator("name", "gender", "color", "breed")
    @classmethod
    def validate_strings(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            if info.field_name == "name":
                raise ValueError(f"Поле {info.field_name} не может быть пустым")
            return None
        
        if not re.match(NAME_REGEX, v):
            raise ValueError(f"Поле {info.field_name} содержит недопустимые символы")
        return v

    @field_validator("chip")
    @classmethod
    def validate_chip(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not re.match(r'^[0-9a-zA-Z]+$', v):
            raise ValueError("Номер чипа может содержать только цифры и английские буквы")
        return v

class PetCreate(PetBase):
    """Схема для создания питомца"""
    pass

class PetUpdate(BaseModel):
    """Схема для обновления данных питомца"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=20)
    date_birth: Optional[date] = Field(None)
    chip: Optional[str] = Field(None, max_length=100)
    weight: Optional[float] = Field(None, gt=0, lt=1000001)

    @field_validator("name", "breed", "color", "gender")
    @classmethod
    def validate_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Поле не может быть пустым")
        if not re.match(NAME_REGEX, v):
            raise ValueError("Поле содержит недопустимые символы")
        return v

    @field_validator("chip")
    @classmethod
    def validate_chip(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not re.match(r'^[0-9a-zA-Z]+$', v):
            raise ValueError("Номер чипа может содержать только цифры и английские буквы")
        return v

class PetResponse(BaseModel):
    """Схема ответа для питомца"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    pet_id: int
    name: str
    breed: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    date_birth: Optional[date] = None
    chip: Optional[str] = None
    photo: str = Field(default="pets/pet-standart.png")
    weight: float = Field(default=0.0)
    user_id: int

    @field_validator("photo", mode="before")
    @classmethod
    def format_photo_path(cls, v: Optional[str]) -> str:
        if not v:
            return "pets/pet-standart.png"
        if not v.startswith("pets/"):
            return f"pets/{v}"
        return v

    @field_validator("weight")
    @classmethod
    def round_weight(cls, v: float) -> float:
        return round(v, 2)

class MedicalEventCreate(BaseModel):
    """Схема для создания медицинского события"""
    type_action: TypeAction
    description: Optional[str] = Field(None, max_length=500)
    date: datetime
    notes: Optional[str] = Field(None, max_length=1000)
    status: MedicalHistoryStatus = Field(default=MedicalHistoryStatus.PLANNED)
    interval_period: Optional[int] = Field(default=0, ge=0, lt=36501)

class MedicalEventUpdate(BaseModel):
    """Схема для обновления медицинского события"""
    type_action: Optional[TypeAction] = None
    description: Optional[str] = Field(None, max_length=500)
    date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[MedicalHistoryStatus] = None
    interval_period: Optional[int] = Field(None, ge=0, lt=36501)

class MedicalEventResponse(BaseModel):
    """Схема ответа для медицинского события"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    medical_history_id: int
    medical_action_id: int = Field(alias="medical_action_id")
    pet_id: int
    type_action: TypeAction
    description: Optional[str] = None
    date: datetime
    status: MedicalHistoryStatus
    notes: Optional[str] = None
    interval_period: int = 0

class MedicalHistoryResponse(BaseModel):
    """Схема ответа для медицинской истории"""
    model_config = ConfigDict(from_attributes=True)

    pet_id: int
    pet_name: str
    events: List[MedicalEventResponse] = []
    total_events: int = 0