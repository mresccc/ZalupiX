import logging
from datetime import date
from typing import List, Optional

from aiocache import Cache, cached
from fastapi import HTTPException
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
    async def get_cached_events(self, start_date: date = None, end_date: date = None) -> List[Event]:
        """Получение событий с кэшированием"""
        events = await self._get_events_raw()
        return self._scheduler.filter_events(events, start_date, end_date)

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

    async def get_events(self, start_date: date = None, end_date: date = None) -> List[Event]:
        """Получение всех событий из Google Sheets"""
        return await self.get_cached_events(start_date, end_date)

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

    
    async def add_events(self, events: list[Event]) -> list[Event]:
        """Добавление событий с валидацией"""
        scheduler = self._get_scheduler()
        added_events = []

        for event in events:
            try:
                #Проверка конфликтов с существующими событиями
                if await self._has_conflict(event):
                    raise HTTPException(
                        status_code=409,
                        detail=f"Конфликт с существующим событием: {event.project} на {event.date}"
                    )
                
                #Добавляем событие через планировщик
                await scheduler.add_event(event)
                added_events.append(event)
                logger.info(f"Добавлено событие: {event.project} - {event.date} - {event.activity}")

            except HTTPException:
                raise

            except Exception as e:
                logger.error(f"Неожиданная ошибка при добавлении события {event}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Не удалось добавить событие: {str(e)}"
                )
        return added_events

    async def _has_conflict(self, event: Event) -> bool:
        """Проверка конфликтов с существующими событиями"""
        try:
            scheduler = self._get_scheduler()

            #Получаем все события на указанную дату
            existing_events = await scheduler.get_events_from_google_sheet(event.date)

            for existing_event in existing_events:
                #Проверяем только точное совпадение проекта, даты и активности
                if (existing_event.project == event.project and
                    existing_event.date == event.date and
                    existing_event.activity == event.activity):
                    logger.warning(f"Найден точный дубликат события: {event}")
                    return True
            return False
        
        except Exception as e:
            logger.error(f"Ошибка при проверке конфликтов для события {event}: {e}")
            # В случае ошибки считаем, что конфликтов нет
            return False
        
    async def get_events_for_period(self, start_date: date, end_date: date) -> List[Event]:
        """Получение событий за указанный период"""
        try:
            scheduler = self._get_scheduler()
            events = await scheduler.get_events_for_period(start_date, end_date)
            logger.info(f"Получено {len(events)} событий за период {start_date} - {end_date}")
            return events
        except Exception as e:
            logger.error(f"Ошибка при получении событий за период: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Не удалось получить события: {str(e)}"
            )
        
