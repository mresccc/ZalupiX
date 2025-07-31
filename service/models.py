# service/models.py
from pydantic import BaseModel
from datetime import date
from typing import List

class Event(BaseModel):
    activity: str
    date: date
    text: str

class Activity(BaseModel):
    name: str
    events: List[Event] = []

class CalendarMonth(BaseModel):
    year: int
    month: int
    events: List[Event] = []
