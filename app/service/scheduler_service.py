import logging
from typing import List, Optional

from aiocache import Cache, cached
from config import GRID_CREDENTIALS_PATH, SPREADSHEET_URL

from service.google_data import GridScheduler, init_scheduler
from service.models import Event

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализируем кэш
cache = Cache(Cache.MEMORY)


class SchedulerServiceError(Exception):
    """Исключение для ошибок сервиса планировщика"""

    pass


class SchedulerService:
    """Сервисный слой для работы с расписанием событий"""

    def __init__(self):
        self._scheduler: Optional[GridScheduler] = None

    def _get_scheduler(self) -> GridScheduler:
        """Получение экземпляра планировщика (ленивая инициализация)"""
        if self._scheduler is None:
            logger.info("Инициализация планировщика...")
            self._scheduler = init_scheduler(SPREADSHEET_URL, GRID_CREDENTIALS_PATH)
            if not self._scheduler:
                logger.error("Не удалось инициализировать планировщик")
                raise SchedulerServiceError("Failed to initialize scheduler")
            logger.info("Планировщик успешно инициализирован")
        return self._scheduler

    @cached(ttl=600, cache=Cache.MEMORY)
    async def get_cached_events(self) -> List[Event]:
        """Получение событий с кэшированием"""
        return await self._get_events_raw()

    async def _get_events_raw(self) -> List[Event]:
        """Получение событий без кэширования (внутренний метод)"""
        try:
            scheduler = self._get_scheduler()
            events = await scheduler.get_events_from_google_sheet()
            logger.info(f"Получено {len(events)} событий")
            return events
        except Exception as e:
            logger.error(f"Ошибка при получении событий: {str(e)}")
            raise

    async def get_events(self) -> List[Event]:
        """Получение всех событий из Google Sheets"""
        return await self.get_cached_events()

    def is_connected(self) -> bool:
        """Проверка подключения к Google Sheets"""
        try:
            scheduler = self._get_scheduler()
            return scheduler.spreadsheet is not None
        except Exception:
            return False

    async def refresh_events(self) -> List[Event]:
        """Принудительное обновление событий с очисткой кэша"""
        logger.info("Принудительное обновление событий")
        await cache.clear()
        return await self._get_events_raw()
