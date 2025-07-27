import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiogram.types import Update

from bot import bot, dp, notify_admins
from config import settings

logging.basicConfig(level=logging.INFO)
templates = Jinja2Templates(directory="web")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await notify_admins("✅ Бот запущен")
    await bot.set_webhook(
        url=settings.webhook(),
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True
    )
    yield
    await bot.delete_webhook()
    await notify_admins("🛑 Бот остановлен")

app = FastAPI(title="MiniApp", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(r: Request):
    return templates.TemplateResponse("index.html", {"request": r})

@app.post("/webhook")
async def telegram_webhook(r: Request):
    print('Хуй хуй')
    u = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, u)
