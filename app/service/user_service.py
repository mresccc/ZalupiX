from models import UserProfile
from schemas import UserProfileUpdateRequest


class UserService:
    def __init__(self):
        pass

    def get_user_profile(self, telegram_id: int) -> UserProfile:
        return UserProfile(telegram_id=telegram_id)
    
    def update_user_profile(self, update_request: UserProfileUpdateRequest) -> bool:
        return True