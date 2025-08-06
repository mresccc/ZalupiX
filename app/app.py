import hashlib
import hmac
import json
import logging
from contextlib import asynccontextmanager
from datetime import date
from urllib.parse import parse_qs, unquote

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import BOT_TOKEN, CORS_ORIGINS
from app.container import Container
from app.repository.user import UserRepository
from app.schemas import (
    HealthResponse,
    ScheduleResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from app.service.models import UserProfile
from app.service.scheduler_service import SchedulerService
from app.service.user_service import UserService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем контейнер зависимостей
container = Container()
container.config.from_dict({})
container.wire(modules=[__name__])


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """Валидация init_data от Telegram Mini App"""
    try:
        # Парсим init_data
        parsed_data = parse_qs(init_data)

        # Извлекаем hash
        received_hash = parsed_data.get("hash", [None])[0]
        if not received_hash:
            raise ValueError("Hash не найден в init_data")

        # Удаляем hash из данных для проверки
        data_check_string_parts = []
        for key, value in parsed_data.items():
            if key != "hash":
                data_check_string_parts.append(f"{key}={value[0]}")

        # Сортируем параметры
        data_check_string_parts.sort()
        data_check_string = "\n".join(data_check_string_parts)

        # Создаем secret key
        secret_key = hmac.new(
            "WebAppData".encode(), bot_token.encode(), hashlib.sha256
        ).digest()

        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        # Проверяем hash
        if calculated_hash != received_hash:
            raise ValueError("Неверный hash")

        # Парсим данные пользователя
        user_data = {}
        if "user" in parsed_data:
            user_data = json.loads(unquote(parsed_data["user"][0]))

        return user_data

    except Exception as e:
        logger.error(f"Ошибка валидации init_data: {str(e)}")
        raise ValueError(f"Ошибка валидации: {str(e)}")


# Создаем сервис
scheduler_service = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan менеджер для FastAPI"""
    logger.info("🚀 FastAPI приложение запускается...")
    yield
    logger.info("🛑 FastAPI приложение завершает работу...")
    # Закрываем движок БД
    if _engine:
        await _engine.dispose()


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


# Dependency для получения сервиса
def get_scheduler_service() -> SchedulerService:
    """Dependency для получения сервиса планировщика"""
    return scheduler_service


# Глобальные переменные для движка и фабрики сессий
_engine = None
_session_factory = None


def get_engine():
    """Получение движка БД (синглтон)"""
    global _engine
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine

        _engine = create_async_engine(
            "sqlite+aiosqlite:///./zalupix.db", echo=False, future=True
        )
    return _engine


def get_session_factory():
    """Получение фабрики сессий (синглтон)"""
    global _session_factory
    if _session_factory is None:
        from sqlalchemy.ext.asyncio import async_sessionmaker

        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def get_db_session():
    """Dependency для получения сессии БД"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_user_service(db_session=Depends(get_db_session)) -> UserService:
    """Dependency для получения сервиса пользователя"""
    repository = UserRepository(db_session)
    return UserService(repository)


# Удаляем устаревший on_event, используем lifespan


@app.get("/health")
async def health_check(
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> HealthResponse:
    """Проверка состояния API"""
    try:
        logger.info("Выполняется health check")
        if scheduler_service.is_connected():
            logger.info("Google API подключен")
            return HealthResponse(status="healthy", google_api="connected")
        else:
            logger.warning("Google API отключен")
            return HealthResponse(status="healthy", google_api="disconnected")
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/schedule")
async def get_schedule(
    refresh: bool = Query(
        default=False, description="Принудительное обновление кэша", examples=[False]
    ),
    start_date: date = Query(
        default=None, description="Начальная дата", examples=[None]
    ),
    end_date: date = Query(default=None, description="Конечная дата", examples=[None]),
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduleResponse:
    """Получение расписания событий"""
    try:
        if refresh:
            logger.info("Принудительное обновление расписания")
            events = await scheduler_service.refresh_events()
            logger.info(f"Обновлено {len(events)} событий")
            return ScheduleResponse(events=events)
        else:
            logger.info("Запрос расписания")
            events = await scheduler_service.get_events(start_date, end_date)
            return ScheduleResponse(events=events)
    except Exception as e:
        logger.error(f"Failed to get schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedule: {str(e)}")


@app.post("/schedule/add")
async def add_schedule(
    schedule: ScheduleResponse,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduleResponse:
    """Добавление события в расписание TODO"""
    # TODO: добавить валидацию данных
    logger.info(f"Добавление события в расписание: {schedule}")

    scheduler_service.add_event(schedule.events)
    return ScheduleResponse(events=[])


@app.get("/user/{telegram_id}")
async def get_user_profile(
    telegram_id: int,
    user_service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    """Получение профиля пользователя TODO"""
    user_profile = await user_service.get_user_profile(telegram_id)
    if user_profile is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserProfileResponse(user_profile=user_profile)


@app.post("/user/create")
async def create_user_profile(
    user_profile: UserProfile,
    user_service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    """Создание нового профиля пользователя"""
    logger.info(f"Создание профиля пользователя: {user_profile}")
    result = await user_service.create_user_profile(user_profile)
    return UserProfileResponse(user_profile=result)


@app.post("/user/update")
async def update_user_profile(
    update_request: UserProfileUpdateRequest,
    user_service: UserService = Depends(get_user_service),
) -> bool:
    """Обновление профиля пользователя с указанием полей для изменения"""
    logger.info(f"Обновление профиля пользователя: {update_request}")
    result = await user_service.update_user_profile(
        update_request.telegram_id, update_request
    )
    return result is not None


@app.post("/auth/telegram")
async def telegram_auth(
    request: Request,
    user_repository: UserRepository = Depends(container.user_repository),
) -> UserProfileResponse:
    """Аутентификация через Telegram Mini App"""
    try:
        data = await request.json()
        init_data = data.get("init_data")

        if not init_data:
            raise HTTPException(status_code=400, detail="init_data is required")

        if not BOT_TOKEN:
            raise HTTPException(status_code=500, detail="BOT_TOKEN не настроен")

        # Валидируем init_data с помощью BOT_TOKEN
        try:
            user_data = validate_telegram_init_data(init_data, BOT_TOKEN)
            telegram_id = user_data.get("id")

            if not telegram_id:
                raise HTTPException(status_code=400, detail="Telegram ID не найден")

        except ValueError as e:
            raise HTTPException(
                status_code=401, detail=f"Неверные данные аутентификации: {str(e)}"
            )

        # Проверяем, что пользователь существует в базе данных
        user_profile = user_repository.get_user_by_telegram_id(telegram_id)
        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден в базе данных. Обратитесь к администратору.",
            )

        logger.info(f"Telegram аутентификация успешна для пользователя {telegram_id}")
        return UserProfileResponse(user_profile=user_profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram auth failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Telegram auth failed: {str(e)}")


if __name__ == "__main__":
    print("Запустите приложение командой: python run.py")
