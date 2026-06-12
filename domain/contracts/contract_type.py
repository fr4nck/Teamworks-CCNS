from enum import Enum


class ContractType(str, Enum):
    CDI = "CDI"
    CDD = "CDD"
    CDII = "CDII"
    APPRENTICESHIP = "APPRENTICESHIP"
    CEE = "CEE"
    OTHER = "OTHER"
