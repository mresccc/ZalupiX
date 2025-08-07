from typing import Literal, Optional

import orjson

from app.config import METRO_DATA_PATH
from app.metro import MetroData

# Тип для языка
Language = Literal["ru", "en", "cn", "all"]


class MetroService:
    """Сервис для работы с данными метро"""

    def __init__(self, file_path: str = METRO_DATA_PATH):
        self.file_path = file_path
        self._metro_data: Optional[MetroData] = None

    def get_metro_data(self) -> Optional[MetroData]:
        """Получить данные метро (ленивая загрузка)"""
        if self._metro_data is None:
            self._metro_data = self._load_from_file()
        return self._metro_data

    def _load_from_file(self) -> Optional[MetroData]:
        """Загружает данные метро из JSON файла с валидацией"""
        try:
            with open(self.file_path, "rb") as f:
                data = orjson.loads(f.read())

            # Преобразуем в Pydantic модели
            metro_data = MetroData(lines=data)
            return metro_data
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return None

    def save_to_file(
        self,
        metro_data: MetroData,
        file_path: str,
        language: str = "ru",
        include_location: bool = True,
        include_all_names: bool = False,
    ) -> None:
        """Сохранить данные в файл с настройками"""
        data = metro_data.to_json(language, include_location, include_all_names)
        with open(file_path, "wb") as f:
            f.write(
                orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS)
            )

    def get_metro(
        self,
        language: Language = "ru",
        include_location: bool = True,
    ) -> MetroData:
        """
        Получить данные метро

        Args:
            language: Язык для названий (ru, en, cn, all)
            include_location: Включать ли координаты станций
        """
        return self.get_metro_data()
