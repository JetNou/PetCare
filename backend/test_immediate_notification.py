import asyncio
from datetime import datetime, timedelta, timezone
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.database import db_helper
from src.db.models import UserStatus, Pet, MedicalHistory, MedicalAction, MedicalHistoryStatus

from src.utils.email import EmailService
from src.core.config_log import logger


async def test_immediate():
    """Запускает срочный тест отправки уведомления"""
    
    logger.info("[TEST] СРОЧНЫЙ ТЕСТ ОТПРАВКИ УВЕДОМЛЕНИЯ")
    logger.info("[TEST] (Московское время, без ожидания 00:00)")
    
    try:
        logger.info("[TEST] Проверка БД...")
        await db_helper.check_connection()
        await db_helper.create_tables()
        logger.info("[TEST] БД подключена")
        
        async with db_helper.session_factory() as session:
            
            msk = pytz.timezone('Europe/Moscow')
            now_msk = datetime.now(msk)
            
            now = datetime.now(timezone.utc)
            tomorrow = now + timedelta(hours=24)
            
            logger.info(f"[TEST] Текущее время (МСК): {now_msk.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"[TEST] Текущее время (UTC): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"[TEST] Диапазон поиска (UTC): {now} - {tomorrow}")
            
            from sqlalchemy import text
            query_text = text("""
                SELECT ma.medical_action_id, ma.medical_history_id, ma.type_action, 
                       ma.date, ma.status, ma.description, ma.notes, ma.interval_period,
                       mh.medical_history_id as mh_id,
                       p.pet_id, p.name as pet_name, p.user_id,
                       u.user_id as u_id, u.user_email, u.user_full_name, u.status as user_status
                FROM medical_actions ma
                LEFT JOIN medical_histories mh ON ma.medical_history_id = mh.medical_history_id
                LEFT JOIN pets p ON mh.medical_history_id = p.medical_history_id
                LEFT JOIN users u ON p.user_id = u.user_id
                WHERE ma.status = 'PLANNED' AND ma.date >= :now AND ma.date <= :tomorrow AND ma.is_deleted = false
            """)
            
            result = await session.execute(query_text, {"now": now, "tomorrow": tomorrow})
            rows = result.fetchall()
            
            if not rows:
                logger.warning("[TEST] Не найдено событий для уведомления в следующие 24 часа")
                logger.info("[TEST] СПОСОБЫ СОЗДАНИЯ ТЕСТОВОГО СОБЫТИЯ:")
                logger.info("[TEST]    1. Запустите: python test_notifications.py")
                logger.info("[TEST]    2. Или создайте событие вручную через API")
                logger.info("[TEST]    3. Событие должно иметь статус PLANNED и дату в течение 24 часов")
                return
            
            logger.info(f"[TEST] Найдено {len(rows)} события(й) для уведомления:")
            
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
            
            for i, row in enumerate(rows, 1):
                medical_action_id, medical_history_id, type_action, event_date, status, description, notes, interval_period, \
                    mh_id, pet_id, pet_name, user_id, u_id, user_email, user_full_name, user_status = row
                
                logger.info(f"[TEST] Событие #{i}:")
                logger.info(f"[TEST]  Питомец: {pet_name} (ID: {pet_id})")
                logger.info(f"[TEST]  Пользователь: {user_full_name} ({user_email})")
                logger.info(f"[TEST]  Статус почты: {user_status}")
                
                if user_status != "ACTIVE":
                    logger.warning(f"[TEST]  Почта не подтверждена, уведомление не отправится")
                    continue
                
                type_name = action_type_names.get(type_action, type_action)
                event_date_str = event_date.strftime("%d.%m.%Y %H:%M") if hasattr(event_date, 'strftime') else str(event_date)
                
                logger.info(f"[TEST]  Тип процедуры: {type_name}")
                logger.info(f"[TEST]  Дата события: {event_date_str}")
                
                content_html = f"""
                    <p>У Вашего питомца <strong>{pet_name}</strong> (ID: {pet_id}) запланирована медицинская процедура:</p>
                    
                    <div style="margin:20px 0; padding:14px; background:#f5f5f5; border-left:4px solid #E67E22; border-radius:4px;">
                        <p><strong>Тип процедуры:</strong> {type_name}</p>
                        <p><strong>Дата и время:</strong> {event_date_str}</p>
                        {f'<p><strong>Описание:</strong> {description}</p>' if description else ''}
                        {f'<p><strong>Примечания:</strong> {notes}</p>' if notes else ''}
                    </div>
                    
                    <p>Пожалуйста, не забудьте подготовить питомца к процедуре и явиться вовремя.</p>
                """
                
                html_body = EmailService._render_email_html(
                    title="Напоминание о медицинской процедуре",
                    user_full_name=user_full_name,
                    content_html=content_html
                )
                
                logger.info(f"[TEST]  Отправка письма на {user_email}...")
                success = await EmailService.send_email(
                    to=user_email,
                    subject=f"Напоминание: {type_name} для {pet_name}",
                    body=html_body,
                    html=True
                )
                
                if success:
                    logger.info(f"[TEST]  Письмо успешно отправлено!")
                else:
                    logger.error(f"[TEST]  Ошибка при отправке письма")
        
        logger.info("[TEST] ТЕСТ ЗАВЕРШЕН")
        
    except Exception as e:
        logger.error(f"[TEST] ОШИБКА: {e}", exc_info=True)
    
    finally:
        await db_helper.dispose()


if __name__ == "__main__":
    asyncio.run(test_immediate())
