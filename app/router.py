from datetime import date
from typing import Any, Dict, List, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.config import BOT_TOKEN
from app.dependencies import (
    get_metro_service,
    get_scheduler_service,
    get_user_repository,
    get_user_service,
)
from app.metro import MetroLine
from app.repository.user import UserRepository
from app.schemas import (
    HealthResponse,
    ScheduleResponse,
    TelegramAuthRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from app.service.metro_service import MetroService
from app.service.models import UserProfile
from app.service.scheduler_service import SchedulerService
from app.service.user_service import UserService
from app.utils import (
    parse_telegram_data_without_validation,
    validate_telegram_init_data,
)

router = APIRouter()


@router.get("/health")
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


@router.get("/schedule")
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


@router.post("/schedule/add")
async def add_schedule(
    schedule: ScheduleResponse,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduleResponse:
    """Добавление события в расписание TODO"""
    # TODO: добавить валидацию данных
    logger.info(f"Добавление события в расписание: {schedule}")

    scheduler_service.add_event(schedule.events)
    return ScheduleResponse(events=[])


@router.get("/user/{telegram_id}")
async def get_user_profile(
    telegram_id: int,
    user_service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    """Получение профиля пользователя TODO"""
    user_profile = await user_service.get_user_profile(telegram_id)
    if user_profile is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserProfileResponse(user_profile=user_profile)


@router.post("/user/create")
async def create_user_profile(
    user_profile: UserProfile,
    user_service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    """Создание нового профиля пользователя"""
    logger.info(f"Создание профиля пользователя: {user_profile}")
    result = await user_service.create_user_profile(user_profile)
    return UserProfileResponse(user_profile=result)


@router.post("/user/update")
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


@router.post("/auth/telegram")
async def telegram_auth(
    auth_request: TelegramAuthRequest,
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserProfileResponse:
    """Аутентификация через Telegram Mini App"""
    try:
        # Проверяем наличие BOT_TOKEN
        if not BOT_TOKEN:
            logger.warning("BOT_TOKEN не настроен, пропускаем валидацию hash")
            # Парсим данные без валидации
            try:
                user_data = parse_telegram_data_without_validation(
                    auth_request.init_data
                )
                telegram_id = user_data.get("id")

                if not telegram_id:
                    raise HTTPException(status_code=400, detail="Telegram ID не найден")

            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Ошибка парсинга данных: {str(e)}"
                )
        else:
            # Валидируем init_data с помощью BOT_TOKEN
            try:
                user_data = validate_telegram_init_data(
                    auth_request.init_data, BOT_TOKEN
                )
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


@router.get("/metro")
async def get_metro(
    language: str = Query(
        default="ru",
        description="Язык для названий (ru, en, cn, all)",
        pattern="^(ru|en|cn|all)$",
    ),
    include_location: bool = Query(
        default=True,
        description="Включать ли координаты станций",
    ),
    use_numeric_keys: bool = Query(
        default=False,
        description="Использовать числовые ключи вместо строковых",
    ),
    metro_service: MetroService = Depends(get_metro_service),
) -> Union[List[MetroLine], List[Dict[str, Any]]]:
    """Получение данных о метро с настройками сериализации"""
    if use_numeric_keys:
        return metro_service.get_optimized_metro_data(
            language=language,
            include_location=include_location,
        )
    else:
        return metro_service.get_metro(
            language=language,
            include_location=include_location,
        )
