from enum import Enum


class MinimumType(str, Enum):
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    PERCENT_SMIC = "PERCENT_SMIC"
    PERCENT_BASE = "PERCENT_BASE"
