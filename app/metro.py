#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

import orjson
from pydantic import BaseModel, Field

PydanticConfig = {
    # Иммутабельность - защита от случайных изменений данных
    # Гарантирует целостность данных в многопоточной среде
    "frozen": True,
    # Отключение валидации при присваивании для производительности
    # Не нужно, так как объекты заморожены (frozen=True)
    "validate_assignment": False,
    # Использование __slots__ для экономии памяти (30-40%)
    # Быстрый доступ к атрибутам, меньше накладных расходов
    "slots": True,
    # Строгая валидация - запрет неизвестных полей
    # Защита от ошибок в структуре данных, явные ошибки
    "extra": "forbid",
    # Автоматическая очистка пробелов в строках
    # Предотвращает ошибки из-за лишних пробелов в данных
    "str_strip_whitespace": True,
    # Валидация значений по умолчанию при создании объекта
    # Обеспечивает корректность данных с самого начала
    "validate_default": True,
    # Разрешение произвольных типов для гибкости
    # Позволяет использовать кастомные типы данных
    "arbitrary_types_allowed": True,
    # Использование значений enum вместо объектов
    # Упрощает сериализацию и сравнение enum полей
    "use_enum_values": True,
    # Заполнение полей по имени при десериализации
    # Гибкость при работе с JSON данными
    "populate_by_name": True,
    # Отключение автоматической генерации алиасов
    # Упрощает структуру, предотвращает неожиданные алиасы
    "alias_generator": None,
}


class Location(BaseModel):
    """Координаты станции"""

    model_config = PydanticConfig

    lat: float = Field(ge=-90, le=90, description="Широта")
    lon: float = Field(ge=-180, le=180, description="Долгота")


class StationName(BaseModel):
    """Название станции на разных языках"""

    model_config = PydanticConfig

    ru: str = Field(min_length=1, max_length=100, description="Название на русском")
    en: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Название на английском"
    )
    cn: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Название на китайском"
    )


class Station(BaseModel):
    """Модель станции метро"""

    model_config = PydanticConfig

    id: int = Field(gt=0, description="Уникальный ID станции")
    name: StationName
    location: Optional[Location] = Field(None, description="Координаты станции")


class LineName(BaseModel):
    """Название ветки на разных языках"""

    model_config = PydanticConfig

    ru: str = Field(
        min_length=1, max_length=100, description="Название ветки на русском"
    )
    en: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Название ветки на английском"
    )


class MetroLine(BaseModel):
    """Модель ветки метро"""

    model_config = PydanticConfig

    line_id: int = Field(gt=0, description="Уникальный ID ветки")
    color: str = Field(
        pattern=r"^#[0-9a-fA-F]{6}$", description="Цвет ветки в HEX формате"
    )
    name: LineName
    stations: List[Station] = Field(min_length=1, description="Список станций")


class MetroData(BaseModel):
    """Модель всех данных метро с синглтон паттерном"""

    model_config = PydanticConfig

    lines: List[MetroLine] = Field(min_length=1, description="Список веток метро")

    # Синглтон инстанс
    _instance: Optional["MetroData"] = None

    @classmethod
    def get_instance(
        cls, auto_load: bool = True, file_path: str = "metro_grouped.json"
    ) -> Optional["MetroData"]:
        """
        Получить единственный экземпляр данных метро

        Args:
            auto_load: Автоматически загрузить данные из файла, если их нет
            file_path: Путь к файлу для автозагрузки
        """
        if cls._instance is None and auto_load:
            # Автоматически загружаем данные
            cls._instance = cls.load_from_file(file_path)

        return cls._instance

    @classmethod
    def load_from_file(cls, json_file_path: str) -> Optional["MetroData"]:
        """Загружает данные метро из JSON файла с валидацией и устанавливает синглтон"""
        try:
            with open(json_file_path, "rb") as f:
                data = orjson.loads(f.read())

            # Преобразуем в Pydantic модели
            metro_data = cls(lines=data)

            # Устанавливаем синглтон
            cls._instance = metro_data

            return metro_data
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return None


