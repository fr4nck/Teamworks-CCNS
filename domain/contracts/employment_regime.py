from enum import Enum


class EmploymentRegime(str, Enum):
    """Régimes métier pouvant être portés par un profil d'emploi.

    Les valeurs historiques sont conservées afin de ne pas modifier les codes
    déjà utilisés par les contrats et les règles existants.
    """

    CCNS_STANDARD = "CCNS_STANDARD"
    CCNS_MODULATION = "CCNS_MODULATION"
    CCNS_CDII = "CCNS_CDII"
    APPRENTICESHIP = "APPRENTICESHIP"
    APPRENTICE = "APPRENTICE"
    CEE = "CEE"
    CIVIC_SERVICE = "CIVIC_SERVICE"
    PEC_CUI_CAE = "PEC_CUI_CAE"
    SERVICE_CIVIQUE = "SERVICE_CIVIQUE"
    INTERNSHIP = "INTERNSHIP"
    STAGE_PFMP = "STAGE_PFMP"
    VOLUNTEER = "VOLUNTEER"
    EXTERNAL_PROVIDER = "EXTERNAL_PROVIDER"
    MANUAL_OUTSIDE_SCOPE = "MANUAL_OUTSIDE_SCOPE"
