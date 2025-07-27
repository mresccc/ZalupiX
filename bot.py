import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
)
from config import settings

bot = Bot(
    token=settings.TG_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
router = Router()

@router.message(CommandStart())
async def start_cmd(m: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="🚀 Открыть Mini App",
                web_app=WebAppInfo(url=settings.WEB_URL)
            )]
        ],
        resize_keyboard=True
    )
    await m.answer(
        "<b>Привет!</b> Жми кнопку – откроется Mini App.",
        reply_markup=kb
    )

@router.message(F.web_app_data)
async def handle_web_app_data(m: Message):
    await m.answer(f"⛳ Получены данные из Mini App: <code>{m.web_app_data.data}</code>")

dp.include_router(router)

async def   notify_admins(text: str):
    for admin in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin, text)
        except Exception:
            pass
