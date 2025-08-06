import asyncio
import csv
from datetime import datetime
from pathlib import Path
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import (
    UserDriverLicenseEnum,
    UserPrinterEnum,
    UserProfileModel,
    UserStatusEnum,
)


class CSVImportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _parse_status(self, status_str: str) -> UserStatusEnum:
        """Преобразовать статус из CSV в enum"""
        status_map = {
            "0": UserStatusEnum.INACTIVE,
            "1": UserStatusEnum.WORK,
            "2": UserStatusEnum.ACTIVE,
            "3": UserStatusEnum.GRADUATED,
        }
        return status_map.get(status_str, UserStatusEnum.INACTIVE)

    def _parse_driver_license(self, license_str: str) -> UserDriverLicenseEnum:
        """Преобразовать права из CSV в enum"""
        license_map = {
            "0": UserDriverLicenseEnum.NO,
            "1": UserDriverLicenseEnum.YES,
            "2": UserDriverLicenseEnum.YES_AND_CAR,
        }
        return license_map.get(license_str, UserDriverLicenseEnum.NO)

    def _parse_printer(self, printer_str: str) -> UserPrinterEnum:
        """Преобразовать принтер из CSV в enum"""
        printer_map = {
            "0": UserPrinterEnum.NO,
            "1": UserPrinterEnum.BLACK,
            "2": UserPrinterEnum.COLOR,
            "3": UserPrinterEnum.BLACK_AND_COLOR,
        }
        return printer_map.get(printer_str, UserPrinterEnum.NO)

    def _parse_date(self, date_str: str) -> datetime.date:
        """Преобразовать дату из CSV в date объект"""
        if not date_str or date_str.strip() == "":
            return datetime.now().date()

        try:
            return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
        except ValueError:
            return datetime.now().date()

    def _parse_metro_stations(self, stations_str: str) -> List[str]:
        """Преобразовать строку со станциями метро в список"""
        if not stations_str or stations_str.strip() == "":
            return []

        # Разделяем по запятой и убираем лишние пробелы
        stations = [station.strip() for station in stations_str.split(",")]
        return [station for station in stations if station]

    def _parse_year_of_admission(self, year_str: str) -> int:
        """Преобразовать год поступления"""
        if not year_str or year_str.strip() == "":
            return datetime.now().year

        try:
            return int(year_str.strip())
        except ValueError:
            return datetime.now().year

    def _parse_telegram_id(self, telegram_id_str: str) -> int | None:
        """Преобразовать Telegram ID"""
        if not telegram_id_str or telegram_id_str.strip() == "":
            return None

        try:
            return int(telegram_id_str.strip())
        except ValueError:
            return None

    async def import_from_csv(
        self, csv_file_path: str, skip_existing: bool = True
    ) -> dict:
        """Импортировать данные из CSV файла в базу"""
        imported_count = 0
        skipped_count = 0
        updated_count = 0
        errors = []

        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Начинаем с 2, так как 1 - заголовки
                    try:
                        # Проверяем минимально необходимые поля
                        telegram_id = self._parse_telegram_id(
                            row.get("Telegram ID", "")
                        )
                        full_name = row.get("ФИО", "").strip()

                        if not telegram_id or not full_name:
                            errors.append(
                                f"Строка {row_num}: Отсутствует Telegram ID или ФИО"
                            )
                            skipped_count += 1
                            continue

                        # Проверяем, существует ли пользователь
                        from sqlalchemy import select

                        stmt = select(UserProfileModel).where(
                            UserProfileModel.telegram_id == telegram_id
                        )
                        result = await self.session.execute(stmt)
                        existing_user = result.scalar_one_or_none()

                        if existing_user and skip_existing:
                            skipped_count += 1
                            continue

                        # Создаем объект UserProfileModel
                        import json

                        user_data = {
                            "telegram_id": telegram_id,
                            "telegram_nickname": row.get("Ник в ТГ", ""),
                            "vk_nickname": row.get("Ник в ВК", ""),
                            "status": self._parse_status(row.get("Статус", "0")),
                            "full_name": full_name,
                            "phone_number": row.get("Номер телефона", ""),
                            "live_metro_station": json.dumps(
                                self._parse_metro_stations(
                                    row.get("Станция метро, на которой ты живешь", "")
                                )
                            ),
                            "study_metro_station": json.dumps(
                                self._parse_metro_stations(
                                    row.get(
                                        "Станция метро, на которой ты учишься/работаешь",
                                        "",
                                    )
                                )
                            ),
                            "year_of_admission": self._parse_year_of_admission(
                                row.get("Год поступления в СтС", "")
                            ),
                            "has_driver_license": self._parse_driver_license(
                                row.get(
                                    "Есть ли у тебя водительские права и/или машина?",
                                    "0",
                                )
                            ),
                            "date_of_birth": self._parse_date(
                                row.get("Дата Рождения", "")
                            ),
                            "has_printer": self._parse_printer(
                                row.get("Если ли у тебя принтер?", "0")
                            ),
                            "can_host_night": row.get(
                                "Можем ли мы проводить ночь креатива/ночь оформления у тебя дома?",
                                "0",
                            )
                            == "1",
                        }

                        if existing_user:
                            # Обновляем существующего пользователя
                            for key, value in user_data.items():
                                if key != "telegram_id":  # Не обновляем ID
                                    setattr(existing_user, key, value)
                            updated_count += 1
                        else:
                            # Создаем нового пользователя
                            user_profile = UserProfileModel(**user_data)
                            self.session.add(user_profile)
                            imported_count += 1

                        await self.session.commit()

                    except Exception as e:
                        errors.append(f"Строка {row_num}: {str(e)}")
                        skipped_count += 1
                        await self.session.rollback()

        except Exception as e:
            errors.append(f"Ошибка чтения файла: {str(e)}")

        return {
            "imported_count": imported_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "errors": errors,
            "success": len(errors) == 0,
        }


async def main():
    """Основная функция для импорта CSV"""
    # Создаем движок базы данных
    engine = create_async_engine("sqlite+aiosqlite:///./zalupix.db", echo=True)

    # Создаем фабрику сессий
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Создаем сессию
    async with session_factory() as session:
        # Создаем сервис импорта
        csv_import_service = CSVImportService(session)

        # Путь к CSV файлу
        csv_file_path = Path(
            "app/Копия LV'25 _ Форма организатора (Ответы) - ИТОГ - полная инфа.csv"
        )

        if not csv_file_path.exists():
            print(f"Файл не найден: {csv_file_path}")
            return

        print(f"Начинаем импорт из файла: {csv_file_path}")
        print("=" * 50)

        # Запускаем импорт
        result = await csv_import_service.import_from_csv(
            str(csv_file_path), skip_existing=False
        )

        # Выводим результаты
        print(f"Импортировано новых пользователей: {result['imported_count']}")
        print(f"Обновлено существующих пользователей: {result['updated_count']}")
        print(f"Пропущено записей: {result['skipped_count']}")
        print(f"Успешно: {result['success']}")

        if result["errors"]:
            print("\nОшибки:")
            for error in result["errors"]:
                print(f"  - {error}")

        print("=" * 50)
        print("Импорт завершен!")


if __name__ == "__main__":
    asyncio.run(main())
