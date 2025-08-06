from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.repository.user import UserRepository
from app.service.user_service import UserService


class Container(containers.DeclarativeContainer):
    """Контейнер зависимостей"""

    # Конфигурация
    config = providers.Configuration()

    # База данных
    database_url = providers.Singleton(lambda: "sqlite+aiosqlite:///./zalupix.db")

    # Асинхронный движок SQLAlchemy
    engine = providers.Singleton(
        create_async_engine,
        database_url,
        echo=True,  # Логирование SQL запросов
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
    user_service = providers.Factory(
        UserService,
        repository=user_repository,
    )
