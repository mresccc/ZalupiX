import os
from typing import List

from dotenv import load_dotenv

# CORS настройки
CORS_ORIGINS: List[str] = [
    "http://localhost:8001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Telegram Mini App домены
    "https://web.telegram.org",
    "https://t.me",
    "https://telegram.org",
]

# Добавляем production домены из переменных окружения
if os.getenv("PRODUCTION_DOMAIN"):
    CORS_ORIGINS.extend(
        [
            f"https://{os.getenv('PRODUCTION_DOMAIN')}",
            f"http://{os.getenv('PRODUCTION_DOMAIN')}",
        ]
    )

# Настройки сервера
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8001"))
RELOAD = os.getenv("RELOAD", "True").lower() == "true"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Загружаем переменные окружения
load_dotenv()


class Settings:
    TG_TOKEN: str = os.getenv("TG_TOKEN", "")
    WEB_URL: str = os.getenv("WEB_URL", "https://localhost:8001")
    ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./zalupix.db")

    def webhook(self) -> str:
        return f"{self.WEB_URL}/webhook"


settings = Settings()


"""
Конфигурация rim_bot - централизованное управление константами и настройками
"""

# === ФАЙЛЫ И ПУТИ ===
CREDS_FILE = "credentials.json"
GRID_CREDENTIALS_PATH = "credentials.json"

# Пути к данным
DATA_DIR = os.getenv("DATA_DIR", "app/data")
METRO_DATA_FILE = os.getenv("METRO_DATA_FILE", "metro_grouped.json")
DATABASE_FILE = os.getenv("DATABASE_FILE", "zalupix.db")

# Полные пути
METRO_DATA_PATH = os.path.join(DATA_DIR, METRO_DATA_FILE)
DATABASE_PATH = os.path.join(DATA_DIR, DATABASE_FILE)

# === ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===
CALENDAR_URL = os.getenv("CALENDAR_URL")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
# BOT_USERNAME = os.getenv("BOT_USERNAME")
# DATABASE_URL = os.getenv("DATABASE_URL", "rim.db")
# PORT = os.getenv("PORT", "8080")

# === НАСТРОЙКИ КАЛЕНДАРЯ ===
WORKSHEET_NAME = "календарь new"
CACHE_DURATION_HOURS = 1  # Время жизни кеша в часах

# === СООТВЕТСТВИЕ РУССКИХ МЕСЯЦЕВ ЧИСЛАМ ===
MONTHS = {
    "ЯНВАРЬ": 1,
    "ФЕВРАЛЬ": 2,
    "МАРТ": 3,
    "АПРЕЛЬ": 4,
    "МАЙ": 5,
    "ИЮНЬ": 6,
    "ИЮЛЬ": 7,
    "АВГУСТ": 8,
    "СЕНТЯБРЬ": 9,
    "ОКТЯБРЬ": 10,
    "НОЯБРЬ": 11,
    "ДЕКАБРЬ": 12,
}

# === НАЗВАНИЯ ДНЕЙ НЕДЕЛИ ===
WEEKDAYS = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье",
}

# === НАЗВАНИЯ МЕСЯЦЕВ В РОДИТЕЛЬНОМ ПАДЕЖЕ ===
MONTH_NAMES = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

# === НАЗВАНИЯ ДНЕЙ НЕДЕЛИ В CSV ===
DAY_COLUMNS = [
    "ПОНЕДЕЛЬНИК",
    "ВТОРНИК",
    "СРЕДА",
    "ЧЕТВЕРГ",
    "ПЯТНИЦА",
    "СУББОТА ",
    "ВОСКРЕСЕНЬЕ",
]
