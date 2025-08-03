import os
import sys
from datetime import date
from pathlib import Path

import gspread
import polars as pl
from config import GRID_CREDENTIALS_PATH, MONTHS
from gspread import Client, Spreadsheet

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
        self.gc: Client | None = None
        self.spreadsheet: Spreadsheet | None = None

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

    async def get_events_from_google_sheet(self) -> list[Event]:
        """Получает все события из Google Sheets"""
        # Подключаемся к Google Sheets если еще не подключены
        if not self.spreadsheet:
            if not self.connect():
                raise Exception("Не удалось подключиться к Google Sheets")

        if self.spreadsheet:
            worksheet = self.spreadsheet.worksheet("календарь new")
            data = worksheet.get_all_values(combine_merged_cells=True)
            headers = data[3] if len(data) > 3 else []
            # Берем данные начиная с 4-й строки (пропускаем заголовки)
            rows = data[2:] if len(data) > 2 else []

            return self.parse_calendar(pl.DataFrame(rows, schema=headers))

    def filter_events(
        self, events: list[Event], start_date: date = None, end_date: date = None
    ) -> list[Event]:
        """Фильтрует события по датам

        Args:
            events: Список событий для фильтрации
            start_date: Начальная дата для фильтрации (включительно)
            end_date: Конечная дата для фильтрации (включительно)

        Returns:
            Отфильтрованный список событий
        """
        if start_date and end_date:
            # Если указаны обе даты, используем диапазон
            return [event for event in events if start_date <= event.date <= end_date]
        elif start_date:
            # Если указана только начальная дата
            return [event for event in events if event.date >= start_date]
        elif end_date:
            # Если указана только конечная дата
            return [event for event in events if event.date <= end_date]
        else:
            # Если не указаны даты, возвращаем все события
            return events

    async def get_filtered_events(
        self, start_date: date = None, end_date: date = None
    ) -> list[Event]:
        """Получает и фильтрует события из Google Sheets

        Args:
            start_date: Начальная дата для фильтрации (включительно)
            end_date: Конечная дата для фильтрации (включительно)

        Returns:
            Отфильтрованный список событий
        """
        events = await self.get_events_from_google_sheet()
        return self.filter_events(events, start_date=start_date, end_date=end_date)

    def parse_calendar(self, data: pl.DataFrame) -> list[Event]:
        """Парсит календарь из DataFrame и возвращает список событий

        Args:
            data: DataFrame с данными календаря
        """
        events = []
        current_year = 2025

        # Получаем все строки как список для итерации
        rows = list(data.iter_rows())

        i = 0
        while i < len(rows):
            row = rows[i]

            # Проверяем, является ли строка месяцем
            if row and row[0] in MONTHS:
                current_month = MONTHS[row[0]]
                i += 1

                # Обрабатываем блок месяца
                while i < len(rows):
                    current_row = rows[i]

                    # Если встретили следующий месяц, прекращаем
                    if current_row and current_row[0] in MONTHS:
                        break

                    # Ищем строку с датами
                    if current_row and self._has_dates_df(current_row[1:]):
                        dates_row = current_row
                        i += 1

                        # Собираем строки проектов для этой недели
                        project_rows = []
                        while i < len(rows):
                            project_row = rows[i]

                            # Если встретили месяц или строку с датами, прекращаем
                            if (
                                project_row and project_row[0] in MONTHS
                            ) or self._has_dates_df(project_row[1:]):
                                break

                            project_rows.append(project_row)
                            i += 1

                        # Обрабатываем неделю с дедупликацией
                        week_events = self._process_week_events_df(
                            project_rows, dates_row, current_month, current_year
                        )
                        events.extend(week_events)
                    else:
                        i += 1
            else:
                i += 1

        # Сортируем события по дате
        events.sort(key=lambda x: x.date)
        return events

    def _process_week_events_df(
        self, project_rows, dates_row, month, year
    ) -> list[Event]:
        """Обрабатывает события недели с дедупликацией вертикальных событий (DataFrame версия)"""
        events = []
        vertical_events_seen = set()  # (дата, активность)

        # Сначала определяем вертикальные события для всей недели
        vertical_activities = self._find_vertical_activities(project_rows, dates_row)

        for project_row in project_rows:
            project_name = (
                str(project_row[0]).strip() if project_row[0] is not None else ""
            )

            if project_name:
                for day_idx in range(1, min(len(project_row), len(dates_row))):
                    date_str = (
                        str(dates_row[day_idx]).strip()
                        if dates_row[day_idx] is not None
                        else ""
                    )
                    activity = (
                        str(project_row[day_idx]).strip()
                        if project_row[day_idx] is not None
                        else ""
                    )

                    if date_str and activity and date_str.isdigit():
                        try:
                            event_date = date(year, month, int(date_str))

                            # Проверяем, является ли это вертикальным событием
                            if activity in vertical_activities:
                                # Для вертикальных событий проверяем дедупликацию
                                key = (event_date, activity)
                                if key not in vertical_events_seen:
                                    vertical_events_seen.add(key)
                                    events.append(
                                        Event(
                                            project="",
                                            date=event_date,
                                            activity=activity,
                                        )
                                    )
                            else:
                                # Обычные события добавляем как есть
                                events.append(
                                    Event(
                                        project=project_name,
                                        date=event_date,
                                        activity=activity,
                                    )
                                )
                        except ValueError:
                            continue

        return events

    def _find_vertical_activities(self, project_rows, dates_row) -> set[str]:
        """Находит вертикальные активности (повторяющиеся во всех проектах)"""
        vertical_activities = set()

        # Для каждой колонки проверяем, повторяется ли активность во всех проектах
        for day_idx in range(1, min(len(dates_row), 8)):  # максимум 7 дней недели
            activities_in_column = []
            non_empty_projects = 0

            for project_row in project_rows:
                if day_idx < len(project_row):
                    activity = (
                        str(project_row[day_idx]).strip()
                        if project_row[day_idx] is not None
                        else ""
                    )
                    activities_in_column.append(activity)
                    if activity:
                        non_empty_projects += 1

            # Проверяем, что активность повторяется во всех непустых проектах
            if non_empty_projects > 1:  # Должно быть минимум 2 проекта с активностью
                unique_activities = set(activities_in_column) - {""}
                if len(unique_activities) == 1:  # Только одна уникальная активность
                    vertical_activities.update(unique_activities)

        return vertical_activities

    def _has_dates_df(self, row_slice) -> bool:
        """Проверяет есть ли числовые даты в строке DataFrame"""
        return any(
            str(cell).strip().isdigit() for cell in row_slice if cell is not None
        )

    def _is_vertical_event_df(self, row) -> bool:
        """Проверяет вертикальные события (занимающие всю неделю) - DataFrame версия"""
        for col_idx in range(1, len(row)):
            activity = str(row[col_idx]).strip() if row[col_idx] is not None else ""
            if activity and len(activity) > 3:
                same_events = sum(
                    1
                    for i in range(col_idx, len(row))
                    if i < len(row) and str(row[i]).strip() == activity
                )
                if same_events >= 3:
                    return True
        return False

    def parse_csv_file(self, csv_path: str) -> list[Event]:
        """Парсит календарь из CSV файла и возвращает список событий

        Args:
            csv_path: Путь к CSV файлу

        Returns:
            Список событий
        """
        df = pl.read_csv(csv_path, has_header=False, encoding="utf8")
        return self.parse_calendar(df)

    def add_event(self, events: list[Event]):
        """Добавление события в расписание"""
        # TODO: реализовать добавление события в расписание
        pass


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

    print(scheduler.get_events_from_google_sheet())
