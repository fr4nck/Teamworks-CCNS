from enum import Enum


class ContractType(str, Enum):
    CDI = "CDI"
    CDII = "CDII"
    CDD = "CDD"
    APPRENTICESHIP = "APPRENTICESHIP"
    CEE = "CEE"
    INTERNSHIP = "INTERNSHIP"
    CIVIC_SERVICE = "CIVIC_SERVICE"
    OTHER = "OTHER"
