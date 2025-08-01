# service/models.py
from pydantic import BaseModel
from datetime import date

class Event(BaseModel):
    activity: str
    date: date
    text: str

class Activity(BaseModel):
    name: str
    events: list[Event] = []

class CalendarMonth(BaseModel):
    year: int
    month: int
    events: list[Event] = []
