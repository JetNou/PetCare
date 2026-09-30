from typing import List
from datetime import datetime, timedelta, timezone, date
import re
from fastapi import APIRouter, Depends, status, UploadFile, File, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.decorators import security_headers_check, active_user_required
from src.utils.email import EmailService
from src.core.config_app import settings
from src.db.database import get_db
from src.auth.auth import get_current_user
from src.core.exceptions import ValidationError, AuthorizationError, NotFoundError, InternalServerError, ConflictError
from src.core.config_log import logger
from src.pets.schemas import PetCreate, PetUpdate, PetResponse, NAME_REGEX
from src.pets.services import PetService
from src.pets.utils import PetPhotoService
from src.db.models import User, Pet
from src.utils.token import TokenManager


router = APIRouter()

@router.post("/", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
@security_headers_check
@active_user_required
async def create_pet(
    pet_data: PetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать нового питомца"""
    try:
        pet = await PetService.create_pet(db, current_user.user_id, pet_data)
        return pet
    except ValueError as e:
        logger.error(f"Ошибка при создании питомца: {e}")
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при создании питомца: {e}")
        raise InternalServerError("Ошибка при создании питомца")

@router.get("/", response_model=List[PetResponse])
@security_headers_check
@active_user_required
async def get_my_pets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить своих питомцев"""
    try:
        pets = await PetService.get_all_pets(db, current_user.user_id)
        return pets
    except Exception as e:
        logger.error(f"Ошибка при получении списка питомцев: {e}")
        raise InternalServerError("Ошибка при получении списка питомцев")

@router.get("/{pet_id}", response_model=PetResponse)
@security_headers_check
@active_user_required
async def get_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить информацию о конкретном питомце
    - Admin: может получить данные любого питомца
    - Владелец: может получить данные только своего питомца
    """
    try:
        pet = await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        return pet
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} не найден для пользователя {current_user.user_id}")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении питомца {pet_id}: {e}")
        raise InternalServerError("Ошибка при получении питомца")

@router.patch("/{pet_id}/photo", response_model=PetResponse)
@security_headers_check
@active_user_required
async def update_pet_photo(
    pet_id: int,
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить фото питомца"""
    try:
        if not PetPhotoService.validate_file_extension(photo.filename):
            raise ValidationError(
                f"Не поддерживаемый тип файла. Разрешены: {', '.join(PetPhotoService.get_allowed_extensions())}",
                field="photo"
            )
        
        photo_content = await photo.read()
        
        if not PetPhotoService.validate_file_size(len(photo_content)):
            raise ValidationError("Размер файла не должен превышать 5MB", field="photo")
        
        pet = await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        
        if pet.photo and pet.photo != "pets/pet-standart.png":
            await PetPhotoService.delete_pet_photo(pet.photo)
        
        photo_filename = PetPhotoService.generate_pet_photo_filename(current_user.user_id, pet_id, photo.filename)
        await PetPhotoService.save_pet_photo(photo_content, photo_filename)
        
        pet.photo = photo_filename
        await db.commit()
        await db.refresh(pet)
        
        logger.info(f"Фото питомца {pet_id} обновлено на {photo_filename} пользователем {current_user.user_id}")
        return pet
    
    except (ValidationError, AuthorizationError) as e:
        raise
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} не найден для пользователя {current_user.user_id}")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except Exception as e:
        error_msg = str(e)
        if error_msg == "pet_deleted":
            logger.warning(f"Питомец {pet_id} был удален. Попытка обновления пользователем {current_user.user_id}")
            raise ConflictError("Питомец был удален и больше не доступен")
        else:
            logger.error(f"Ошибка при обновлении фото питомца {pet_id}: {error_msg[:200]}")
            raise InternalServerError("Ошибка при обновлении фото")

@router.patch("/{pet_id}", response_model=PetResponse)
@security_headers_check
@active_user_required
async def update_pet(
    pet_id: int,
    pet_update: PetUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить данные питомца (кличка, пол, порода, окрас, вес, дата рождения, чип).
    Все поля опциональны, обновляются только переданные значения
    """
    try:
        update_data = {}
        
        if pet_update.name is not None:
            if not pet_update.name.strip():
                raise ValidationError("Кличка не может быть пустой", field="name")
            if not re.match(NAME_REGEX, pet_update.name.strip()):
                raise ValidationError("Кличка может содержать только английские и русские буквы, пробелы и дефис", field="name")
            update_data['name'] = pet_update.name.strip()
        
        if pet_update.gender is not None:
            if not pet_update.gender.strip():
                raise ValidationError("Пол не может быть пустой", field="gender")
            if not re.match(NAME_REGEX, pet_update.gender.strip()):
                raise ValidationError("Пол может содержать только английские и русские буквы, пробелы и дефис", field="gender")
            update_data['gender'] = pet_update.gender.strip()
        
        if pet_update.breed is not None:
            if not pet_update.breed.strip():
                raise ValidationError("Порода не может быть пустой", field="breed")
            if not re.match(NAME_REGEX, pet_update.breed.strip()):
                raise ValidationError("Порода может содержать только английские и русские буквы, пробелы и дефис", field="breed")
            update_data['breed'] = pet_update.breed.strip()
        
        if pet_update.color is not None:
            if not pet_update.color.strip():
                raise ValidationError("Окрас не может быть пустым", field="color")
            if not re.match(NAME_REGEX, pet_update.color.strip()):
                raise ValidationError("Окрас может содержать только английские и русские буквы, пробелы и дефис", field="color")
            update_data['color'] = pet_update.color.strip()
        
        if pet_update.weight is not None:
            if pet_update.weight <= 0:
                raise ValidationError("Вес должен быть положительным числом", field="weight")
            update_data['weight'] = round(pet_update.weight, 2)
        
        if pet_update.date_birth is not None:
            if pet_update.date_birth > date.today():
                raise ValidationError("Дата рождения не может быть в будущем", field="date_birth")
            update_data['date_birth'] = pet_update.date_birth
        
        if pet_update.chip is not None:
            if pet_update.chip.strip():
                if not re.match(r'^[0-9a-zA-Z]+$', pet_update.chip.strip()):
                    raise ValidationError("Номер чипа может содержать только цифры и английские буквы", field="chip")
                update_data['chip'] = pet_update.chip.strip()
        
        pet = await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        
        if not update_data:
            return pet
        
        pet_update = PetUpdate(**update_data)
        updated_pet = await PetService.update_pet(db, pet_id, current_user.user_id, pet_update, pet, is_admin=(current_user.role_id == 1))
        return updated_pet
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Ошибка валидации при обновлении питомца {pet_id}: {error_msg[:200]}")
        raise ValidationError(error_msg[:200])
    except (ValidationError, AuthorizationError) as e:
        raise
    except Exception as e:
        error_msg = str(e)
        if error_msg == "pet_deleted":
            logger.warning(f"Питомец {pet_id} был удален. Попытка обновления пользователем {current_user.user_id}")
            raise ConflictError("Питомец был удален и больше не доступен")
        else:
            logger.warning(f"Питомец {pet_id} не найден для пользователя {current_user.user_id}")
            raise NotFoundError("Питомец")
    except NotFoundError:
        raise

@router.delete("/{pet_id}/photo", response_model=PetResponse)
@security_headers_check
@active_user_required
async def reset_pet_photo(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сбросить фото питомца до стандартного"""
    try:
        pet = await PetService.reset_pet_photo(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        logger.info(f"Фото питомца {pet_id} сброшено до стандартного")
        return pet
    
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} был удален. Попытка изменения пользователем {current_user.user_id}")
        raise ConflictError("Питомец был удален и больше не доступен")
    except Exception as e:
        logger.error(f"Ошибка при сбросе фото питомца {pet_id}: {e}")
        raise InternalServerError("Ошибка при сбросе фото")

@router.delete("/{pet_id}", response_model=dict)
@security_headers_check
@active_user_required
async def delete_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить питомца (мягкое удаление)"""
    try:
        pet = await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        
        if pet.is_deleted:
            logger.warning(f"Питомец {pet_id} был удален. Попытка повторного удаления пользователем {current_user.user_id}")
            raise ConflictError("Питомец уже был удален ранее")
        
        await PetService.delete_pet(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        
        if current_user.user_email:
            ttl = settings.TOKEN_TTL_SECONDS
            raw_token = await TokenManager.create_user_token(db, current_user.user_id, f"pet_restore_{pet_id}", ttl)
            expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).strftime("%Y-%m-%d %H:%M UTC")
            
            await EmailService.send_pet_restore_email(
                current_user.user_email, 
                current_user.user_full_name, 
                pet.name,
                raw_token, 
                expires
            )
        
        logger.info(f"Питомец {pet_id} удален пользователем {current_user.user_id}")
        from src.users.services import ActionService
        await ActionService.log_action(db, current_user.user_id, f"Удален питомец {pet_id}")
        return {
            "message": "Питомец успешно удален. Инструкция по восстановлению отправлена на email."
        }
        
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} был удален. Попытка доступа пользователем {current_user.user_id}")
        raise ConflictError("Питомец был удален и больше не доступен")
    except Exception as e:
        logger.error(f"Ошибка при удалении питомца {pet_id}: {e}")
        raise InternalServerError("Ошибка при удалении питомца")

@router.post("/restore", response_model=dict, status_code=200)
@security_headers_check
@active_user_required
async def restore_pet_by_token(
    token: str = Query(..., description="Токен восстановления питомца"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Восстановление питомца по токену"""
    
    token_hash = TokenManager.hash_token(token)
    db_token = await TokenManager.get_token_by_hash(db, token_hash, None)
    
    if not db_token or db_token.consumed_at or db_token.expires_at < datetime.now(timezone.utc):
        raise ValidationError("Неверный, использованный или просроченный токен")
    
    if not db_token.token_type.startswith("pet_restore_"):
        raise ValidationError("Неверный тип токена")
    
    try:
        pet_id = int(db_token.token_type.split("_")[2])
    except (IndexError, ValueError):
        raise ValidationError("Неверный формат токена")
    
    try:
        from sqlalchemy import select, and_
        
        query = select(Pet).where(Pet.pet_id == pet_id, Pet.is_deleted == True)
        
        if current_user.role_id != 1:
            query = query.where(Pet.user_id == current_user.user_id)
        
        result = await db.execute(query)
        pet = result.scalar_one_or_none()
        
        if not pet:
            if current_user.role_id != 1 and db_token.user_id != current_user.user_id:
                logger.warning(f"Пользователь {current_user.user_id} попытался восстановить питомца {pet_id} по токену, принадлежащему другому пользователю")
                raise AuthorizationError("Вы не имеете прав на восстановление этого питомца")
            else:
                raise NotFoundError("Удаленный питомец")
        
        if current_user.role_id != 1 and pet.user_id != current_user.user_id:
            logger.warning(f"Пользователь {current_user.user_id} попытался восстановить питомца {pet_id}, принадлежащего другому пользователю")
            raise AuthorizationError("Вы не имеете прав на восстановление этого питомца")
        
        if current_user.role_id == 1 and db_token.user_id != current_user.user_id:
            logger.info(f"Администратор {current_user.user_id} восстанавливает питомца {pet_id} по токену, принадлежащему пользователю {db_token.user_id}")
        else:
            logger.info(f"Пользователь {current_user.user_id} восстанавливает питомца {pet_id} по токену")
        
        pet.is_deleted = False
        db_token.consumed_at = datetime.now(timezone.utc)
        await db.commit()
        
        logger.info(f"Питомец {pet_id} восстановлен по токену пользователем {db_token.user_id}")
        from src.users.services import ActionService
        await ActionService.log_action(db, db_token.user_id, f"Восстановлен питомец {pet_id}")
        return {"detail": "Питомец успешно восстановлен"}
    
    except (NotFoundError, AuthorizationError):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка восстановления питомца по токену: {e}")
        raise InternalServerError("Ошибка восстановления питомца")

