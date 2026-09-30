import asyncio
from typing import AsyncGenerator
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import text

from src.core.config_app import settings
from src.core.config_log import logger
from src.core.exceptions import AuthenticationError, ValidationError, NotFoundError, ConflictError, AuthorizationError


class Base(DeclarativeBase):
    pass

class DatabaseHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            connect_args={
                "command_timeout": 30,
                "server_settings": {
                    "application_name": "PetCore",
                    "statement_timeout": "30000",
                    "idle_in_transaction_session_timeout": "60000"
                }
            }
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )

    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Генератор сессии для FastAPI Depends().
        Обеспечивает автоматическое закрытие сессии (context manager).
        """
        async with self.session_factory() as session:
            try:
                yield session
            except (HTTPException, ValidationError, AuthorizationError, AuthenticationError, NotFoundError, ConflictError):
                # Это ожидаемая ошибка (401, 403, 404), не логируем её как ошибку БД
                raise
            except Exception as e:
                logger.error(f"[DatabaseHelper] КРИТИЧЕСКАЯ ОШИБКА СЕССИИ: {e}")
                raise

    async def check_connection(self, max_attempts: int = 3, delay: int = 2) -> None:
        """Проверяет соединение с базой при старте (Health Check)"""
        attempt = 1
        while attempt <= max_attempts:
            try:
                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                logger.info("[DatabaseHelper] Подключение успешно")
                return
            except Exception as e:
                logger.warning(f"[DatabaseHelper] Попытка {attempt}/{max_attempts} не удалась: {e}")
                if attempt == max_attempts:
                    logger.error("[DatabaseHelper] Подключение недоступно")
                    raise e
                await asyncio.sleep(delay)
                attempt += 1

    async def create_tables(self):
        """Создать все таблицы"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[DatabaseHelper] Таблицы созданы")

    async def dispose(self) -> None:
        """Корректное закрытие пула соединений при остановке приложения"""
        await self.engine.dispose()
        logger.info("[DatabaseHelper] Пул соединений закрыт")


db_helper = DatabaseHelper(
    url=settings.ASYNC_DATABASE_URL,
    echo=False
)

get_db = db_helper.get_db