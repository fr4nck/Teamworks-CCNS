"""Règles métier communes pour la récupération liée aux nuitées de minicamp.

Ce module sépare volontairement les unités selon le régime :
- salarié CCNS : banque en minutes, 1 nuitée = 9 h 36 ;
- CEE : banque en jours, 1 nuitée = 1 jour.

Aucune conversion automatique entre jours CEE et heures CCNS n'est autorisée ici.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


RegimeRecuperation = Literal["CCNS", "CEE"]

CCNS_MINUTES_PAR_NUITEE = 9 * 60 + 36
CEE_JOURS_PAR_NUITEE = 1


@dataclass(frozen=True)
class RecuperationCredit:
    regime: RegimeRecuperation
    nuitees: int
    unite: Literal["minutes", "jours"]
    valeur: int


def credit_recuperation_minicamp(nuitees: int, regime: RegimeRecuperation) -> RecuperationCredit:
    """Calcule le crédit de récupération généré par des nuitées de minicamp.

    ``nuitees`` doit être un entier positif ou nul. Une nuitée crédite 576 minutes
    pour un salarié CCNS et 1 jour pour un CEE.
    """
    if isinstance(nuitees, bool) or not isinstance(nuitees, int):
        raise TypeError("Le nombre de nuitées doit être un entier.")
    if nuitees < 0:
        raise ValueError("Le nombre de nuitées ne peut pas être négatif.")

    if regime == "CCNS":
        return RecuperationCredit(
            regime="CCNS",
            nuitees=nuitees,
            unite="minutes",
            valeur=nuitees * CCNS_MINUTES_PAR_NUITEE,
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
