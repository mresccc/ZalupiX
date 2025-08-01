from fastapi import FastAPI, Request
from service.google_data import init_scheduler
from fastapi.middleware.cors import CORSMiddleware
from config import GRID_CREDENTIALS_PATH, SPREADSHEET_URL
from aiogram.types import Update

from bot import bot, dp
from typing import List
from service.models import Event
scheduler = init_scheduler(SPREADSHEET_URL, GRID_CREDENTIALS_PATH)

app = FastAPI(title="Google Sheets Events API")

# Разрешить CORS если надо
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", 'http://localhost:3000'],  # или список разрешённых доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_events():
    return 'Hello'


@app.get("/schedule", response_model=List[Event])
async def read_events():

    events = scheduler.get_events_from_google_sheet()
    
    return events