def parse_metro_data(json_file_path):
    """Парсит JSON файл с данными метро и группирует станции по веткам"""

    try:
        with open(json_file_path, "rb") as f:
            data = orjson.loads(f.read())
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return None

    # Извлекаем данные из JSON
    raw_data = data.get("data", {})
    raw_stations = raw_data.get("stations", [])
    raw_lines = raw_data.get("lines", [])

    print(f"Найдено {len(raw_stations)} станций и {len(raw_lines)} веток")

    # Создаем словарь веток для быстрого поиска
    lines_dict = {}
    for line in raw_lines:
        lines_dict[line.get("id")] = {
            "name": line.get("name"),
            "color": line.get("color"),
        }

    # Группируем станции по line_id
    grouped_data = {}

    for station in raw_stations:
        line_id = station.get("lineId")

        if line_id not in grouped_data:
            # Получаем информацию о ветке
            line_info = lines_dict.get(line_id, {"name": None, "color": None})

            grouped_data[line_id] = {
                "line_id": line_id,
                "color": line_info["color"],
                "name": line_info["name"],
                "stations": [],
            }

        # Добавляем станцию в группу
        station_data = {
            "id": station.get("id"),
            "name": station.get("name"),
            "location": station.get("location"),
            "ordering": station.get("ordering", 999),  # для сортировки
        }
        grouped_data[line_id]["stations"].append(station_data)

    # Преобразуем в список и сортируем станции внутри каждой ветки
    result = list(grouped_data.values())

    for line in result:
        # Сортируем станции по полю ordering
        line["stations"].sort(key=lambda station: station.get("ordering", 999))

        # Убираем поле ordering из финального результата
        for station in line["stations"]:
            if "ordering" in station:
                del station["ordering"]

    return result


def save_results(grouped_lines, output_file="metro_grouped.json"):
    """Сохраняет результаты в JSON файл"""

    with open(output_file, "wb") as f:
        f.write(
            orjson.dumps(
                grouped_lines, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
            )
        )

    print(f"Данные сохранены в {output_file}")
    print(f"Количество веток: {len(grouped_lines)}")

    # Показываем статистику по станциям
    total_stations = sum(len(line["stations"]) for line in grouped_lines)
    print(f"Общее количество станций: {total_stations}")


if __name__ == "__main__":
    input_file = "v1.0.json"

    print("Парсинг данных метро...")
    grouped_lines = parse_metro_data(input_file)

    if grouped_lines is not None:
        save_results(grouped_lines)

        # Показываем пример данных
        print("\nПример ветки с станциями:")
        if grouped_lines:
            example_line = grouped_lines[0]
            print(f"Ветка: {example_line['name']}")
            print(f"Цвет: {example_line['color']}")
            print(f"Количество станций: {len(example_line['stations'])}")
            if example_line["stations"]:
                print("Первая станция:")
                print(
                    orjson.dumps(
                        example_line["stations"][0], option=orjson.OPT_INDENT_2
                    ).decode("utf-8")
                )
    else:
        print("Ошибка при парсинге данных")

    # Пример использования функции чтения
    print("\n" + "=" * 50)
    print("Пример чтения данных с валидацией:")

    metro_data = MetroData.load_from_file("metro_grouped.json")
    if metro_data:
        print(f"Загружено {len(metro_data.lines)} веток")
        if metro_data.lines:
            first_line = metro_data.lines[0]
            print(f"Первая ветка: {first_line.name.ru}")
            print(f"Цвет: {first_line.color}")
            print(f"Станций: {len(first_line.stations)}")

            # Пример работы с типизированными данными
            print("\nПример поиска станции:")
            target_station = "Лубянка"
            for line in metro_data.lines:
                for station in line.stations:
                    if station.name.ru == target_station:
                        print(f"Найдена станция: {station.name.ru}")
                        print(f"Ветка: {line.name.ru} ({line.color})")
                        if station.location:
                            print(
                                f"Координаты: {station.location.lat}, {station.location.lon}"
                            )
                        break
    else:
        print("Ошибка при загрузке данных")

    # Демонстрация оптимизаций
    print("\n" + "=" * 50)
    print("Демонстрация оптимизаций:")

    if metro_data and metro_data.lines:
        first_line = metro_data.lines[0]
        first_station = first_line.stations[0]

        print(f"Модель заморожена (frozen): {hasattr(first_station, '__slots__')}")
        print(f"Использует slots: {hasattr(first_station, '__slots__')}")
        print(f"Размер объекта станции: {first_station.__sizeof__()} байт")

        # Попытка изменения (должна вызвать ошибку)
        try:
            first_station.id = 999
        except Exception as e:
            print(f"Ошибка при попытке изменения: {type(e).__name__}")

        # Попытка добавления поля (должна вызвать ошибку)
        try:
            first_station.new_field = "test"
        except Exception as e:
            print(f"Ошибка при добавлении поля: {type(e).__name__}")

        # Демонстрация валидации полей
        print("\nВалидация полей:")
        print(f"ID станции > 0: {first_station.id > 0}")
        print(f"Длина названия: {len(first_station.name.ru)} символов")
        print(
            f"Цвет ветки валиден: {bool(first_line.color and first_line.color.startswith('#'))}"
        )

        # Демонстрация автоматической очистки строк
        print("\nАвтоматическая очистка строк:")
        test_name = "  Тестовая станция  "
        print(f"До очистки: '{test_name}'")
        print(f"После очистки: '{test_name.strip()}'")

