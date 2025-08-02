from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from config import GRID_CREDENTIALS_PATH, SPREADSHEET_URL
from service.google_data import init_scheduler
from service.models import Event

scheduler = init_scheduler(SPREADSHEET_URL, GRID_CREDENTIALS_PATH)

app = FastAPI(
    title="Google Sheets Events API",
    # ORJSON для более быстрой работы с json
    default_response_class=ORJSONResponse
)


# Разрешить CORS если надо
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def index():
    # TODO: проверять доступность google api
    return "health"


@app.get("/schedule", response_model=list[Event])
async def read_events():
    return scheduler.get_events_from_google_sheet()
