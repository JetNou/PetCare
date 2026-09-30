from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config_log import logger
from src.db.models import Pet, MedicalHistory, MedicalAction, TypeAction, MedicalHistoryStatus
from src.users.services import ActionService
from src.pets.schemas import PetCreate, PetUpdate, MedicalEventCreate, MedicalEventUpdate


class PetService:
    """Сервис для управления питомцами"""

    @staticmethod
    async def create_pet(db: AsyncSession, user_id: int, pet_data: PetCreate) -> Pet:
        """Создать новый питомец"""
        new_pet = Pet(
            user_id=user_id,
            name=pet_data.name,
            breed=pet_data.breed,
            color=pet_data.color,
            gender=pet_data.gender,
            date_birth=pet_data.date_birth,
            chip=pet_data.chip,
            weight=pet_data.weight,
            photo="pets/pet-standart.png"
        )
        db.add(new_pet)
        await db.commit()
        await db.refresh(new_pet)
        logger.info(f"[PetService] Питомец {new_pet.pet_id} создан для пользователя {user_id}")
        await ActionService.log_action(db, user_id, f"Создан питомец {new_pet.pet_id}", notes=f"Имя: {new_pet.name}")
        return new_pet

    @staticmethod
    async def get_pet_by_id(db: AsyncSession, pet_id: int, user_id: int, is_admin: bool = False) -> Pet:
        """Получить питомца по ID (admin - любой, user - только своих)"""
        logger.debug(f"[get_pet_by_id] pet_id={pet_id}, user_id={user_id}, is_admin={is_admin}")
        query = select(Pet).where(Pet.pet_id == pet_id, Pet.is_deleted == False)
        
        if not is_admin:
            query = query.where(Pet.user_id == user_id)
        
        query = query.options(selectinload(Pet.medical_history))
        result = await db.execute(query)
        pet = result.scalar_one_or_none()

        if not pet:
            raise ValueError("Питомец не найден или доступ запрещен")
        return pet
    
    @staticmethod
    async def get_all_pets(db: AsyncSession, user_id: Optional[int] = None, is_admin: bool = False) -> List[Pet]:
        """Получить питомцев (admin - всех, user - только своих)"""
        query = select(Pet).where(Pet.is_deleted == False)
        
        if not is_admin and user_id:
            query = query.where(Pet.user_id == user_id)
        
        query = query.options(selectinload(Pet.medical_history))
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_pet(db: AsyncSession, pet_id: int, user_id: int, pet_data: PetUpdate, pet: Optional[Pet] = None, is_admin: bool = False) -> Pet:
        """Обновить данные питомца (admin - любой, user - только своих)"""
        if pet is None:
            pet = await PetService.get_pet_by_id(db, pet_id, user_id, is_admin=is_admin)
        
        update_data = pet_data.model_dump(exclude_unset=True, exclude_none=True)
        
        for field, value in update_data.items():
            setattr(pet, field, value)
        
        await db.commit()
        await db.refresh(pet)
        logger.info(f"[PetService] Питомец {pet_id} обновлен")
        await ActionService.log_action(db, user_id, f"Обновлен питомец {pet_id}", notes=str(update_data))
        return pet

    @staticmethod
    async def update_pet_photo(db: AsyncSession, pet_id: int, user_id: int, photo_filename: str, is_admin: bool = False) -> Pet:
        """Обновить фото питомца (admin - любой, user - только своих)"""
        pet = await PetService.get_pet_by_id(db, pet_id, user_id, is_admin=is_admin)
        pet.photo = photo_filename
        await db.commit()
        await db.refresh(pet)
        logger.info(f"[PetService] Фото питомца {pet_id} обновлено: {photo_filename}")
        return pet

    @staticmethod
    async def reset_pet_photo(db: AsyncSession, pet_id: int, user_id: int, is_admin: bool = False) -> Pet:
        """Сбросить фото питомца до стандартного (pets/pet-standart.png) (admin - любой, user - только своих)"""
        pet = await PetService.get_pet_by_id(db, pet_id, user_id, is_admin=is_admin)
        pet.photo = "pets/pet-standart.png"
        await db.commit()
        await db.refresh(pet)
        logger.info(f"[PetService] Фото питомца {pet_id} сброшено до стандартного")
        await ActionService.log_action(db, user_id, f"Сброшено фото питомца {pet_id} до стандартного")
        return pet

    @staticmethod
    async def delete_pet(db: AsyncSession, pet_id: int, user_id: int, is_admin: bool = False) -> None:
        """Мягко удалить питомца (установить is_deleted = True)"""
        pet = await PetService.get_pet_by_id(db, pet_id, user_id, is_admin=is_admin)
        pet.is_deleted = True
        await db.commit()
        logger.info(f"[PetService] Питомец {pet_id} отмечен как удаленный")
        await ActionService.log_action(db, user_id, f"Удален питомец {pet_id}")

    @staticmethod
    async def restore_pet(db: AsyncSession, pet_id: int, user_id: int, is_admin: bool = False) -> Pet:
        """Восстановить удаленного питомца"""
        query = select(Pet).where(Pet.pet_id == pet_id, Pet.is_deleted == True)
        
        if not is_admin and user_id:
            query = query.where(Pet.user_id == user_id)
        
        pet = await db.execute(query).scalar_one_or_none()
    
        if not pet:
            raise ValueError("Удаленный питомец не найден")
        
        pet.is_deleted = False
        await db.commit()
        await db.refresh(pet)
        logger.info(f"[PetService] Питомец {pet_id} восстановлен")
        await ActionService.log_action(db, user_id, f"Восстановлен питомец {pet_id}")
        return pet


