"""Règles métier communes pour la récupération liée aux nuitées de minicamp.

Ce module sépare volontairement les unités selon le régime :
- salarié CCNS : banque en minutes ; 1 nuitée = 1 journée extrascolaire de référence ;
- CEE : banque en jours ; 1 nuitée = 1 jour.

La durée actuelle d'une journée extrascolaire est 9 h 36 (576 minutes), mais elle
reste un paramètre de référence et non une propriété intrinsèque d'une nuitée.
Aucune conversion automatique entre jours CEE et heures CCNS n'est autorisée ici.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


RegimeRecuperation = Literal["CCNS", "CEE"]

JOURNEE_EXTRASCOLAIRE_MINUTES_ACTUELLE = 9 * 60 + 36
CEE_JOURS_PAR_NUITEE = 1
_REFERENCE_EXTRASCOLAIRE_COURANTE = object()


@dataclass(frozen=True)
class RecuperationCredit:
    regime: RegimeRecuperation
    nuitees: int
    unite: Literal["minutes", "jours"]
    valeur: int


def credit_recuperation_minicamp(
    nuitees: int,
    regime: RegimeRecuperation,
    *,
    journee_extrascolaire_minutes=_REFERENCE_EXTRASCOLAIRE_COURANTE,
) -> RecuperationCredit:
    """Calcule le crédit de récupération généré par des nuitées de minicamp.

    ``nuitees`` doit être un entier positif ou nul.

    Pour un salarié CCNS, une nuitée crédite l'équivalent d'une journée
    extrascolaire. Sa durée actuelle est 576 minutes (9 h 36). Quand aucune
    durée n'est fournie, la référence courante est résolue au moment de l'appel,
    afin qu'une évolution de configuration ne reste pas figée dans la signature.

    Pour un CEE, une nuitée crédite 1 jour sans conversion horaire.
    """
    if isinstance(nuitees, bool) or not isinstance(nuitees, int):
        raise TypeError("Le nombre de nuitées doit être un entier.")
    if nuitees < 0:
        raise ValueError("Le nombre de nuitées ne peut pas être négatif.")

    if regime == "CCNS":
        if journee_extrascolaire_minutes is _REFERENCE_EXTRASCOLAIRE_COURANTE:
            journee_extrascolaire_minutes = JOURNEE_EXTRASCOLAIRE_MINUTES_ACTUELLE
        if isinstance(journee_extrascolaire_minutes, bool) or not isinstance(
            journee_extrascolaire_minutes, int
        ):
            raise TypeError("La durée de la journée extrascolaire doit être un entier de minutes.")
        if journee_extrascolaire_minutes <= 0:
            raise ValueError("La durée de la journée extrascolaire doit être strictement positive.")
        return RecuperationCredit(
            regime="CCNS",
            nuitees=nuitees,
            unite="minutes",
            valeur=nuitees * journee_extrascolaire_minutes,
        )
    if regime == "CEE":
        return RecuperationCredit(
            regime="CEE",
            nuitees=nuitees,
            unite="jours",
            valeur=nuitees * CEE_JOURS_PAR_NUITEE,
        )

    raise ValueError("Régime de récupération inconnu : %r" % (regime,))


def format_minutes_recuperation(minutes: int) -> str:
    """Formate une banque CCNS en H:MM sans la borner à 24 heures."""
    if isinstance(minutes, bool) or not isinstance(minutes, int):
        raise TypeError("La récupération en minutes doit être un entier.")
    if minutes < 0:
        raise ValueError("Le crédit de récupération ne peut pas être négatif.")
    heures, reste = divmod(minutes, 60)
    return "%d:%02d" % (heures, reste)
