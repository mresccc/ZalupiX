from fastapi import FastAPI
from service.google_data import init_scheduler
from fastapi.middleware.cors import CORSMiddleware
from config import GRID_CREDENTIALS_PATH

from typing import List
from service.models import Event
scheduler = init_scheduler('https://docs.google.com/spreadsheets/d/1c00-wZ_ocej9VqEx6rKLK3H1ojNHvKDSD4KEZarAmWw/edit?gid=984591375#gid=984591375', GRID_CREDENTIALS_PATH)

app = FastAPI(title="Google Sheets Events API")

# Разрешить CORS если надо
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или список разрешённых доменов
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
    print(events)
    return events
