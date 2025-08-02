from fastapi import FastAPI, Request
from service.google_data import init_scheduler
from fastapi.middleware.cors import CORSMiddleware
from config import GRID_CREDENTIALS_PATH, SPREADSHEET_URL

from service.models import Event
scheduler = init_scheduler(SPREADSHEET_URL, GRID_CREDENTIALS_PATH)

app = FastAPI(
    title="Google Sheets Events API"
)

# Разрешить CORS если надо
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", 'http://localhost:3000'],  # или список разрешённых доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def index():
    return 'health'


@app.get("/schedule", response_model=list[Event])
async def read_events():
    return scheduler.get_events_from_google_sheet()
