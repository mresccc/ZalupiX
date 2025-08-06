from abc import ABC, abstractmethod

from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository(ABC):
    """Базовый протокол репозитория с CRUD операциями"""

    @abstractmethod
    async def create(self, obj_in: BaseModel) -> BaseModel:
        """Создать новую запись"""
        pass

    @abstractmethod
    async def get(self, id: int) -> BaseModel | None:
        """Получить запись по ID"""
        pass

    @abstractmethod
    async def update(self, id: int, obj_in: BaseModel) -> BaseModel | None:
        """Обновить запись"""
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Удалить запись"""
        pass


class SQLAlchemyRepository(BaseRepository):
    """Реализация базового репозитория для SQLAlchemy"""

    def __init__(self, model, db: AsyncSession):
        self.model = model
        self.db = db

    async def create(self, obj_in: BaseModel) -> BaseModel:
        """Создать новую запись"""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get(self, id: int) -> BaseModel | None:
        """Получить запись по ID"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, id: int, obj_in: BaseModel) -> BaseModel | None:
        """Обновить запись"""
        # Получаем только непустые поля
        update_data = {k: v for k, v in obj_in.model_dump().items() if v is not None}

        if not update_data:
            return await self.get(id)

        stmt = update(self.model).where(self.model.id == id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()

        return await self.get(id)

    async def delete(self, id: int) -> bool:
        """Удалить запись"""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def get_all(self) -> list[BaseModel]:
        """Получить все записи"""
        stmt = select(self.model)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_field(self, field_name: str, value) -> list[BaseModel]:
        """Получить записи по полю"""
        stmt = select(self.model).where(getattr(self.model, field_name) == value)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def exists(self, id: int) -> bool:
        """Проверить существование записи"""
        return await self.get(id) is not None
