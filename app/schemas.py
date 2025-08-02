from pydantic import BaseModel, ConfigDict, Field
from service.models import Event


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
