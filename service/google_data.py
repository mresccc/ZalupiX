import gspread
import pandas as pd
from datetime import datetime, time
from typing import Dict, List, Optional
import os
import sys
from pathlib import Path

from .models import Event
# Добавляем родительскую директорию в sys.path если её нет
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from config import GRID_CREDENTIALS_PATH, MONTHS

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
        # Если путь к credentials не абсолютный, ищем рядом со скриптом
        if credentials_path and os.path.isabs(credentials_path):
            self.credentials_path = credentials_path
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.credentials_path = os.path.join(script_dir, credentials_path or "../credentials.json")
        print(self.credentials_path)
        self.gc = None
        self.spreadsheet = None
        # Список дней недели по умолчанию (будет обновлен после подключения)
        # self.days = DEFAULT_GRID_DAYS.copy()
        
        # Названия дней недели для поиска в названиях листов
        # self.weekday_names = WEEKDAY_NAMES
        # Подключаемся только если есть URL и credentials файл существует
        # if self.spreadsheet_url and os.path.exists(self.credentials_path):
        #     if self.connect():
        #         # Обновляем список дней из названий листов
        #         self.days = self._get_days_from_sheets()
        


    

    def connect(self) -> bool:
        """Подключение к Google Sheets"""
        if not self.spreadsheet_url:
            return False
            
        try:
            if os.path.exists(self.credentials_path):
                self.gc = gspread.service_account(filename=self.credentials_path)
            else:
                # Попробуем использовать переменные окружения
                self.gc = gspread.service_account()
                
            self.spreadsheet = self.gc.open_by_url(self.spreadsheet_url)
            print(f"Успешно подключились к Google Sheets {self.spreadsheet.title}")
            return True
            
        except Exception as e:
            print(f"Ошибка подключения к Google Sheets: {e}")
            return False
    
    
    def get_events_from_google_sheet(self) -> list:
        import re

        # self.connect()
        if self.spreadsheet:
            # --- 1. Получение всех данных ---
            worksheet = self.spreadsheet.worksheet('календарь new')
            data = worksheet.get_all_values()
            
            # --- 2. Поиск строки начала нужного блока ("ИЮЛЬ") ---
            # 1. Найти строку, где начинается календарная сетка (ищем "ША" в диапазоне строк)
            import gspread
            import re

            
            data = worksheet.get_all_values()

            # --- 2. Справочник месяцев ---
            month_map = {
                'ЯНВАРЬ': '01',
                'ФЕВРАЛЬ': '02',
                'МАРТ': '03',
                'АПРЕЛЬ': '04',
                'МАЙ': '05',
                'ИЮНЬ': '06',
                'ИЮЛЬ': '07',
                'АВГУСТ': '08',
                'СЕНТЯБРЬ': '09',
                'ОКТЯБРЬ': '10',
                'НОЯБРЬ': '11',
                'ДЕКАБРЬ': '12'
            }

            YEAR = "2025"  # Укажите нужный год!

            raw_events = []
            events = []
            i = 0
            while i < len(data):
                row = data[i]
                # Поиск начала месяца
                month = None
                for key in month_map:
                    if key in row:
                        month = month_map[key]
                        break
                if not month:
                    i += 1
                    continue

                # days_row (i+2): строка с числами дней (например: ['', '27', '28', ...])
                days_row = data[i+2] if len(data) > i+2 else []
                # Находим используемые дневные столбцы (там, где действительно есть число)
                day_columns = []
                for col, val in enumerate(days_row):
                    if re.fullmatch(r'\d+', val.strip()):
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
                    if any(m in act_row for m in month_map):
                        break
                    activity = act_row[0].strip()
                    if not activity:
                        j += 1
                        continue
                    for col, date in dates:
                        text = act_row[col].strip()
                        if text:
                            raw_events.append({
                                'activity': activity,
                                'date': date,
                                'text': text
                            })
                    j += 1
                i = j  # Перепрыгиваем к следующему блоку месяца

            # --- 3. ПРОВЕРКА: выводим все события ---
            for raw_event in raw_events:
                event = Event(
                    activity=raw_event['activity'],
                    date = datetime.strptime(raw_event['date'], "%Y-%m-%d").date(),
                    text = raw_event['text']

                )
                events.append(event)
            return events


def init_scheduler(spreadsheet_url: str = None, credentials_path: str = None):
    """Инициализация планировщика"""
    global scheduler
    scheduler = GridScheduler(
        spreadsheet_url=spreadsheet_url,
        credentials_path=credentials_path
    )
    scheduler.connect()
    return scheduler


if __name__ == "__main__":
    scheduler = init_scheduler(
        spreadsheet_url=os.getenv("SPREADSHEET_URL"),
        credentials_path=GRID_CREDENTIALS_PATH
    )
    scheduler.connect()

    print(scheduler.get_info())
