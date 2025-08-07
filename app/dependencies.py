from dependency_injector import containers, providers
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import DATABASE_PATH
from app.repository.user import UserRepository
from app.service.metro_service import MetroService
from app.service.scheduler_service import SchedulerService
from app.service.user_service import UserService


class Container(containers.DeclarativeContainer):
    """Контейнер зависимостей"""

    # Конфигурация
    config = providers.Configuration()

    # База данных
    database_url = providers.Singleton(lambda: f"sqlite+aiosqlite:///{DATABASE_PATH}")

    # Асинхронный движок SQLAlchemy
    engine = providers.Singleton(
        create_async_engine,
        database_url,
        echo=False,  # Отключаем логирование SQL запросов
        future=True,
    )

    # Фабрика сессий
    session_factory = providers.Singleton(
        async_sessionmaker,
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Репозиторий пользователя
    user_repository = providers.Factory(
        UserRepository,
        db=providers.Dependency(),
    )

    # Сервис пользователя
    user_service = providers.Singleton(
        UserService,
        repository=user_repository,
    )

    # Сервис планировщика
    scheduler_service = providers.Singleton(SchedulerService)

    # Сервис метро
    metro_service = providers.Singleton(MetroService)


# Создаем экземпляр контейнера
container = Container()


async def get_db_session() -> AsyncSession:
    """Dependency для получения сессии БД"""
    session_factory = container.session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_scheduler_service() -> SchedulerService:
    """Dependency для получения сервиса планировщика"""
    return container.scheduler_service()


def get_user_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Dependency для получения репозитория пользователя"""
    return UserRepository(db_session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Dependency для получения сервиса пользователя"""
    return UserService(repository)


def get_metro_service() -> MetroService:
    """Dependency для получения сервиса метро"""
    return container.metro_service()
