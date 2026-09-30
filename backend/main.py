from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config_app import settings
from src.core.config_log import logger
from src.core.exceptions import setup_exception_handlers
from src.core.notification_scheduler import start_notification_scheduler, stop_notification_scheduler

from src.users.routes import profile_router, admin_router
from src.auth.routes import router as auth_router
from src.images.routes import router as img_router
from src.pets.routes import pets_router, medical_events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("[MAIN] Запуск приложения...")
    
    try:
        from src.db.database import db_helper
        await db_helper.check_connection()
        await db_helper.create_tables()
        logger.info("[MAIN] БД подключена и таблицы созданы")
    except Exception as e:
        logger.error(f"[MAIN] Ошибка подключения БД: {e}")
        raise

    try:
        from src.cache.redis_service import redis_service
        await redis_service.connect()
        if redis_service.is_connected:
            logger.info("[MAIN] Redis подключен")
        else:
            logger.warning("[MAIN] Redis недоступен, кэширование отключено")
    except Exception as e:
        logger.warning(f"[MAIN] Redis ошибка: {e}")

    try:
        from src.core.lifespan import seed_initial_data
        await seed_initial_data()
        logger.info("[MAIN] Начальные данные загружены")
    except Exception as e:
        logger.error(f"[MAIN] Ошибка инициализации БД: {e}")
        raise

    # Запуск планировщика уведомлений
    try:
        start_notification_scheduler()
        logger.info("[MAIN] Планировщик уведомлений инициализирован")
    except Exception as e:
        logger.error(f"[MAIN] Ошибка при запуске планировщика: {e}")
    
    yield  # Приложение работает здесь
    
    logger.info("[MAIN] Остановка приложения")
    
    # Остановка планировщика
    try:
        stop_notification_scheduler()
    except Exception as e:
        logger.warning(f"[MAIN] Ошибка при остановке планировщика: {e}")
    
    try:
        await redis_service.close()
    except Exception as e:
        logger.warning(f"[MAIN] Ошибка при закрытии Redis: {e}")

    try:
        await db_helper.dispose()
    except Exception as e:
        logger.warning(f"[MAIN] Ошибка при закрытии БД: {e}")
    
    logger.info("[MAIN] Приложение остановлено")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="REST API для учета здоровья питомцев",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
)

setup_exception_handlers(app)

try:
    # Аутентификация
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

    # Пользователи
    app.include_router(profile_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])

    # Питомцы и медицинские события
    app.include_router(pets_router, prefix="/api/v1/pets", tags=["Pets"])
    app.include_router(medical_events_router, prefix="/api/v1/pets", tags=["Medical Events"])

    # Изображения
    app.include_router(img_router, prefix="/api/v1/images", tags=["Images"])

    @app.get("/api/v1/health", tags=["Health"])
    async def health_check():
        """Проверка здоровья приложения"""
        return {
            "status": "ok",
            "version": settings.PROJECT_VERSION,
            "service": settings.PROJECT_NAME
        }

except Exception as e:
    logger.warning(f"[MAIN] Ошибка подключения routes: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
        log_level="info"
    )
