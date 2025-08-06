import csv
from datetime import datetime
from typing import List

from app.models import UserDriverLicenseEnum, UserPrinterEnum, UserStatusEnum
from app.service.models import UserProfile
from app.service.user_service import UserService


class CSVImportService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

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

    async def import_from_csv(self, csv_file_path: str) -> dict:
        """Импортировать данные из CSV файла в базу"""
        imported_count = 0
        skipped_count = 0
        errors = []

        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Начинаем с 2, так как 1 - заголовки
                    try:
                        # Проверяем обязательные поля
                        if not row.get("Telegram ID") or not row.get("ФИО"):
                            skipped_count += 1
                            continue

                        # Проверяем, существует ли пользователь
                        telegram_id = int(row["Telegram ID"])
                        if await self.user_service.user_exists(telegram_id):
                            skipped_count += 1
                            continue

                        # Создаем объект UserProfile
                        user_profile = UserProfile(
                            telegram_id=telegram_id,
                            telegram_nickname=row.get("Ник в ТГ", ""),
                            vk_nickname=row.get("Ник в ВК", ""),
                            status=self._parse_status(row.get("Статус", "0")),
                            full_name=row["ФИО"].strip(),
                            phone_number=row.get("Номер телефона", ""),
                            live_metro_station=self._parse_metro_stations(
                                row.get("Станция метро, на которой ты живешь", "")
                            ),
                            study_metro_station=self._parse_metro_stations(
                                row.get(
                                    "Станция метро, на которой ты учишься/работаешь", ""
                                )
                            ),
                            year_of_admission=int(
                                row.get("Год поступления в СтС", datetime.now().year)
                            ),
                            has_driver_license=self._parse_driver_license(
                                row.get(
                                    "Есть ли у тебя водительские права и/или машина?",
                                    "0",
                                )
                            ),
                            date_of_birth=self._parse_date(
                                row.get("Дата Рождения", "")
                            ),
                            has_printer=self._parse_printer(
                                row.get("Если ли у тебя принтер?", "0")
                            ),
                            can_host_night=row.get(
                                "Можем ли мы проводить ночь креатива/ночь оформления у тебя дома?",
                                "0",
                            )
                            == "1",
                        )

                        # Сохраняем в базу
                        await self.user_service.create_user_profile(user_profile)
                        imported_count += 1

                    except Exception as e:
                        errors.append(f"Строка {row_num}: {str(e)}")
                        skipped_count += 1

        except Exception as e:
            errors.append(f"Ошибка чтения файла: {str(e)}")

        return {
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "errors": errors,
            "success": len(errors) == 0,
        }
