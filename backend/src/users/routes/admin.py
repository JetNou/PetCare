import re
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.pets.services import PetService
from src.core.exceptions import AuthorizationError, ConflictError, InternalServerError, NotFoundError, ValidationError
from src.users.schemas import UserProfile, UserUpdate, SystemStatistics
from src.users.services import UserService, ActionService
from src.db.models import User, Pet, Action
from src.db.database import get_db
from src.utils.decorators import active_user_required, admin_required, cache, security_headers_check
from src.auth import get_current_user
from src.core.config_log import logger
from src.pets.schemas import PetResponse, PetUpdate


router = APIRouter()

@router.post("/set-role/{user_id}/{role_id}", response_model=dict,  status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def set_role(
    request: Request,
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Устанавливает произвольную роль пользователю
    1 - Администратор
    3 - Пользователь
    """
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise NotFoundError("Пользователь")

        if target_user.user_id == current_user.user_id:
            raise ValidationError("Нельзя изменять собственные права")
        if target_user.user_id == 1:
            raise AuthorizationError("С пользователем с id=1 нельзя выполнять это действие")

        if role_id not in (1, 3):
            raise ValidationError("Неверная роль")

        await db.execute(update(User).where(User.user_id == target_user.user_id).values(role_id=role_id))
        await db.commit()

        if role_id == 1:
            role_name = 'администратор'
        elif role_id == 3:
            role_name = 'пользователь'
        else:
            role_name = 'ошибка'
                
        logger.info(f"[ADMIN] Роль пользователя (id = {target_user.user_id}) установлена: {role_name} ({role_id})")
        await ActionService.log_action(db, current_user.user_id, f"Роль пользователя {target_user.user_id} установлена на {role_name} ({role_id})", notes=f"Дата: {(datetime.now(timezone.utc) + timedelta(hours=3)).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")}")
        await db.commit()
        
        from src.utils.email import EmailService
        content_html = f"<p style='margin:0 0 16px;'>Ваша роль была изменена на: <strong>{role_name}</strong></p>" \
                      "<p style='margin:0 0 16px;'>Если вы не авторизировали это действие, обратитесь в службу поддержки.</p>"
        
        body = EmailService._render_email_html(
            title="Роль изменена",
            user_full_name=target_user.user_full_name,
            content_html=content_html
        )
        await EmailService.send_email(target_user.user_email, "Ваша роль изменена", body)
        
        return {"detail": f"Роль пользователя (id = {target_user.user_id}) установлена: {role_name} ({role_id}) и пользователь уведомлен"}
    
    except (ValidationError, NotFoundError, ConflictError, AuthorizationError) as e:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Неожиданная ошибка при установке роли: {e}")
        raise InternalServerError("Внутренняя ошибка сервера")

@router.post("/user/{user_id}/restore", response_model=dict,  status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def restore_user_admin(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Восстанавливает удаленного пользователя"""
    try:
        result = await db.execute(select(User).where(User.user_id == user_id, User.is_deleted == True))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise ValueError("Пользователь не найден или не удалён")
        
        await UserService.restore_user(db, user_id, current_user.user_id, is_admin=True)
        logger.info(f"[ADMIN] Пользователь {current_user.user_id} восстановил пользователя {user_id}")
        
        from src.utils.email import EmailService
        body = EmailService._render_email_html(
            title="Аккаунт восстановлен",
            user_full_name=target_user.user_full_name,
            content_html="<p style='margin:0 0 16px;'>Ваш аккаунт был восстановлен администратором.</p>"
                        "<p style='margin:0 0 16px;'>Если это произошло без вашего ведома, обратитесь в службу поддержки.</p>"
        )
        await EmailService.send_email(target_user.user_email, "Аккаунт восстановлен", body)
        
        return {"detail": "Пользователь восстановлен и уведомлен"}
    
    except ValueError as e:
        raise HTTPException(status_code=200, detail=str(e))
    except Exception as e:
        logger.error(f"[ADMIN] Неожиданная ошибка при восстановлении: {e}")
        raise InternalServerError()

@router.delete("/user/{user_id}/delete", response_model=dict,  status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def delete_user_admin(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Помечает пользователя как удалённого"""
    try:
        result = await db.execute(select(User).where(User.user_id == user_id, User.is_deleted == False))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise ValueError("Пользователь не найден или уже удалён")

        await UserService.delete_user(db, user_id, current_user.user_id, is_admin=True)
        logger.info(f"[ADMIN] Пользователь {current_user.user_id} удалил пользователя {user_id}")
        
        from src.utils.email import EmailService
        await EmailService.send_delete_email(target_user.user_email, target_user.user_full_name)
        
        return {"detail": "Пользователь удалён и уведомлен"}
    
    except ValueError as e:
        raise HTTPException(status_code=200, detail=str(e))
    except Exception as e:
        logger.error(f"[ADMIN] Неожиданная ошибка при удалении: {e}")
        raise InternalServerError()

@router.post("/user/{user_id}/ban", response_model=dict,  status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def ban_user(
        request: Request,
        user_id: int,
        reason: str = None,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Заблокировать пользователя и отправить уведомление"""
    try:
        result = await db.execute(select(User).where(User.user_id == user_id, User.is_deleted == False))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise NotFoundError("Пользователь")
        
        await UserService.ban_user(db, user_id, current_user.user_id, reason, is_admin=True)
        logger.info(f"[ADMIN] Пользователь {current_user.user_id} заблокировал пользователя {user_id}")
        
        from src.utils.email import EmailService
        reason_text = f"Причина: {reason}" if reason else "Причина не указана"
        content_html = f"<p style='margin:0 0 16px;'>Ваш аккаунт был заблокирован администратором.</p>" \
                      f"<p style='margin:0 0 16px;'>{reason_text}</p>" \
                      f"<p style='margin:0 0 16px;'>Если вы считаете, что это ошибка, обратитесь в службу поддержки.</p>"
        
        body = EmailService._render_email_html(
            title="Аккаунт заблокирован",
            user_full_name=target_user.user_full_name,
            content_html=content_html
        )
        await EmailService.send_email(target_user.user_email, "Аккаунт заблокирован", body)
        
        return {"detail": "Пользователь заблокирован и уведомлен"}
    
    except NotFoundError as e:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[ADMIN] Неожиданная ошибка при блокировке: {e}")
        raise InternalServerError()

@router.post("/user/{user_id}/unban", response_model=dict,  status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def unban_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Разблокирует пользователя и отправляет уведомление"""
    try:
        result = await db.execute(select(User).where(User.user_id == user_id, User.is_deleted == False))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise NotFoundError("Пользователь")
        
        await UserService.unban_user(db, user_id, current_user.user_id, is_admin=True)
        logger.info(f"[ADMIN] Пользователь {current_user.user_id} разблокировал пользователя {user_id}")
        
        from src.utils.email import EmailService
        content_html = "<p style='margin:0 0 16px;'>Ваш аккаунт был разблокирован администратором.</p>" \
                      "<p style='margin:0 0 16px;'>Вы можете снова использовать свой аккаунт.</p>"
        
        body = EmailService._render_email_html(
            title="Аккаунт разблокирован",
            user_full_name=target_user.user_full_name,
            content_html=content_html
        )
        await EmailService.send_email(target_user.user_email, "Аккаунт разблокирован", body)
        
        return {"detail": "Пользователь разблокирован и уведомлен."}
    
    except NotFoundError as e:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Неожиданная ошибка при разблокировке: {e}")
        raise InternalServerError()

@router.patch("/user/{user_id}/update", response_model=dict, status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def update_user_by_admin(
    request: Request,
    user_id: int,
    user_update: UserUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Изменять данные пользователя (только имя, почту, логин)"""
    try:
        if user_id == 1:
            raise ValueError("Невозможно изменить данные администратора")
        
        result = await db.execute(select(User).where(User.user_id == user_id))
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise NotFoundError("Пользователь")
        
        updates = {}

        user_login_clean = user_update.user_login.strip() if user_update.user_login else None
        user_full_name_clean = user_update.user_full_name.strip() if user_update.user_full_name else None
        user_email_clean = user_update.user_email.strip() if user_update.user_email else None

        if user_login_clean and user_login_clean != target_user.user_login:
            exists = await db.execute(select(User.user_id).where(User.user_login == user_login_clean).limit(1))
            if exists.scalar():
                raise ConflictError("Логин уже занят")
            updates["user_login"] = user_login_clean

        if user_full_name_clean and user_full_name_clean != target_user.user_full_name:
            updates["user_full_name"] = user_full_name_clean

        if user_email_clean and user_email_clean != target_user.user_email:
            exists = await db.execute(select(User.user_id).where(User.user_email == user_email_clean).limit(1))
            if exists.scalar():
                raise ConflictError("Email уже занят")
            
            updates["user_email"] = user_email_clean
            # updates["status"] = UserStatus.REGISTERED
            
        if not updates:
            return {
                "message": "Нет изменений",
                "user_id": target_user.user_id,
                "updated_fields": [],
            }


        stmt = update(User).where(User.user_id == user_id).values(**updates).returning(User)
        result = await db.execute(stmt)
        await db.commit()

        await ActionService.log_action(db, target_user.user_id, f"Администратор {current_user.user_id} обновил профиль")

        logger.info(f"[ADMIN] {current_user.user_id} изменил данные пользователя {user_id}: {updates}")
        
        from src.utils.email import EmailService
        await EmailService.send_profile_reset_notification(target_user.user_email, target_user.user_full_name, target_user.user_login)
        return {
            "message": "Данные пользователя обновлены",
            "user_id": user_id,
            "updated_fields": list(updates.keys())
        }
        
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except (ValidationError, AuthorizationError, ConflictError):
        await db.rollback()
        raise
    except (HTTPException, NotFoundError):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[ADMIN] Ошибка при изменении данных пользователя: {e}")
        raise InternalServerError()

@router.patch("/user/{user_id}/avatar", response_model=dict, status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def reset_user_profile_to_defaults(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сбросить аватарки пользователя до стандартной"""
    try:
        if user_id == 1:
            raise ValueError("Невозможно сбросить данные администратора")
        
        result = await db.execute(select(User).where(User.user_id == user_id))
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise NotFoundError("Пользователь")
        
        old_avatar = target_user.user_avatar
        target_user.user_avatar = "avatars/user-standart.png"
        await db.commit()
        
        logger.info(f"[ADMIN] {current_user.user_id} сбросил профиль пользователя {user_id}. Был аватар: {old_avatar}")

        await ActionService.log_action(db, target_user.user_id, f"Изменен профиль пользователя {user_id} админом {current_user.user_id}", notes=f"Дата: {(datetime.now(timezone.utc) + timedelta(hours=3)).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")}")
        await db.commit()

        from src.utils.email import EmailService
        await EmailService.send_profile_reset_notification(target_user.user_email, target_user.user_full_name, target_user.user_login)

        return {
            "message": "Профиль пользователя сброшен и пользователь уведомлен",
            "user_id": user_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при сбросе профиля: {e}")
        raise InternalServerError()

@router.patch("/pet/{pet_id}/update", response_model=dict, status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def update_pet_by_admin(
    request: Request,
    pet_id: int,
    pet_update: PetUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Изменять данные питомца (только имя, породу, окрас)"""
    try:
        from src.db.models import Pet
        from sqlalchemy import select
        
        result = await db.execute(
            select(Pet).where(Pet.pet_id == pet_id, Pet.is_deleted == False)
        )
        pet = result.scalar_one_or_none()
        
        if not pet:
            raise ValueError("Питомец не найден")
        
        pet_owner_id = pet.user_id
        update_data = {}
        
        if pet_update.name is not None:
            if not pet_update.name.strip():
                raise ValidationError("Кличка не может быть пустой", field="name")
            if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', pet_update.name.strip()):
                raise ValidationError("Кличка может содержать только английские и русские буквы, пробелы и дефис", field="name")
            update_data['name'] = pet_update.name.strip()
        
        if pet_update.gender is not None:
            if not pet_update.gender.strip():
                raise ValidationError("Пол не может быть пустой", field="gender")
            if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', pet_update.gender.strip()):
                raise ValidationError("Пол может содержать только английские и русские буквы, пробелы и дефис", field="gender")
            update_data['gender'] = pet_update.gender.strip()
        
        if pet_update.breed is not None:
            if not pet_update.breed.strip():
                raise ValidationError("Порода не может быть пустой", field="breed")
            if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', pet_update.breed.strip()):
                raise ValidationError("Порода может содержать только английские и русские буквы, пробелы и дефис", field="breed")
            update_data['breed'] = pet_update.breed.strip()
        
        if pet_update.color is not None:
            if not pet_update.color.strip():
                raise ValidationError("Окрас не может быть пустым", field="color")
            if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', pet_update.color.strip()):
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
        
        if update_data:
            await db.execute(
                update(Pet).where(Pet.pet_id == pet_id).values(**update_data)
            )
            await db.commit()
        
        logger.info(f"[ADMIN] {current_user.user_id} изменил данные питомца {pet_id} (владелец: {pet_owner_id}): {update_data}")
        
        owner_result = await db.execute(select(User).where(User.user_id == pet_owner_id))
        owner_user = owner_result.scalar_one_or_none()
        if owner_user:
            from src.utils.email import EmailService
            await EmailService.send_pet_profile_reset_notification(owner_user.user_email, owner_user.user_full_name, pet.name)
        
        return {
            "message": "Данные питомца обновлены",
            "pet_id": pet_id,
            "owner_id": pet_owner_id,
            "updated_fields": list(update_data.keys())
        }
        
    except ValueError as e:
        logger.error(f"[ADMIN] шибка валидации при обновлении питомца {pet_id}: {e}")
        raise ValidationError(str(e))
    except (ValidationError, AuthorizationError) as e:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при изменении данных питомца: {e}")
        raise InternalServerError()


@router.patch("/pet/{pet_id}/avatar", response_model=dict, status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def reset_pet_profile_to_defaults(
    request: Request,
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сбросить аватарки питомца до стандартной"""
    try:
        from src.db.models import Pet
        from sqlalchemy import select
        
        result = await db.execute(
            select(Pet).where(Pet.pet_id == pet_id, Pet.is_deleted == False)
        )
        pet = result.scalar_one_or_none()
        
        if not pet:
            raise ValueError("Питомец не найден")
        
        pet_owner_id = pet.user_id
        old_photo = pet.photo
        pet.photo = "pet-standart.png"
        await db.commit()

        logger.info(f"[ADMIN] {current_user.user_id} сбросил профиль питомца {pet_id} (владелец: {pet_owner_id}). Было фото: {old_photo}")

        await ActionService.log_action(db, pet_owner_id, f"Изменен профиль питомца {pet_id} администратором {current_user.user_id}", notes=f"Дата: {(datetime.now(timezone.utc) + timedelta(hours=3)).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")}")
        await db.commit()

        owner_result = await db.execute(select(User).where(User.user_id == pet_owner_id))
        owner_user = owner_result.scalar_one_or_none()
        if owner_user:
            from src.utils.email import EmailService
            await EmailService.send_pet_profile_reset_notification(owner_user.user_email, owner_user.user_full_name, pet.name)

        return {
            "message": "Профиль питомца сброшен до стандартных значений и владелец уведомлен",
            "pet_id": pet_id,
            "owner_id": pet_owner_id
        }
        
    except ValueError as e:
        logger.error(f"[ADMIN] Ошибка валидации при сбросе профиля питомца {pet_id}: {e}")
        raise ValidationError(str(e))
    except (ValidationError, AuthorizationError) as e:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при сбросе профиля питомца: {e}")
        raise InternalServerError()


@router.get("/pets/all", response_model=List[PetResponse], status_code=200)
@security_headers_check
@admin_required
@active_user_required
@cache(ttl=300, key_prefix="pet_search")
async def get_all_pets(
    request: Request,
    name: Optional[str] = None,
    gender: Optional[str] = None,
    date_birth: Optional[date] = None,
    weight: Optional[float] = None,
    breed: Optional[str] = None,
    color: Optional[str] = None,
    chip: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить всех питомцев с фильтрацией"""
    
    if not (1 <= limit <= 100):
        raise ValidationError("Лимит должен быть в диапазоне 1-100", field="limit")
    if offset < 0:
        raise ValidationError("Offset не может быть отрицательным", field="offset")

    query = select(Pet).where(Pet.is_deleted == False)

    if name:
        query = query.filter(Pet.name.ilike(f"%{name.strip()}%"))

    if gender:
        query = query.filter(Pet.gender.ilike(f"%{gender.strip()}%"))
  
    if date_birth:
        query = query.filter(Pet.date_birth == date_birth)

    if weight:
        query = query.filter(Pet.weight == weight)
        
    if breed:
        query = query.filter(Pet.breed.ilike(f"%{breed.strip()}%"))
        
    if color:
        query = query.filter(Pet.color.ilike(f"%{color.strip()}%"))
        
    if chip:
        query = query.filter(Pet.chip.ilike(f"%{chip.strip()}%"))

    try:
        result = await db.execute(query.order_by(Pet.pet_id).limit(limit).offset(offset))
        pets = result.scalars().all()
        
        if pets is None or pets == []:
            raise NotFoundError("Питомцы", multiple=True)
        return pets
    
    except (HTTPException, NotFoundError):
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка поиска питомцев: {e}")
        raise InternalServerError("Ошибка при выполнении поиска питомцев")
    
    
@router.get("/users/all", response_model=List[UserProfile])
@security_headers_check
@admin_required
@active_user_required
@cache(ttl=300, key_prefix="user_search")
async def get_all_users(
    request: Request,
    user_login: Optional[str] = None,
    user_full_name: Optional[str] = None,
    user_email: Optional[str] = None,
    role_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получение всех пользователей с фильтрацией"""
    
    if not (1 <= limit <= 100):
        raise ValidationError("Лимит должен быть в диапазоне 1-100", field="limit")
    if offset < 0:
        raise ValidationError("Offset не может быть отрицательным", field="offset")

    query = select(User).where(User.is_deleted == False)

    if user_login:
        query = query.where(User.user_login.ilike(f"%{user_login.strip()}%"))

    if user_full_name:
        query = query.where(User.user_full_name.ilike(f"%{user_full_name.strip()}%"))

    if user_email:
        query = query.where(User.user_email.ilike(f"%{user_email.strip()}%"))

    if role_id:
        if role_id not in (1, 3):
            raise ValidationError("Некорректный ID роли", field="role_id")
        query = query.filter(User.role_id == role_id)

    try:
        result = await db.execute(
            query.order_by(User.user_login.asc())
            .limit(limit)
            .offset(offset)
        )
        users = result.scalars().all()
        if users is None or users == []:
            raise NotFoundError("Пользователи", multiple=True)
        return users
        
    except (AuthorizationError, NotFoundError):
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка поиска пользователей: {e}")
        raise InternalServerError("Ошибка при выполнении поиска пользователей")


@router.get("/statistics", response_model=SystemStatistics, status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def get_system_statistics(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику системы для администратора"""
    try:
        total_users_result = await db.execute(
            select(User).where(User.is_deleted == False)
        )
        total_users = len(total_users_result.scalars().all())

        active_users_result = await db.execute(
            select(User).where(User.is_deleted == False, User.status == "ACTIVE")
        )
        active_users = len(active_users_result.scalars().all())

        total_pets_result = await db.execute(
            select(Pet).where()
        )
        total_pets = len(total_pets_result.scalars().all())

        active_pets_result = await db.execute(
            select(Pet).where(Pet.is_deleted == False, Pet.user_id.isnot(None))
        )
        active_pets = len(active_pets_result.scalars().all())

        from sqlalchemy import func
        from src.db.models import MedicalAction
        events_by_status_result = await db.execute(
            select(
                MedicalAction.status,
                func.count(MedicalAction.medical_action_id).label('count')
            )
            .where(MedicalAction.is_deleted == False)
            .group_by(MedicalAction.status)
        )

        medical_events_by_type = {}
        for row in events_by_status_result:
            medical_events_by_type[row.status.value] = row.count

        statistics = SystemStatistics(
            total_users=total_users,
            active_users=active_users,
            total_pets=total_pets,
            active_pets=active_pets,
            medical_events_by_status=medical_events_by_type
        )

        logger.info(f"[ADMIN] {current_user.user_id} запросил статистику системы")
        return statistics
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при получении статистики: {e}")
        raise InternalServerError()


@router.get("/user/{user_id}/logs", response_model=List[str], status_code=200)
@security_headers_check
@admin_required
@active_user_required
async def get_user_logs(
    request: Request,
    user_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить логи для пользователя"""
    try:
        result = await db.execute(
            select(Action)
            .where(Action.user_id == user_id)
            .order_by(Action.action_id.desc())
            .limit(limit)
        )

        actions = result.scalars().all()
        return [f"log id {action.action_id} | {action.description}" + (f" | Примечание: {action.notes}" if action.notes else "") for action in actions]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при чтении логов пользователя {user_id}: {e}")
        raise InternalServerError()



@router.delete("/pet/{pet_id}/delete", response_model=dict)
@security_headers_check
@admin_required
async def admin_delete_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить питомца (мягкое удаление) как админ"""
    try:

        pet = await PetService.get_pet_by_id(db, pet_id, user_id=current_user.user_id, is_admin=True)
        
        if pet.is_deleted:
            logger.warning(f"[ADMIN] Питомец {pet_id} уже был удален. Попытка удаления админом {current_user.user_id}")
            raise ConflictError("Питомец уже был удален ранее")
        
        await PetService.delete_pet(db, pet_id, current_user.user_id, is_admin=True)
        
        logger.info(f"[ADMIN] Питомец {pet_id} удален админом {current_user.user_id}")
        from src.users.services import ActionService
        await ActionService.log_action(db, current_user.user_id, f"Удален питомец {pet_id} админом", notes=f"Дата: {(datetime.now(timezone.utc) + timedelta(hours=3)).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")}")
        
        return {"message": "Питомец успешно удален админом."}
    
    except ValueError:
        logger.warning(f"[ADMIN] Питомец {pet_id} не найден или уже удален. Попытка удаления админом {current_user.user_id}")
        raise ConflictError("Питомец был удален или не найден")
    except Exception as e:
        logger.error(f"[ADMIN] Ошибка при удалении питомца {pet_id} админом: {e}")
        raise InternalServerError("Ошибка при удалении питомца")
    

@router.post("/pet/{pet_id}/restore", response_model=dict, status_code=200)
@security_headers_check
@admin_required
async def admin_restore_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Восстановление питомца админом без токена"""
    try:
        from sqlalchemy import select
        result = await db.execute(
            select(Pet).where(Pet.pet_id == pet_id, Pet.is_deleted == True)
        )
        pet = result.scalar_one_or_none()
        
        if not pet:
            raise NotFoundError("Удаленный питомец")
        
        pet.is_deleted = False
        await db.commit()
        
        logger.info(f"[ADMIN] Питомец {pet_id} восстановлен админом {current_user.user_id}")
        from src.users.services import ActionService
        await ActionService.log_action(db, current_user.user_id, f"Восстановлен питомец {pet_id} (админ)")
        
        return {"detail": "Питомец успешно восстановлен"}
    
    except NotFoundError:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[ADMIN] Ошибка восстановления питомца админом: {e}")
        raise InternalServerError("Ошибка восстановления питомца")