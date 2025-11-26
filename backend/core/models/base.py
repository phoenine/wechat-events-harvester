from enum import IntEnum

class DataStatus(IntEnum):
    DELETED = 1000
    ACTIVE = 1
    INACTIVE = 2
    PENDING = 3
    COMPLETED = 4
    FAILED = 5