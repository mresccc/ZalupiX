from typing import Optional

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.enums import UserDriverLicenseEnum, UserPrinterEnum, UserStatusEnum


class Base(DeclarativeBase):
    pass


class UserProfileModel(Base):
    """SQLAlchemy модель пользователя"""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    telegram_nickname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    vk_nickname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[UserStatusEnum] = mapped_column(
        SQLEnum(UserStatusEnum), default=UserStatusEnum.INACTIVE
    )
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    live_metro_station: Mapped[Optional[str]] = mapped_column(
        JSON, nullable=True
    )  # JSON строка
    study_metro_station: Mapped[Optional[str]] = mapped_column(
        JSON, nullable=True
    )  # JSON строка
    year_of_admission: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_driver_license: Mapped[UserDriverLicenseEnum] = mapped_column(
        SQLEnum(UserDriverLicenseEnum), default=UserDriverLicenseEnum.NO
    )
    date_of_birth: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Простая строка
    has_printer: Mapped[UserPrinterEnum] = mapped_column(
        SQLEnum(UserPrinterEnum), default=UserPrinterEnum.NO
    )
    can_host_night: Mapped[bool] = mapped_column(Boolean, default=False)
