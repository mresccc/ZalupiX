from enum import Enum


class UserStatusEnum(int, Enum):
    INACTIVE = 0
    WORK = 1
    ACTIVE = 2
    GRADUATED = 3


class UserDriverLicenseEnum(int, Enum):
    NO = 0
    YES = 1
    YES_AND_CAR = 2


class UserPrinterEnum(int, Enum):
    NO = 0
    BLACK = 1
    COLOR = 2
    BLACK_AND_COLOR = 3
