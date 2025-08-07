import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import CORS_ORIGINS
from app.dependencies import container
from app.router import router as api_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan менеджер для FastAPI"""
    logger.info("🚀 FastAPI приложение запускается...")
    yield
    logger.info("🛑 FastAPI приложение завершает работу...")
    # Закрываем движок БД
    engine = container.engine()
    await engine.dispose()


def create_app() -> FastAPI:
    """Создание и настройка FastAPI приложения"""
    app = FastAPI(
        title="Google Sheets Events API",
        description="API для работы с событиями из Google Sheets",
        version="1.0.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    app.include_router(api_router)

    # Улучшенная настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    # Настройка dependency injection
    app.container = container

    return app


# Создаем приложение
app = create_app()


if __name__ == "__main__":
    print("Запустите приложение командой: python run.py")
