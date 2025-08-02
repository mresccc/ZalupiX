from datetime import datetime
from unittest.mock import Mock

from app.service.models import Event
from app.service.scheduler_service import (
    MockDataProvider,
    SchedulerService,
    create_mock_scheduler_service,
)


class TestSchedulerService:
    """Тесты для SchedulerService с использованием Dependency Injection"""

    def test_get_events_with_mock_provider(self):
        """Тест получения событий с mock провайдером"""
        # Arrange
        mock_events = [
            Event(
                title="Тестовое событие",
                date=datetime.now(),
                time="10:00",
                description="Описание события",
            )
        ]
        mock_provider = MockDataProvider(mock_events)
        service = SchedulerService(mock_provider)

        # Act
        result = service.get_events()

        # Assert
        assert result == mock_events
        assert len(result) == 1

    def test_is_connected_with_mock_provider(self):
        """Тест проверки подключения с mock провайдером"""
        # Arrange
        mock_provider = MockDataProvider()
        service = SchedulerService(mock_provider)

        # Act
        result = service.is_connected()

        # Assert
        assert result is True

    def test_is_connected_with_disconnected_provider(self):
        """Тест проверки подключения с отключенным провайдером"""
        # Arrange
        mock_provider = Mock()
        mock_provider.spreadsheet = None
        service = SchedulerService(mock_provider)

        # Act
        result = service.is_connected()

        # Assert
        assert result is False

    def test_refresh_events(self):
        """Тест обновления событий"""
        # Arrange
        mock_events = [Event(title="Событие", date=datetime.now(), time="12:00")]
        mock_provider = MockDataProvider(mock_events)
        service = SchedulerService(mock_provider)

        # Act
        result = service.refresh_events()

        # Assert
        assert result == mock_events


class TestMockDataProvider:
    """Тесты для MockDataProvider"""

    def test_mock_provider_returns_events(self):
        """Тест что mock провайдер возвращает события"""
        # Arrange
        events = [Event(title="Тест", date=datetime.now(), time="15:00")]
        provider = MockDataProvider(events)

        # Act
        result = provider.get_events_from_google_sheet()

        # Assert
        assert result == events

    def test_mock_provider_has_spreadsheet_property(self):
        """Тест что mock провайдер имеет свойство spreadsheet"""
        # Arrange
        provider = MockDataProvider()

        # Act & Assert
        assert provider.spreadsheet is True


class TestFactoryFunctions:
    """Тесты для фабричных функций"""

    def test_create_mock_scheduler_service(self):
        """Тест создания сервиса с mock данными"""
        # Arrange
        events = [Event(title="Фабрика", date=datetime.now(), time="20:00")]

        # Act
        service = create_mock_scheduler_service(events)

        # Assert
        assert isinstance(service, SchedulerService)
        assert service.get_events() == events
