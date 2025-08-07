from typing import Any, Dict, List, Literal, Optional, Union

import orjson

from app.config import METRO_DATA_PATH
from app.metro import LineName, MetroData, MetroLine, Station, StationName

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
    ) -> List[MetroLine]:
        """
        Получить данные метро

        Args:
            language: Язык для названий (ru, en, cn, all)
            include_location: Включать ли координаты станций
        """
        metro_data = self.get_metro_data()
        if metro_data is None:
            return []

        return metro_data.lines

    def get_optimized_metro_data(
        self,
        language: Language = "ru",
        include_location: bool = True,
    ) -> List[Dict[str, Any]]:
        """Получить оптимизированные данные метро с числовыми ключами"""
        lines = self.get_metro(language, include_location)

        return [self._optimize_line(line, language, include_location) for line in lines]

    def _optimize_line(
        self,
        line: MetroLine,
        language: Language,
        include_location: bool,
    ) -> Dict[str, Any]:
        """Оптимизировать ветку метро с числовыми ключами"""
        result = {
            "1": line.line_id,  # line_id
            "2": line.color,  # color
            "3": self._optimize_name(line.name, language),  # name
            "4": [
                self._optimize_station(station, language, include_location)
                for station in line.stations
            ],  # stations
        }
        return result

    def _optimize_station(
        self,
        station: Station,
        language: Language,
        include_location: bool,
    ) -> Dict[str, Any]:
        """Оптимизировать станцию"""
        result = {
            "1": station.id,  # id
            "2": self._optimize_name(station.name, language),  # name
        }

        if include_location and station.location:
            result["3"] = {
                "lat": station.location.lat,
                "lon": station.location.lon,
            }  # location

        return result

    def _optimize_name(
        self,
        name_obj: Union[StationName, LineName],
        language: Language,
    ) -> Union[str, Dict[str, str]]:
        """Оптимизировать название"""
        if language == "all":
            return name_obj.model_dump()
        else:
            return name_obj.get_name(language)
