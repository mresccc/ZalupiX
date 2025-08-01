import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from service.google_data import init_scheduler
from service.models import Event

from config import GRID_CREDENTIALS_PATH, SPREADSHEET_URL
# Импортируем вашего бота и функцию уведомления из bot.py
from bot import dp, bot, notify_admins

# Конфигурация
scheduler = init_scheduler(SPREADSHEET_URL, GRID_CREDENTIALS_PATH)

# --- FASTAPI APP ---
app = FastAPI(title="Google Sheets Events API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return "Hello"

@app.get("/schedule", response_model=List[Event])
async def get_schedule():
    events = scheduler.get_events_from_google_sheet()
    return events

# --- ФУНКЦИЯ ЗАПУСКА FASTAPI через uvicorn в asyncio ---
async def start_api():
    import uvicorn
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

# --- ОСНОВНОЙ ЛАНЧЕР: запуск бота и API параллельно ---
async def main():
    # Отправляем уведомление администратору
    await notify_admins("🤖 Бот и API сервер запущены!")
    # Стартуем оба процесса параллельно: API и Telegram-бот
    await asyncio.gather(
        start_api(),
        dp.start_polling(bot)
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
