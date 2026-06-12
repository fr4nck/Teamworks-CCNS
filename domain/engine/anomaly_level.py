from enum import Enum


class AnomalyLevel(str, Enum):
    INFO = "INFO"
    ATTENTION = "ATTENTION"
    BLOCKING = "BLOCKING"
