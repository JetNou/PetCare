from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.core.config_log import logger
from src.db.database import db_helper
from src.db.models import MedicalAction, MedicalHistory, MedicalHistoryStatus, UserStatus, Pet
from src.utils.email import EmailService

scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Moscow"))

async def send_medical_event_notifications() -> None:
    """Проверка предстоящих процедур и отправка уведомлений (за 24ч)"""
    logger.info("[Scheduler] Запуск проверки предстоящих медицинских процедур...")
    
    async with db_helper.session_factory() as session:
        try:
            now = datetime.now(timezone.utc)
            tomorrow = now + timedelta(hours=24)
            
            query = (
                select(MedicalAction)
                .where(
                    (MedicalAction.status == MedicalHistoryStatus.PLANNED) &
                    (MedicalAction.date >= now) &
                    (MedicalAction.date <= tomorrow) &
                    (MedicalAction.is_deleted == False)
                )
                .options(
                    joinedload(MedicalAction.medical_history)
                        .joinedload(MedicalHistory.pet)
                        .joinedload(Pet.user)
                )
            )
            
            result = await session.execute(query)
            medical_actions = result.unique().scalars().all()
            
            if not medical_actions:
                logger.info("[Scheduler] Предстоящих медицинских процедур не найдено")
                return
            
            for action in medical_actions:
                await _send_notification_for_action(session, action)
                
        except Exception as e:
            logger.error(f"[Scheduler] Ошибка уведомлений: {e}", exc_info=True)


async def check_and_update_overdue_events() -> None:
    """Помечает события как просроченные, не меняя их оригинальную дату и время."""
    logger.info("[Scheduler] Запуск проверки просроченных медицинских процедур...")
    async with db_helper.session_factory() as session:
        try:
            now = datetime.now(timezone.utc)
            query = select(MedicalAction).where(
                (MedicalAction.status == MedicalHistoryStatus.PLANNED) &
                (MedicalAction.date < now) &
                (MedicalAction.is_deleted == False)
            )
            result = await session.execute(query)
            overdue_actions = result.scalars().all()

            for action in overdue_actions:
                action.status = MedicalHistoryStatus.OVERDUE
                session.add(action)
                logger.info(f"[Scheduler] Событие ID {action.medical_action_id} ({action.type_action.value}) -> OVERDUE")
            
            await session.commit()
        except Exception as e:
            logger.error(f"[Scheduler] Ошибка при обновлении просроченных: {e}")
            await session.rollback()


async def create_recurring_events() -> None:
    """Создает новое запланированное событие через N дней для любого события с интервалом, если такое еще не было создано."""
    logger.info("[Scheduler] Запуск проверки периодических медицинских процедур...")
    async with db_helper.session_factory() as session:
        try:
            query = select(MedicalAction).where(
                (MedicalAction.interval_period.isnot(None)) &
                (MedicalAction.is_deleted == False)
            )
            result = await session.execute(query)
            actions = result.scalars().all()

            created_count = 0
            for action in actions:
                next_date = action.date + timedelta(days=action.interval_period)
                
                check_query = select(MedicalAction).where(
                    (MedicalAction.medical_history_id == action.medical_history_id) &
                    (MedicalAction.type_action == action.type_action) &
                    (MedicalAction.date == next_date) &
                    (MedicalAction.is_deleted == False)
                )
                check_result = await session.execute(check_query)
                if check_result.scalar():
                    continue 

                new_action = MedicalAction(
                    medical_history_id=action.medical_history_id,
                    type_action=action.type_action,
                    description=action.description,
                    interval_period=action.interval_period,
                    date=next_date,
                    status=MedicalHistoryStatus.PLANNED,
                    notes=None,
                    is_deleted=False
                )
                session.add(new_action)
                created_count += 1
                logger.info(f"[Scheduler] Создано повторение для ID {action.medical_action_id} на {next_date}")

            await session.commit()
            logger.info(f"[Scheduler] Всего создано новых повторений: {created_count}")
        except Exception as e:
            logger.error(f"[Scheduler] Ошибка при создании повторов: {e}")
            await session.rollback()

async def _send_notification_for_action(session: AsyncSession, action: MedicalAction) -> None:
    """Отправляет уведомление для конкретной медицинской процедуры"""
    try:
        pet = action.medical_history.pet
        user = pet.user
        
        if user.status != UserStatus.ACTIVE:
            logger.info(f"[Scheduler] Уведомление не отправлено для питомца '{pet.name}' (ID {pet.pet_id}): email пользователя не подтвержден")
            return
        
        action_type_names = {
            "inspection": "Осмотр",
            "tests": "Анализы",
            "diagnostics": "Диагностика",
            "complex": "Комплекс мероприятий",
            "parasite_treatment": "Обработка от паразитов",
            "surgery": "Операция",
            "treatment_course": "Курс лечения",
            "dentistry": "Стоматология",
            "grooming": "Груминг",
            "other": "Прочее"
        }
        
        type_name = action_type_names.get(action.type_action.value, action.type_action.value)
        event_date = action.date.strftime("%d.%m.%Y %H:%M")
        
        content_html = f"""
            <p>У Вашего питомца <strong>{pet.name}</strong> (ID: {pet.pet_id}) запланирована медицинская процедура:</p>
            
            <div style="margin:20px 0; padding:14px; background:#f5f5f5; border-left:4px solid #E67E22; border-radius:4px;">
                <p><strong>Тип процедуры:</strong> {type_name}</p>
                <p><strong>Дата и время:</strong> {event_date}</p>
                {f'<p><strong>Описание:</strong> {action.description}</p>' if action.description else ''}
                {f'<p><strong>Примечания:</strong> {action.notes}</p>' if action.notes else ''}
            </div>
            
            <p>Пожалуйста, не забудьте подготовить питомца к процедуре и явиться вовремя.</p>
        """
        
        html_body = EmailService._render_email_html(
            title="Напоминание о медицинской процедуре",
            user_full_name=user.user_full_name,
            content_html=content_html
        )
        
        success = await EmailService.send_email(
            to=user.user_email,
            subject=f"Напоминание: {type_name} для {pet.name}",
            body=html_body,
            html=True
        )
        
        if success:
            logger.info(f"[Scheduler] Уведомление отправлено пользователю {user.user_email} о процедуре '{type_name}' для питомца '{pet.name}' (ID {pet.pet_id})")
        else:
            logger.warning(f"[Scheduler] Не удалось отправить уведомление пользователю {user.user_email} о процедуре для питомца '{pet.name}' (ID {pet.pet_id})")
            
    except Exception as e:
        logger.error(f"[Scheduler] Ошибка при отправке уведомления о медицинской процедуре: {e}", exc_info=True)



def start_notification_scheduler() -> None:
    """Настраивает и запускает планировщик задач, если он еще не запущен."""
    if not scheduler.running:
        scheduler.add_job(check_and_update_overdue_events, "cron", hour=0, minute=0, 
                          id="overdue", misfire_grace_time=3600, coalesce=True)
        
        scheduler.add_job(send_medical_event_notifications, "cron", hour=0, minute=1, 
                          id="notify", misfire_grace_time=3600, coalesce=True)
        
        scheduler.add_job(create_recurring_events, "cron", hour=0, minute=2, 
                          id="recurring", misfire_grace_time=3600, coalesce=True)
        
        scheduler.start()
        logger.debug("[Scheduler] Запущен (00:00 - Overdue, 00:01 - Notify, 00:02 - Recurring)")

def stop_notification_scheduler() -> None:
    """Останавливает планировщик, если он запущен."""
    if scheduler.running:
        scheduler.shutdown()