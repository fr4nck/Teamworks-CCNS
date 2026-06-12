from enum import Enum


class ResultStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    WARNING = "WARNING"
    DATA_ERROR = "DATA_ERROR"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INFO = "INFO"
