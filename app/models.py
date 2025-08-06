from enum import Enum

from sqlalchemy import Boolean, Column, Date, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserStatusEnum(str, Enum):
    INACTIVE = "inactive"
    WORK = "work"
    ACTIVE = "active"
    GRADUATED = "graduated"


class UserDriverLicenseEnum(str, Enum):
    NO = "no"
    YES = "yes"
    YES_AND_CAR = "yes_and_car"


class UserPrinterEnum(str, Enum):
    NO = "no"
    BLACK = "black"
    COLOR = "color"
    BLACK_AND_COLOR = "black_and_color"


class UserProfileModel(Base):
    """SQLAlchemy модель пользователя"""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    telegram_nickname = Column(String, nullable=False)
    vk_nickname = Column(String, nullable=False)
    status = Column(SQLEnum(UserStatusEnum), nullable=False)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    live_metro_station = Column(String, nullable=False)  # JSON строка
    study_metro_station = Column(String, nullable=False)  # JSON строка
    year_of_admission = Column(Integer, nullable=False)
    has_driver_license = Column(SQLEnum(UserDriverLicenseEnum), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    has_printer = Column(SQLEnum(UserPrinterEnum), nullable=False)
    can_host_night = Column(Boolean, nullable=False)
