from enum import Enum


class EmploymentRegime(str, Enum):
    """Régimes métier canoniques utilisés par le domaine CCNS.

    Les libellés historiques ``APPRENTICE``, ``SERVICE_CIVIQUE`` et
    ``STAGE_PFMP`` sont les codes canoniques. Les codes d'import plus récents
    (``APPRENTICESHIP``, ``CIVIC_SERVICE`` et ``INTERNSHIP``) doivent être
    convertis à la frontière du domaine et ne constituent pas des régimes.
    """

    CCNS_STANDARD = "CCNS_STANDARD"
    CCNS_MODULATION = "CCNS_MODULATION"
    CCNS_CDII = "CCNS_CDII"
    APPRENTICE = "APPRENTICE"
    CEE = "CEE"
    PEC_CUI_CAE = "PEC_CUI_CAE"
    SERVICE_CIVIQUE = "SERVICE_CIVIQUE"
    STAGE_PFMP = "STAGE_PFMP"
    VOLUNTEER = "VOLUNTEER"
    MANUAL_OUTSIDE_SCOPE = "MANUAL_OUTSIDE_SCOPE"