class MedicalEventService:
    """Сервис для управления медицинскими событиями"""

    @staticmethod
    async def _ensure_medical_action(db: AsyncSession, type_action: TypeAction, interval_period: Optional[int]) -> MedicalAction:
        """Получить или создать шаблон medical_action"""
        result = await db.execute(
            select(MedicalAction).where(
                MedicalAction.type_action == type_action,
                MedicalAction.interval_period == interval_period
            )
        )
        medical_action = result.scalar_one_or_none()

        if not medical_action:
            medical_action = MedicalAction(
                type_action=type_action,
                interval_period=interval_period
            )
            db.add(medical_action)
            await db.commit()
            await db.refresh(medical_action)

        return medical_action

    @staticmethod
    async def _ensure_pet_medical_history(db: AsyncSession, pet: Pet) -> MedicalHistory:
        """Гарантированно получить мед. историю питомца (1 на питомца)"""
        if pet.medical_history_id:
            history = await db.get(MedicalHistory, pet.medical_history_id)
            if history:
                return history

        history = MedicalHistory()
        db.add(history)
        await db.commit()
        await db.refresh(history)

        pet.medical_history_id = history.medical_history_id
        await db.commit()
        return history

    @staticmethod
    async def create_medical_event(
        db: AsyncSession,
        user_id: int,
        event_data: MedicalEventCreate,
        pet_id: int
    ) -> MedicalAction:
        """Создать медицинское событие в истории питомца"""
        pet = await PetService.get_pet_by_id(db, pet_id, user_id, is_admin=True)
        history = await MedicalEventService._ensure_pet_medical_history(db, pet)

        if event_data.status:
            status = event_data.status
        else:
            status = MedicalHistoryStatus.PLANNED
            if event_data.date <= datetime.now(timezone.utc):
                status = MedicalHistoryStatus.COMPLETED

        medical_action = MedicalAction(
            medical_history_id=history.medical_history_id,
            type_action=event_data.type_action,
            description=event_data.description,
            interval_period=event_data.interval_period,
            date=event_data.date,
            status=status,
            notes=event_data.notes
        )

        db.add(medical_action)
        await db.commit()
        await db.refresh(medical_action, ['medical_history'])

        medical_action.pet_id = pet_id

        logger.info(f"[MedicalEventService] Медицинское событие {medical_action.medical_action_id} создано для питомца {pet_id}")
        return medical_action

    @staticmethod
    async def get_medical_event(db: AsyncSession, event_id: int, user_id: int, is_admin: bool = False) -> MedicalAction:
        """Получить медицинское событие по ID"""
        result = await db.execute(
            select(MedicalAction)
            .join(MedicalHistory)
            .join(Pet)
            .where(
                MedicalAction.medical_action_id == event_id,
                MedicalAction.is_deleted == False,
                Pet.user_id == user_id,
                Pet.is_deleted == False
            )
            .options(
                selectinload(MedicalAction.medical_history).selectinload(MedicalHistory.pet)
            )
        )
        
        if is_admin:
            result = await db.execute(
                select(MedicalAction)
                .join(MedicalHistory)
                .join(Pet)
                .where(
                    MedicalAction.medical_action_id == event_id,
                    MedicalAction.is_deleted == False,
                    Pet.is_deleted == False
                )
                .options(
                    selectinload(MedicalAction.medical_history).selectinload(MedicalHistory.pet)
                )
            )
        
        event = result.scalar_one_or_none()

        if not event:
            raise ValueError("Медицинское событие не найдено")

        if not event.medical_history or not event.medical_history.pet:
            raise ValueError("Доступ запрещен")

        event.pet_id = event.medical_history.pet.pet_id

        return event

    @staticmethod
    async def update_medical_event(
        db: AsyncSession,
        event_id: int,
        user_id: int,
        event_data: MedicalEventUpdate,
        is_admin: bool = False
    ) -> MedicalAction:
        """Обновить медицинское событие"""
        event = await MedicalEventService.get_medical_event(db, event_id, user_id, is_admin=is_admin)
        
        update_data = event_data.model_dump(exclude_unset=True, exclude_none=True)

        for field, value in update_data.items():
            if field == "interval_period" and value is not None:
                value = int(value)
            setattr(event, field, value)

        await db.commit()
        await db.refresh(event)

        logger.info(f"[MedicalEventService] Медицинское событие {event_id} обновлено")
        return event

    @staticmethod
    async def get_pet_medical_history(
        db: AsyncSession,
        pet_id: int,
        user_id: int,
        status: Optional[MedicalHistoryStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[MedicalAction], int]:
        """Получить медицинскую историю питомца"""
        pet = await PetService.get_pet_by_id(db, pet_id, user_id, is_admin=True)

        if not pet.medical_history_id:
            return [], 0

        query = select(MedicalAction).where(
            MedicalAction.medical_history_id == pet.medical_history_id,
            MedicalAction.is_deleted == False
        )

        if status:
            query = query.where(MedicalAction.status == status)

        count_result = await db.execute(
            select(MedicalAction).where(
                MedicalAction.medical_history_id == pet.medical_history_id,
                MedicalAction.is_deleted == False
            )
        )
        total = len(count_result.scalars().all())

        result = await db.execute(
            query
            .order_by(MedicalAction.date.desc())
            .limit(limit)
            .offset(offset)
        )

        events = result.scalars().all()
        for event in events:
            event.pet_id = pet_id
        return events, total

    @staticmethod
    async def mark_event_completed(db: AsyncSession, event_id: int, user_id: int, is_admin: bool = False) -> MedicalAction:
        """Отметить медицинское событие как выполненное"""
        event = await MedicalEventService.get_medical_event(db, event_id, user_id, is_admin=is_admin)
        event.status = MedicalHistoryStatus.COMPLETED
        await db.commit()
        await db.refresh(event)

        logger.info(f"[MedicalEventService] Медицинское событие {event_id} отмечено как выполненное")
        return event

    @staticmethod
    async def mark_event_overdue(db: AsyncSession, event_id: int, user_id: int, is_admin: bool = False) -> MedicalAction:
        """Отметить медицинское событие как просроченное"""
        event = await MedicalEventService.get_medical_event(db, event_id, user_id, is_admin=is_admin)
        event.status = MedicalHistoryStatus.OVERDUE
        await db.commit()
        await db.refresh(event)

        logger.info(f"[MedicalEventService] Медицинское событие {event_id} отмечено как просроченное")
        return event

    @staticmethod
    async def delete_medical_event(db: AsyncSession, event_id: int, user_id: int, is_admin: bool = False) -> None:
        """Мягко удалить медицинское событие (установить is_deleted = True)"""
        event = await MedicalEventService.get_medical_event(db, event_id, user_id, is_admin=is_admin)
        event.is_deleted = True
        await db.commit()
        logger.info(f"[MedicalEventService] Медицинское событие {event_id} помечено как удаленное")

