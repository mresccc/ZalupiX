#!/usr/bin/env python3
"""Скрипт для инициализации базы данных"""

import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Base
from app.repository.user import UserRepository
from app.service.csv_import_service import CSVImportService
from app.service.user_service import UserService


async def init_database():
    """Инициализация базы данных"""
    # Создаем engine
    engine = create_async_engine(settings.database_url, echo=True)

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем сессию
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return engine, async_session


async def import_initial_data(csv_path: str = "app/init.csv"):
    """Импорт начальных данных из CSV файла"""
    print("🚀 Инициализация базы данных...")

    # Инициализируем БД
    engine, async_session = await init_database()

    try:
        # Создаем сервисы
        async with async_session() as session:
            user_repository = UserRepository(session)
            user_service = UserService(user_repository)
            csv_service = CSVImportService(user_service)

            # Проверяем существование CSV файла
            if not os.path.exists(csv_path):
                print(f"❌ Файл {csv_path} не найден!")
                return

            print(f"📁 Импортируем данные из {csv_path}...")

            # Импортируем данные
            result = await csv_service.import_from_csv(csv_path)

            if result["success"]:
                print("✅ Импорт завершен успешно!")
                print(f"   📊 Импортировано: {result['imported_count']}")
                print(f"   ⏭️  Пропущено: {result['skipped_count']}")
            else:
                print("❌ Ошибки при импорте:")
                for error in result["errors"]:
                    print(f"   - {error}")

    finally:
        await engine.dispose()


async def export_data(output_path: str = "app/export.csv"):
    """Экспорт данных в CSV файл"""
    print("📤 Экспорт данных...")

    # Инициализируем БД
    engine, async_session = await init_database()

    try:
        # Создаем сервисы
        async with async_session() as session:
            user_repository = UserRepository(session)
            user_service = UserService(user_repository)
            csv_service = CSVImportService(user_service)

            # Экспортируем данные
            result = await csv_service.export_to_csv(output_path)

            if result["success"]:
                print("✅ Экспорт завершен успешно!")
                print(f"   📊 Экспортировано: {result['exported_count']} записей")
                print(f"   📁 Файл сохранен: {output_path}")
            else:
                print("❌ Ошибки при экспорте:")
                for error in result["errors"]:
                    print(f"   - {error}")

    finally:
        await engine.dispose()


async def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Управление базой данных")
    parser.add_argument(
        "--action",
        choices=["import", "export", "both"],
        default="import",
        help="Действие: import (импорт), export (экспорт), both (оба)",
    )
    parser.add_argument(
        "--input", default="app/init.csv", help="Путь к входному CSV файлу"
    )
    parser.add_argument(
        "--output", default="app/export.csv", help="Путь к выходному CSV файлу"
    )

    args = parser.parse_args()

    if args.action in ["import", "both"]:
        await import_initial_data(args.input)

    if args.action in ["export", "both"]:
        await export_data(args.output)


if __name__ == "__main__":
    asyncio.run(main())
