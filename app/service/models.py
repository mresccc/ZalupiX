# service/models.py
from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import UserDriverLicenseEnum, UserPrinterEnum, UserStatusEnum


class Event(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    project: str = Field(
        description="Название проекта/активности", min_length=0, max_length=255
    )
    date: date_type = Field(description="Дата события")
    activity: str = Field(
        description="Описание активности", min_length=1, max_length=500
    )

    @field_validator("project", "activity")
    def allow_empty_project(cls, v):
        return v.strip()


class UserProfile(BaseModel):
    telegram_id: int = Field(description="Telegram ID")
    telegram_nickname: str = Field(description="Ник в ТГ")
    vk_nickname: str = Field(description="Ник в ВК")
    status: UserStatusEnum = Field(description="Статус")
    full_name: str = Field(description="ФИО")
    phone_number: str = Field(description="Номер телефона")
    live_metro_station: list[int] = Field(
        description="Станция метро, на которой ты живешь",
    )
    study_metro_station: list[int] = Field(
        description="Станция метро, на которой ты учишься/работаешь"
    )
    year_of_admission: int = Field(description="Год поступления в СтС")
    has_driver_license: UserDriverLicenseEnum = Field(
        description="Есть ли у тебя водительские права и/или машина?"
    )
    date_of_birth: date_type | None = Field(description="Дата Рождения")
    has_printer: UserPrinterEnum = Field(description="Если ли у тебя принтер?")
    can_host_night: bool = Field(
        description="Можем ли мы проводить ночь креатива/ночь оформления у тебя дома?"
    )

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, v):
        if v is None:
            return v
        
        # Если уже date объект, возвращаем как есть
        if isinstance(v, date_type):
            return v
        
        # Если строка, пытаемся парсить
        if isinstance(v, str):
            v = v.strip()
            
            # Пробуем формат DD.MM.YYYY
            try:
                return datetime.strptime(v, "%d.%m.%Y").date()
            except ValueError:
                pass
            
            # Пробуем формат YYYY-MM-DD
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                pass
            
            # Если ничего не подошло, возвращаем как есть (Pydantic выдаст ошибку)
            return v
        
        return v

    @property
    def course_number(self) -> int:
        return date_type.today().year - self.year_of_admission

    # last_update: datetime = Field(description="Время последнего обновления")


# UserProfileUpdateRequest теперь импортируется из schemas.py


class Activity(BaseModel):
    name: str
    events: list[Event] = []


class CalendarMonth(BaseModel):
    year: int
    month: int
    events: list[Event] = []
