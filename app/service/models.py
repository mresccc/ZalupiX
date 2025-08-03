# service/models.py
from datetime import date as date_type
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class UserStatus(Enum):
    INACTIVE = 0
    WORK = 1
    ACTIVE = 2
    GRADUATED = 3


class UserDriverLicense(Enum):
    NO = 0
    YES = 1
    YES_AND_CAR = 2


class UserPrinter(Enum):
    NO = 0
    BLACK = 1
    COLOR = 2
    BLACK_AND_COLOR = 3


class UserProfile(BaseModel):
    telegram_id: int = Field(description="Telegram ID")
    telegram_nickname: str = Field(description="Ник в ТГ")
    vk_nickname: str = Field(description="Ник в ВК")
    status: UserStatus = Field(description="Статус")
    full_name: str = Field(description="ФИО")
    phone_number: str = Field(description="Номер телефона")
    live_metro_station: list[str] = Field(
        description="Станция метро, на которой ты живешь"
    )
    study_metro_station: list[str] = Field(
        description="Станция метро, на которой ты учишься/работаешь"
    )
    year_of_admission: int = Field(description="Год поступления в СтС")
    has_driver_license: UserDriverLicense = Field(
        description="Есть ли у тебя водительские права и/или машина?"
    )
    date_of_birth: date_type = Field(description="Дата Рождения")
    has_printer: bool = Field(description="Если ли у тебя принтер?")
    can_host_night: bool = Field(
        description="Можем ли мы проводить ночь креатива/ночь оформления у тебя дома?"
    )

    @property
    def course_number(self) -> int:
        return date_type.today().year - self.year_of_admission

    # last_update: datetime = Field(description="Время последнего обновления")


class Activity(BaseModel):
    name: str
    events: list[Event] = []


class CalendarMonth(BaseModel):
    year: int
    month: int
    events: list[Event] = []
