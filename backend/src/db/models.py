import enum
from typing import Optional
from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, Boolean, TIMESTAMP, Float, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.database import Base


class UserStatus(str, enum.Enum):
    """Статусы пользователя в системе"""
    REGISTERED = "registered"                       # Пользователь зарегистрирован, но не подтвердил почту
    ACTIVE = "active"                               # Пользователь зарегистрирован и подтвердил почту
    BANNED = "banned"                               # Пользователь заблокирован

class MedicalHistoryStatus(str, enum.Enum):
    """Статусы медицинской записи"""
    PLANNED = "planned"                             # Запланировано
    OVERDUE = "overdue"                             # Просрочено
    COMPLETED = "completed"                         # Завершено

class TypeAction(str, enum.Enum):
    """Типы медицинских действий"""
    INSPECTION = "inspection"                       # Осмотр
    TESTS = "tests"                                 # Анализы
    DIAGNOSTICS = "diagnostics"                     # Диагностика
    COMPLEX = "complex"                             # Комплекс мероприятий
    PARASITE_TREATMENT = "parasite_treatment"       # Обработка от паразитов
    SURGERY = "surgery"                             # Операция
    TREATMENT_COURSE = "treatment_course"           # Курс лечения
    DENTISTRY = "dentistry"                         # Стоматология
    GROOMING = "grooming"                           # Груминг
    OTHER = "other"                                 # Прочее


class Role(Base):
    """Таблица Роли"""
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    users = relationship("User", back_populates="role")

class User(Base):
    """Таблица Пользователи"""
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_login: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    user_password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_avatar: Mapped[str] = mapped_column(String(255), nullable=True, default="avatars/user-standart.png")
    
    registered_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id", ondelete="RESTRICT"), default=1)
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus), default=UserStatus.REGISTERED, nullable=False)

    banned_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    ban_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role = relationship("Role", back_populates="users")
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="user", cascade="all, delete-orphan")
    pets = relationship("Pet", back_populates="user", cascade="all, delete-orphan")

class UserToken(Base):
    """Таблица Токены пользователей"""
    
    __tablename__ = "user_tokens"

    token_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    token_type: Mapped[str] = mapped_column(String(32), nullable=False)

    requested_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="tokens")

class Action(Base):
    """Таблица Действия"""
    __tablename__ = "actions"

    action_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    user = relationship("User", back_populates="actions")

class MedicalAction(Base):
    """Таблица Медицинские действия"""
    __tablename__ = "medical_actions"

    medical_action_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medical_history_id: Mapped[int] = mapped_column(ForeignKey("medical_histories.medical_history_id", ondelete="CASCADE"), index=True)
    type_action: Mapped[TypeAction] = mapped_column(SQLEnum(TypeAction), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    interval_period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[MedicalHistoryStatus] = mapped_column(SQLEnum(MedicalHistoryStatus), default=MedicalHistoryStatus.PLANNED, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    medical_history = relationship("MedicalHistory", back_populates="actions")

class MedicalHistory(Base):
    """Таблица Медицинская история"""
    __tablename__ = "medical_histories"

    medical_history_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    actions = relationship("MedicalAction", back_populates="medical_history", cascade="all, delete-orphan")

    pet = relationship("Pet", back_populates="medical_history", uselist=False, primaryjoin="MedicalHistory.medical_history_id==Pet.medical_history_id")



class Pet(Base):
    """Таблица Питомцы"""
    __tablename__ = "pets"

    pet_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    breed: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_birth: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    chip: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    photo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default="pets/pet-standart.png")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    medical_history_id: Mapped[Optional[int]] = mapped_column(ForeignKey("medical_histories.medical_history_id", ondelete="SET NULL"), index=True)
    weight: Mapped[Optional[float]] = mapped_column(Float(precision=2), nullable=True, default=0.0)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="pets")
    medical_history = relationship("MedicalHistory", back_populates="pet", uselist=False, foreign_keys=[medical_history_id])

