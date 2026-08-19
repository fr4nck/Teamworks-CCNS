from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from domain.convention.smic import SmicCatalog, SmicTerritory


CEE_LEGAL_DAILY_SMIC_MULTIPLIER = Decimal("4.30")
CEE_LEGAL_SOURCE_REFERENCE = "CASF, article D432-2 — minimum journalier CEE = 4,30 x SMIC horaire"
_CENT = Decimal("0.01")


def legal_cee_daily_minimum(
    *,
    smic_catalog: SmicCatalog,
    reference_date: date,
    territory: SmicTerritory = SmicTerritory.METROPOLITAN_FRANCE,
) -> Decimal:
    """Retourne le minimum brut journalier CEE applicable à une date.

    Le multiplicateur légal est séparé du catalogue de SMIC afin que chaque
    évolution reste traçable et testable. Le SMIC applicable est résolu par le
    catalogue existant de Teamworks.
    """
    if type(smic_catalog) is not SmicCatalog:
        raise TypeError("smic_catalog doit être un SmicCatalog.")
    if type(reference_date) is not date:
        raise TypeError("reference_date doit être une date stricte.")
    if type(territory) is not SmicTerritory:
        raise TypeError("territory doit être un SmicTerritory.")

    hourly = smic_catalog.hourly_amount_on(reference_date, territory)
    return (hourly * CEE_LEGAL_DAILY_SMIC_MULTIPLIER).quantize(_CENT, rounding=ROUND_HALF_UP)
