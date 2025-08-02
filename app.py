import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from service.models import Event
from service.scheduler_service import SchedulerService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем сервис
scheduler_service = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan менеджер для FastAPI"""
    logger.info("🚀 FastAPI приложение запускается...")
    yield
    logger.info("🛑 FastAPI приложение завершает работу...")


def create_app() -> FastAPI:
    """Создание и настройка FastAPI приложения"""
    app = FastAPI(
        title="Google Sheets Events API",
        description="API для работы с событиями из Google Sheets",
        version="1.0.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # Улучшенная настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    return app


# Создаем приложение
app = create_app()


# Dependency для получения сервиса
def get_scheduler_service() -> SchedulerService:
    """Dependency для получения сервиса планировщика"""
    return scheduler_service


@app.on_event("startup")
async def startup_event():
    """Инициализация приложения"""
    logger.info("API сервер запущен")


@app.get("/health")
async def health_check(
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
):
    """Проверка состояния API"""
    try:
        logger.info("Выполняется health check")
        if scheduler_service.is_connected():
            logger.info("Google API подключен")
            return {"status": "healthy", "google_api": "connected"}
        else:
            logger.warning("Google API отключен")
            return {"status": "healthy", "google_api": "disconnected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/schedule")
async def get_schedule(
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> list[Event]:
    """Получение расписания событий"""
    try:
        logger.info("Запрос расписания")
        return await scheduler_service.get_events()
    except Exception as e:
        logger.error(f"Failed to get schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedule: {str(e)}")


@app.get("/schedule/refresh")
async def refresh_schedule(
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> list[Event]:
    """Принудительное обновление кэша расписания"""
    try:
        logger.info("Принудительное обновление расписания")
        events = await scheduler_service.refresh_events()
        logger.info(f"Обновлено {len(events)} событий")
        return events
    except Exception as e:
        logger.error(f"Failed to refresh schedule: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh schedule: {str(e)}"
        )
