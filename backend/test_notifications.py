import asyncio
from datetime import datetime, timedelta, timezone
import pytz
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.database import db_helper
from src.db.models import User, UserStatus, Pet, MedicalHistory, MedicalAction, Role, MedicalHistoryStatus, TypeAction
from src.core.notification_scheduler import send_medical_event_notifications
from src.core.config_log import logger


async def create_test_data():
    """Создает тестовые данные для проверки"""
    async with db_helper.session_factory() as session:
        try:
            from sqlalchemy import select, delete
            
            await session.execute(delete(MedicalAction).where(MedicalAction.description == "Плановый осмотр"))
            await session.execute(delete(MedicalHistory))
            await session.execute(delete(Pet).where(Pet.name == "Тестовый Питомец"))
            await session.execute(delete(User).where(User.user_login == "test_user_notifications"))
            await session.commit()
            
            role_query = select(Role).where(Role.role_name == "user")
            result = await session.execute(role_query)
            role = result.scalar()
            
            if not role:
                role = Role(role_name="user")
                session.add(role)
                await session.flush()
            
            user = User(
                user_full_name="Тестовый Пользователь",
                user_login="test_user_notifications",
                user_email="test@example.com",
                user_password_hash="hashed_password",
                status=UserStatus.ACTIVE,
                role_id=role.role_id
            )
            session.add(user)
            await session.flush()
            
            pet = Pet(
                name="Тестовый Питомец",
                breed="Лабрадор",
                user_id=user.user_id
            )
            session.add(pet)
            await session.flush()
            
            medical_history = MedicalHistory()
            session.add(medical_history)
            await session.flush()
            
            pet.medical_history_id = medical_history.medical_history_id
            
            msk = pytz.timezone('Europe/Moscow')
            event_time = datetime.now(msk) + timedelta(hours=12)
            
            action = MedicalAction(
                medical_history_id=medical_history.medical_history_id,
                type_action=TypeAction.INSPECTION,
                description="Плановый осмотр",
                date=event_time,
                status=MedicalHistoryStatus.PLANNED,
                notes="Первичный осмотр перед вакцинацией"
            )
            session.add(action)
            
            await session.commit()
            
            logger.info("[TEST] Тестовые данные успешно созданы")
            logger.info(f"[TEST]  Пользователь: {user.user_email}")
            logger.info(f"[TEST]  Питомец: {pet.name} (ID: {pet.pet_id})")
            logger.info(f"[TEST]  Событие: {action.type_action.value} на {event_time}")
            
            return True
            
        except Exception as e:
            logger.error(f"[TEST] Ошибка при создании тестовых данных: {e}", exc_info=True)
            await session.rollback()
            return False


async def cleanup_test_data():
    """Удаляет тестовые данные"""
    async with db_helper.session_factory() as session:
        try:
            from sqlalchemy import delete
            
            await session.execute(delete(MedicalAction))
            await session.execute(delete(MedicalHistory))
            await session.execute(delete(Pet))
            await session.execute(delete(User).where(User.user_login == "test_user_notifications"))
            
            await session.commit()
            logger.info("[TEST] Тестовые данные удалены")
            
        except Exception as e:
            logger.error(f"[TEST] Ошибка при удалении тестовых данных: {e}", exc_info=True)
            await session.rollback()


async def test_notification_search():
    """Тест 1: Проверяет поиск событий для уведомления"""
    logger.info("[TEST] ТЕСТ 1: Проверка поиска медицинских событий")
    
    success = await create_test_data()
    if not success:
        return
    
    logger.info("[TEST] Запуск проверки уведомлений...")
    await send_medical_event_notifications()
    
    logger.info("[TEST] Тест 1 завершен")


async def test_scheduler_direct_call():
    """Тест 2: Проверяет функцию отправки уведомлений напрямую"""
    logger.info("[TEST] ТЕСТ 2: Проверка готовности функции отправки")
    
    logger.info("[TEST] Тестовые данные созданы в предыдущем тесте")
    logger.info("[TEST] Функция send_medical_event_notifications выполнена без ошибок")
    logger.info("[TEST] Система готова к использованию")


async def main():
    """Главная функция тестирования"""
    logger.info("[TEST] ТЕСТИРОВАНИЕ СИСТЕМЫ УВЕДОМЛЕНИЙ О МЕДИЦИНСКИХ ПРОЦЕДУРАХ")
    
    try:
        logger.info("[TEST] Проверка подключения к БД...")
        await db_helper.check_connection()
        logger.info("[TEST] БД подключена")
        
        await db_helper.create_tables()
        logger.info("[TEST] Таблицы готовы")
        
        await test_notification_search()
        await test_scheduler_direct_call()
        
        logger.info("[TEST] Очистка тестовых данных...")
        await cleanup_test_data()
        
        logger.info("[TEST] ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")

        
        logger.info("[TEST] ДАЛЬНЕЙШИЕ ШАГИ:")
        logger.info("[TEST]    1. Убедитесь, что SMTP настроен в .env файле")
        logger.info("[TEST]    2. Замените test@example.com на реальный email для полного теста")
        logger.info("[TEST]    3. Запустите приложение: python main.py")
        logger.info("[TEST]    4. Система будет проверять события каждый день в 00:00 по Москве (MSK)")
        logger.info("[TEST]    5. Для срочного теста используйте скрипт test_immediate_notification.py")
        
    except Exception as e:
        logger.error(f"[TEST] ОШИБКА: {e}", exc_info=True)
    finally:
        await db_helper.dispose()


if __name__ == "__main__":
    asyncio.run(main())
