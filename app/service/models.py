# service/models.py
from datetime import date as date_type

from pydantic import BaseModel, ConfigDict, Field


class Event(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    project: str = Field(description="Название проекта/активности")
    date: date_type = Field(description="Дата события")
    activity: str = Field(description="Описание активности")


class Activity(BaseModel):
    name: str
    events: list[Event] = []


class CalendarMonth(BaseModel):
    year: int
    month: int
    events: list[Event] = []
