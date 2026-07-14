from __future__ import annotations

from enum import Enum


class LegalCertainty(str, Enum):
    """Niveau de confiance juridique attaché à une règle de contrôle."""

    NON_EVALUEE = "NON_EVALUEE"
    CERTAINE = "CERTAINE"
    MAJORITAIRE = "MAJORITAIRE"
    DISCUTEE = "DISCUTEE"
    CONTEXTUELLE = "CONTEXTUELLE"
    INTERNE = "INTERNE"


LEGAL_CERTAINTY_DESCRIPTIONS: dict[LegalCertainty, str] = {
    LegalCertainty.NON_EVALUEE: "Niveau non qualifié ou pas encore analysé juridiquement.",
    LegalCertainty.CERTAINE: "Texte officiel clair, contrôle objectif et directement vérifiable.",
    LegalCertainty.MAJORITAIRE: "Texte existant avec une interprétation largement admise et peu de divergences.",
    LegalCertainty.DISCUTEE: "Interprétations concurrentes, jurisprudence ou pratiques susceptibles de varier.",
    LegalCertainty.CONTEXTUELLE: "Qualification dépendant fortement de l'organisation, des accords ou du contexte de travail.",
    LegalCertainty.INTERNE: "Règle propre à Teamworks ou à l'association, non directement imposée par un texte réglementaire.",
}
