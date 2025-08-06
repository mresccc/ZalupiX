import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserProfileModel
from app.repository.base import SQLAlchemyRepository
from app.schemas import UserProfileUpdateRequest
from app.service.models import UserProfile


class UserRepository(SQLAlchemyRepository):
    """Репозиторий для работы с пользователями"""

    def __init__(self, db: AsyncSession):
        super().__init__(UserProfileModel, db)

    def _model_to_pydantic(self, db_model: UserProfileModel) -> UserProfile:
        """Конвертировать SQLAlchemy модель в Pydantic модель"""
        return UserProfile(
            telegram_id=db_model.telegram_id,
            telegram_nickname=db_model.telegram_nickname,
            vk_nickname=db_model.vk_nickname,
            status=db_model.status,
            full_name=db_model.full_name,
            phone_number=db_model.phone_number,
            live_metro_station=json.loads(db_model.live_metro_station),
            study_metro_station=json.loads(db_model.study_metro_station),
            year_of_admission=db_model.year_of_admission,
            has_driver_license=db_model.has_driver_license,
            date_of_birth=db_model.date_of_birth,
            has_printer=db_model.has_printer,
            can_host_night=db_model.can_host_night,
        )

    def _pydantic_to_model(self, pydantic_model: UserProfile) -> UserProfileModel:
        """Конвертировать Pydantic модель в SQLAlchemy модель"""
        return UserProfileModel(
            telegram_id=pydantic_model.telegram_id,
            telegram_nickname=pydantic_model.telegram_nickname,
            vk_nickname=pydantic_model.vk_nickname,
            status=pydantic_model.status,
            full_name=pydantic_model.full_name,
            phone_number=pydantic_model.phone_number,
            live_metro_station=json.dumps(pydantic_model.live_metro_station),
            study_metro_station=json.dumps(pydantic_model.study_metro_station),
            year_of_admission=pydantic_model.year_of_admission,
            has_driver_license=pydantic_model.has_driver_license,
            date_of_birth=pydantic_model.date_of_birth,
            has_printer=pydantic_model.has_printer,
            can_host_night=pydantic_model.can_host_night,
        )

    async def get_user_by_telegram_id(self, telegram_id: int) -> UserProfile | None:
        """Получить пользователя по Telegram ID"""
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        db_model = result.scalar_one_or_none()
        if db_model:
            return self._model_to_pydantic(db_model)
        return None

    async def create_user(self, user_profile: UserProfile) -> UserProfile:
        """Создать нового пользователя"""
        db_model = self._pydantic_to_model(user_profile)
        self.db.add(db_model)
        await self.db.commit()
        await self.db.refresh(db_model)
        return self._model_to_pydantic(db_model)

    async def update_user(
        self, telegram_id: int, update_request: UserProfileUpdateRequest
    ) -> UserProfile | None:
        """Обновить профиль пользователя по Telegram ID"""
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        db_model = result.scalar_one_or_none()

        if not db_model:
            return None

        # Обновляем поля из запроса
        fields_to_update = update_request.fields
        for field, value in fields_to_update.items():
            if hasattr(db_model, field):
                if field in ["live_metro_station", "study_metro_station"]:
                    setattr(db_model, field, json.dumps(value))
                else:
                    setattr(db_model, field, value)

        await self.db.commit()
        await self.db.refresh(db_model)
        return self._model_to_pydantic(db_model)

    async def delete_user(self, telegram_id: int) -> bool:
        """Удалить пользователя по Telegram ID"""
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model:
            await self.db.delete(db_model)
            await self.db.commit()
            return True
        return False

    async def user_exists(self, telegram_id: int) -> bool:
        """Проверить существование пользователя по Telegram ID"""
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_users_by_status(self, status) -> list[UserProfile]:
        """Получить пользователей по статусу"""
        stmt = select(self.model).where(self.model.status == status)
        result = await self.db.execute(stmt)
        db_models = result.scalars().all()
        return [self._model_to_pydantic(model) for model in db_models]

    async def get_users_by_course(self, course_number: int) -> list[UserProfile]:
        """Получить пользователей по курсу"""
        target_year = date.today().year - course_number
        stmt = select(self.model).where(self.model.year_of_admission == target_year)
        result = await self.db.execute(stmt)
        db_models = result.scalars().all()
        return [self._model_to_pydantic(model) for model in db_models]
