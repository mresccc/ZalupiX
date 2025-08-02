import asyncio
import logging

from app import app
from bot import bot, dp, notify_admins


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
    await asyncio.gather(start_api(), dp.start_polling(bot))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
