from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext

from domain.convention.smic import SmicCatalog, SmicTerritory


CEE_LEGAL_DAILY_SMIC_MULTIPLIER = Decimal("4.30")
CEE_LEGAL_SOURCE_REFERENCE = "CASF, article D432-2 — minimum journalier CEE = 4,30 x SMIC horaire depuis le 1er mai 2025"
_CENT = Decimal("0.01")

# Le minimum CEE est versionné indépendamment du catalogue de SMIC. Avant le
# 28 avril 2012, la règle de rémunération figurait à l'article D432-3 ; elle a
# ensuite été déplacée à D432-2 sans changer le coefficient de 2,20. Le décret
# n° 2024-1151 du 4 décembre 2024 porte ce coefficient à 4,30 au 1er mai 2025.
_CEE_LEGAL_DAILY_RULES = (
    (
        date(2008, 5, 1),
        Decimal("2.20"),
        "CASF, article D432-3 puis D432-2 — minimum journalier CEE = 2,20 x SMIC horaire",
    ),
    (
        date(2025, 5, 1),
        Decimal("4.30"),
        CEE_LEGAL_SOURCE_REFERENCE,
    ),
)


def legal_cee_daily_smic_multiplier_on(reference_date: date) -> Decimal:
    """Retourne le coefficient légal CEE applicable à la date demandée."""
    if type(reference_date) is not date:
        raise TypeError("reference_date doit être une date stricte.")

    applicable = None
    for effective_from, multiplier, _source in _CEE_LEGAL_DAILY_RULES:
        if reference_date >= effective_from:
            applicable = multiplier
        else:
            break
    if applicable is None:
        raise ValueError("Aucune règle de minimum journalier CEE n’est disponible à cette date.")
    return applicable


def legal_cee_daily_source_on(reference_date: date) -> str:
    """Retourne la référence réglementaire associée au coefficient appliqué."""
    if type(reference_date) is not date:
        raise TypeError("reference_date doit être une date stricte.")

    applicable = None
    for effective_from, _multiplier, source in _CEE_LEGAL_DAILY_RULES:
        if reference_date >= effective_from:
            applicable = source
        else:
            break
    if applicable is None:
        raise ValueError("Aucune règle de minimum journalier CEE n’est disponible à cette date.")
    return applicable


def legal_cee_daily_minimum(
    *,
    smic_catalog: SmicCatalog,
    reference_date: date,
    territory: SmicTerritory = SmicTerritory.METROPOLITAN_FRANCE,
) -> Decimal:
    """Retourne le minimum brut journalier CEE applicable à une date.

    Le multiplicateur légal est résolu à la date du contrat puis appliqué au
    SMIC horaire applicable, afin de conserver un calcul historique exact.
    Toute l'opération arithmétique, multiplication comprise, est isolée du
    contexte Decimal global laissé par le runtime legacy.
    """
    if type(smic_catalog) is not SmicCatalog:
        raise TypeError("smic_catalog doit être un SmicCatalog.")
    if type(reference_date) is not date:
        raise TypeError("reference_date doit être une date stricte.")
    if type(territory) is not SmicTerritory:
        raise TypeError("territory doit être un SmicTerritory.")

    hourly = smic_catalog.hourly_amount_on(reference_date, territory)
    multiplier = legal_cee_daily_smic_multiplier_on(reference_date)
    with localcontext() as context:
        context.prec = max(
            28,
            len(hourly.as_tuple().digits) + len(multiplier.as_tuple().digits) + 4,
        )
        amount = hourly * multiplier
        return amount.quantize(_CENT, rounding=ROUND_HALF_UP)
