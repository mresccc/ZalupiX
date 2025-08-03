from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field
from service.models import Event, UserProfile


class ScheduleResponse(BaseModel):
    """Схема ответа для эндпоинта /schedule"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "events": [
                    {
                        "project": "Школа Актива",
                        "date": "2025-01-15",
                        "activity": "Собрание по пиару",
                    }
                ]
            }
        }
    )

    events: list[Event] = Field(
        description="Список событий из Google Sheets", min_length=0
    )


class HealthResponse(BaseModel):
    """Схема ответа для эндпоинта /health"""

    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "healthy", "google_api": "connected"}}
    )

    status: str = Field(description="Статус API", pattern="^(healthy|unhealthy)$")
    google_api: str = Field(
        description="Статус подключения к Google API",
        pattern="^(connected|disconnected)$",
    )


class UserProfileResponse(BaseModel):
    """Схема ответа для эндпоинта /user_profile"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_profile": {
                    "telegram_id": 123456789,
                    "telegram_nickname": "ivan_ivanov",
                    "vk_nickname": "ivan_ivanovvv",
                    "status": 2,
                    "full_name": "Иван Иванов Иванович",
                    "phone_number": "+79991234567",
                    "live_metro_station": ["Одинцово", "Дубки"],
                    "study_metro_station": ["Чкаловская", "Курская", "Китай-город"],
                    "year_of_admission": 2024,
                    "has_driver_license": 0,
                    "date_of_birth": "2000-01-01",
                    "has_printer": 3,
                    "can_host_night": True,
                }
            }
        }
    )

    user_profile: UserProfile = Field(description="Профиль пользователя")


class UserProfileRequest(BaseModel):
    """Схема запроса для эндпоинта /user"""

    telegram_id: int = Field(description="Telegram ID")

class UserProfileUpdateRequest(BaseModel):
    """Схема запроса для частичного обновления профиля пользователя"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "telegram_id": 123456789,
                "from_user_telegram_id": 987654321,
                "fields": {
                    "full_name": "Новое ФИО",
                    "phone_number": "+79991234567",
                    "live_metro_station": ["Новая станция"],
                },
            }
        }
    )

    telegram_id: int = Field(description="Telegram ID пользователя для обновления")
    from_user_telegram_id: int = Field(
        description="Telegram ID пользователя, который делает запрос"
    )
    fields: Dict[str, Any] = Field(
        description="Словарь с полями для обновления", min_length=1
    )
