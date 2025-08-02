import os
import sys
from datetime import datetime
from pathlib import Path

import gspread
from config import GRID_CREDENTIALS_PATH, MONTHS

from .models import Event

# Добавляем родительскую директорию в sys.path если её нет
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

scheduler = None
spreadsheet_url = None
credentials_path = GRID_CREDENTIALS_PATH


class GridScheduler:
    """Класс для работы с расписанием событий через Google Sheets"""

    def __init__(self, spreadsheet_url: str = None, credentials_path: str = None):
        """
        Инициализация подключения к Google Sheets

        Args:
            spreadsheet_url: URL Google таблицы
            credentials_path: Путь к JSON файлу с credentials
        """
        self.spreadsheet_url = spreadsheet_url
        # Если путь к credentials не абсолютный, ищем в корне проекта
        if credentials_path and os.path.isabs(credentials_path):
            self.credentials_path = credentials_path
        else:
            # Ищем в корне проекта (родительская директория от service/)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.credentials_path = os.path.join(
                project_root, credentials_path or "credentials.json"
            )
        print(self.credentials_path)
        self.gc = None
        self.spreadsheet = None

    def connect(self) -> bool:
        """Подключение к Google Sheets"""
        if not self.spreadsheet_url:
            print("Ошибка: не указан URL таблицы")
            return False

        try:
            print("Попытка подключения к Google Sheets...")
            print(f"URL: {self.spreadsheet_url}")
            print(f"Credentials path: {self.credentials_path}")

            if os.path.exists(self.credentials_path):
                print(f"Используем файл credentials: {self.credentials_path}")
                self.gc = gspread.service_account(filename=self.credentials_path)
            else:
                print("Файл credentials не найден, используем переменные окружения")
                # Попробуем использовать переменные окружения
                self.gc = gspread.service_account()

            self.spreadsheet = self.gc.open_by_url(self.spreadsheet_url)
            print(f"Успешно подключились к Google Sheets {self.spreadsheet.title}")
            return True

        except Exception as e:
            print(f"Ошибка подключения к Google Sheets: {e}")
            return False

    async def get_events_from_google_sheet(self) -> list:
        import re

        # Подключаемся к Google Sheets если еще не подключены
        if not self.spreadsheet:
            if not self.connect():
                raise Exception("Не удалось подключиться к Google Sheets")

        if self.spreadsheet:
            worksheet = self.spreadsheet.worksheet("календарь new")
            data = worksheet.get_all_values()

            YEAR = datetime.now().year

            events = []
            i = 0
            while i < len(data):
                row = data[i]
                # Поиск начала месяца
                month = None
                for key in MONTHS:
                    if key in row:
                        month = MONTHS[key]
                        break
                if not month:
                    i += 1
                    continue

                # days_row (i+2): строка с числами дней (например: ['', '27', '28', ...])
                days_row = data[i + 2] if len(data) > i + 2 else []
                # Находим используемые дневные столбцы (там, где действительно есть число)
                day_columns = []
                for col, val in enumerate(days_row):
                    if re.fullmatch(r"\d+", val.strip()):
                        day_columns.append(col)
                # Список дат для этих столбцов
                dates = []
                for col in day_columns:
                    day = days_row[col].strip()
                    if day:
                        date = f"{YEAR}-{month}-{int(day):02d}"
                        dates.append((col, date))

                # Проходим по активности, пока не встретим новый месяц или не дойдём до конца
                j = i + 3
                while j < len(data):
                    act_row = data[j]
                    if any(m in act_row for m in MONTHS):
                        break
                    activity = act_row[0].strip()
                    if not activity:
                        j += 1
                        continue
                    for col, date in dates:
                        text = act_row[col].strip()
                        if text:
                            event = Event(
                                project=activity,
                                date=datetime.strptime(date, "%Y-%m-%d").date(),
                                activity=text,
                            )
                            events.append(event)
                    j += 1
                i = j  # Перепрыгиваем к следующему блоку месяца
            return events


def init_scheduler(spreadsheet_url: str = None, credentials_path: str = None):
    """Инициализация планировщика"""
    global scheduler
    scheduler = GridScheduler(
        spreadsheet_url=spreadsheet_url, credentials_path=credentials_path
    )
    scheduler.connect()
    return scheduler


if __name__ == "__main__":
    scheduler = init_scheduler(
        spreadsheet_url=os.getenv("SPREADSHEET_URL"),
        credentials_path=GRID_CREDENTIALS_PATH,
    )
    scheduler.connect()

    print(scheduler.get_info())
