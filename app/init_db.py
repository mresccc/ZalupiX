#!/usr/bin/env python3
"""Скрипт для инициализации базы данных"""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.models import Base


async def init_db():
    """Инициализация базы данных"""
    # Создаем движок для SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///./zalupix.db",
        echo=True,
    )

    async with engine.begin() as conn:
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)

    print("✅ База данных инициализирована успешно!")
    print("📁 Файл БД: zalupix.db")


if __name__ == "__main__":
    asyncio.run(init_db())
