import csv
from datetime import datetime
from typing import List, Optional

from app.enums import UserDriverLicenseEnum, UserPrinterEnum, UserStatusEnum
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

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Преобразовать дату из CSV в date объект"""
        if not date_str or date_str.strip() == "":
            return None

        try:
            return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
        except ValueError:
            return None

    def _parse_metro_stations(self, stations_str: str) -> List[int]:
        """Преобразовать строку со станциями метро в список ID"""
        if not stations_str or stations_str.strip() == "":
            return []

        # Разделяем по запятой и убираем лишние пробелы
        stations = [station.strip() for station in stations_str.split(",")]
        result = []

        for station in stations:
            if station:
                try:
                    # Пытаемся преобразовать в число
                    station_id = int(station)
                    result.append(station_id)
                except ValueError:
                    # Если не число, пропускаем
                    continue

        return result

    def _parse_year_of_admission(self, year_str: str) -> int:
        """Преобразовать год поступления"""
        if not year_str or year_str.strip() == "":
            return datetime.now().year

        try:
            return int(year_str.strip())
        except ValueError:
            return datetime.now().year

    async def import_from_csv(self, csv_file_path: str) -> dict:
        """Импортировать данные из CSV файла в базу"""
        imported_count = 0
        skipped_count = 0
        errors = []

        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row_num, row in enumerate(reader, start=2):
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
                            year_of_admission=self._parse_year_of_admission(
                                row.get("Год вступления в СтС", "")
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

    async def export_to_csv(self, csv_file_path: str) -> dict:
        """Экспортировать данные из базы в CSV файл"""
        exported_count = 0
        errors = []

        try:
            # Получаем всех пользователей
            users = await self.user_service.get_all_users()

            # Определяем заголовки CSV
            fieldnames = [
                "Telegram ID",
                "Ник в ТГ",
                "Ник в ВК",
                "Статус",
                "ФИО",
                "Номер телефона",
                "Станция метро, на которой ты живешь",
                "Станция метро, на которой ты учишься/работаешь",
                "Номер курса",
                "Год вступления в СтС",
                "Есть ли у тебя водительские права и/или машина?",
                "Дата Рождения",
                "Если ли у тебя принтер?",
                "Можем ли мы проводить ночь креатива/ночь оформления у тебя дома?",
                "Время последнего обновления",
            ]

            with open(csv_file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                for user in users:
                    try:
                        # Преобразуем данные для экспорта
                        row = {
                            "Telegram ID": user.telegram_id,
                            "Ник в ТГ": user.telegram_nickname or "",
                            "Ник в ВК": user.vk_nickname or "",
                            "Статус": user.status.value,
                            "ФИО": user.full_name,
                            "Номер телефона": user.phone_number or "",
                            "Станция метро, на которой ты живешь": ", ".join(
                                map(str, user.live_metro_station)
                            ),
                            "Станция метро, на которой ты учишься/работаешь": ", ".join(
                                map(str, user.study_metro_station)
                            ),
                            "Номер курса": user.course_number,
                            "Год вступления в СтС": user.year_of_admission,
                            "Есть ли у тебя водительские права и/или машина?": user.has_driver_license.value,
                            "Дата Рождения": user.date_of_birth.strftime("%d.%m.%Y")
                            if user.date_of_birth
                            else "",
                            "Если ли у тебя принтер?": user.has_printer.value,
                            "Можем ли мы проводить ночь креатива/ночь оформления у тебя дома?": "1"
                            if user.can_host_night
                            else "0",
                            "Время последнего обновления": "",
                        }

                        writer.writerow(row)
                        exported_count += 1

                    except Exception as e:
                        errors.append(
                            f"Ошибка экспорта пользователя {user.telegram_id}: {str(e)}"
                        )

        except Exception as e:
            errors.append(f"Ошибка записи файла: {str(e)}")

        return {
            "exported_count": exported_count,
            "errors": errors,
            "success": len(errors) == 0,
        }
