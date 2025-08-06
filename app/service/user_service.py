from app.repository.user import UserRepository
from app.schemas import UserProfileUpdateRequest
from app.service.models import UserProfile


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user_profile(self, telegram_id: int) -> UserProfile | None:
        """Получить профиль пользователя"""
        return await self.repository.get_user_by_telegram_id(telegram_id)

    async def create_user_profile(self, user_profile: UserProfile) -> UserProfile:
        """Создать новый профиль пользователя"""
        return await self.repository.create_user(user_profile)

    async def update_user_profile(
        self, telegram_id: int, update_request: UserProfileUpdateRequest
    ) -> UserProfile | None:
        """Обновить профиль пользователя"""
        return await self.repository.update_user(telegram_id, update_request)

    async def delete_user_profile(self, telegram_id: int) -> bool:
        """Удалить профиль пользователя"""
        return await self.repository.delete_user(telegram_id)

    async def get_all_users(self) -> list[UserProfile]:
        """Получить всех пользователей"""
        return await self.repository.get_all()

    async def user_exists(self, telegram_id: int) -> bool:
        """Проверить существование пользователя"""
        return await self.repository.user_exists(telegram_id)

    async def get_users_by_status(self, status) -> list[UserProfile]:
        """Получить пользователей по статусу"""
        return await self.repository.get_users_by_status(status)

    async def get_users_by_course(self, course_number: int) -> list[UserProfile]:
        """Получить пользователей по курсу"""
        return await self.repository.get_users_by_course(course_number)
