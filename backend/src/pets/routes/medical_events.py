from typing import Optional
from io import BytesIO
from fastapi import APIRouter, Depends, status, Query, Body
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.decorators import security_headers_check, active_user_required
from src.db.database import get_db
from src.db.models import User, MedicalHistoryStatus
from src.auth.auth import get_current_user
from src.core.exceptions import NotFoundError, InternalServerError
from src.core.config_log import logger
from src.pets.schemas import MedicalEventCreate,  MedicalEventUpdate, MedicalEventResponse, MedicalHistoryResponse
from src.pets.services import PetService, MedicalEventService
from src.pets.utils import MedicalEventExportService
from src.users.services import ActionService


router = APIRouter()

@router.post("/{pet_id}/medical_events", response_model=MedicalEventResponse, status_code=status.HTTP_201_CREATED)
@security_headers_check
@active_user_required
async def create_medical_event(
    pet_id: int,
    event_data: MedicalEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать новое медицинское событие для питомца"""
    try:
        await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        
        event = await MedicalEventService.create_medical_event(db, current_user.user_id, event_data, pet_id)
        logger.info(f"Медицинское событие создано для питомца {pet_id} пользователем {current_user.user_id}")
        await ActionService.log_action(db, current_user.user_id, f"Создано медицинское событие {event.medical_action_id} для питомца {pet_id}")
        return event
    except ValueError:
        logger.warning(f"Питомец {pet_id} не найден для пользователя {current_user.user_id}")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании медицинского события: {e}")
        raise InternalServerError("Ошибка при создании события")

@router.get("/{pet_id}/medical_events/{event_id}", response_model=MedicalEventResponse)
@security_headers_check
@active_user_required
async def get_medical_event(
    pet_id: int,
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить информацию о конкретном медицинском событии"""
    try:
        await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        event = await MedicalEventService.get_medical_event(db, event_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        return event
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} не найден для пользователя {current_user.user_id}")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении события {event_id}: {e}")
        raise InternalServerError("Ошибка при получении события")

@router.patch("/{pet_id}/medical_events/{event_id}", response_model=MedicalEventResponse)
@security_headers_check
@active_user_required
async def update_medical_event(
    pet_id: int,
    event_id: int,
    event_update: MedicalEventUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Частично обновить медицинское событие"""
    try:
        await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        
        event = await MedicalEventService.update_medical_event(db, event_id, current_user.user_id, event_update, is_admin=(current_user.role_id == 1))
        logger.info(f"Событие {event_id} питомца {pet_id} обновлено пользователем {current_user.user_id}")
        await ActionService.log_action(db, current_user.user_id, f"Обновлено медицинское событие {event_id} питомца {pet_id}")
        return event
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} не найден для пользователя {current_user.user_id}")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении события {event_id}: {e}")
        raise InternalServerError("Ошибка при обновлении события")

@router.get("/{pet_id}/medical_events", response_model=MedicalHistoryResponse)
@security_headers_check
@active_user_required
async def get_pet_medical_history(
    pet_id: int,
    status: Optional[MedicalHistoryStatus] = Query(None, description="Фильтр по статусу"),
    limit: int = Query(50, ge=1, le=500, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить полную медицинскую историю питомца (все события)"""
    try:
        pet = await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        events, total = await MedicalEventService.get_pet_medical_history(
            db, pet_id, current_user.user_id, status=status, limit=limit, offset=offset
        )
        
        return MedicalHistoryResponse(
            pet_id=pet.pet_id,
            pet_name=pet.name,
            events=events,
            total_events=total
        )
        
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} не найден для пользователя {current_user.user_id}")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении истории питомца {pet_id}: {e}")
        raise InternalServerError("Ошибка при получении истории")

@router.delete("/{pet_id}/medical_events/{event_id}", response_model=dict)
@security_headers_check
@active_user_required
async def delete_medical_event(
    pet_id: int,
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить медицинское событие"""
    try:
        await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        await MedicalEventService.delete_medical_event(db, event_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        logger.info(f"Событие {event_id} удалено пользователем {current_user.user_id}")
        await ActionService.log_action(db, current_user.user_id, f"Удалено медицинское событие {event_id} питомца {pet_id}")
        return {
            "message": "Медицинское событие успешно удалено"
        }
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} не найден")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении события {event_id}: {e}")
        raise InternalServerError("Ошибка при удалении события")

@router.get("/{pet_id}/export/pdf")
@security_headers_check
@active_user_required
async def export_pet_history_pdf(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Экспортировать медицинскую историю питомца в PDF (документ)"""
    try:
        pet = await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        events, _ = await MedicalEventService.get_pet_medical_history(
            db, pet_id, current_user.user_id, limit=1000
        )
        
        pdf_buffer = MedicalEventExportService.export_medical_history_to_pdf(
            pet_name=pet.name,
            events=events,
            user_name=current_user.user_full_name
        )
        
        filename = f"pet_{pet.pet_id}_history.pdf"
        logger.info(f"PDF история питомца {pet_id} экспортирована пользователем {current_user.user_id}")
        await ActionService.log_action(db, current_user.user_id, f"Экспортирована PDF история питомца {pet_id}")
        
        if isinstance(pdf_buffer, BytesIO):
            pdf_buffer.seek(0)
            return StreamingResponse(
                iter([pdf_buffer.getvalue()]),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            return FileResponse(
                path=pdf_buffer,
                filename=filename,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} не найден")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except ImportError as e:
        logger.error(f"Библиотека для экспорта PDF не установлена: {e}")
        raise InternalServerError("Функция экспорта недоступна")
    except Exception as e:
        logger.error(f"Ошибка при экспорте PDF питомца {pet_id}: {e}")
        raise InternalServerError("Ошибка при экспорте в PDF")

@router.get("/{pet_id}/export/calendar")
@security_headers_check
@active_user_required
async def export_pet_events_to_calendar(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Экспортировать медицинские события в ICS формат (календарь)"""
    try:
        pet = await PetService.get_pet_by_id(db, pet_id, current_user.user_id, is_admin=(current_user.role_id == 1))
        events, _ = await MedicalEventService.get_pet_medical_history(
            db, pet_id, current_user.user_id, limit=1000
        )
        
        ics_buffer = MedicalEventExportService.export_medical_events_to_ics(
            pet_name=pet.name,
            events=events,
            user_email=current_user.user_email
        )
        
        filename = f"pet_{pet.pet_id}_calendar.ics"
        logger.info(f"ICS календарь питомца {pet_id} экспортирован пользователем {current_user.user_id}")
        await ActionService.log_action(db, current_user.user_id, f"Экспортирован ICS календарь питомца {pet_id}")
        
        if isinstance(ics_buffer, BytesIO):
            ics_buffer.seek(0)
            return StreamingResponse(
                iter([ics_buffer.getvalue()]),
                media_type="text/calendar",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            return FileResponse(
                path=ics_buffer,
                filename=filename,
                media_type="text/calendar",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except ValueError as e:
        logger.warning(f"Питомец {pet_id} не найден")
        raise NotFoundError("Питомец")
    except NotFoundError:
        raise
    except ImportError as e:
        logger.error(f"Библиотека для экспорта ICS не установлена: {e}")
        raise InternalServerError("Функция экспорта недоступна")
    except Exception as e:
        logger.error(f"Ошибка при экспорте ICS питомца {pet_id}: {e}")
        raise InternalServerError("Ошибка при экспорте в календарь")
    
