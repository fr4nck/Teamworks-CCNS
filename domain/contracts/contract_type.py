from enum import Enum


class ContractType(str, Enum):
    CDI = "CDI"
    CDD = "CDD"
    CDII = "CDII"
    APPRENTICESHIP = "APPRENTICESHIP"
    CEE = "CEE"
    INTERNSHIP = "INTERNSHIP"
    CIVIC_SERVICE = "CIVIC_SERVICE"
    OTHER = "OTHER"
