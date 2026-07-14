from __future__ import annotations

from datetime import date

from domain.engine.rule_reference import RuleReference, RuleReferenceStatus

CCNS_OFFICIAL_URL = "https://www.legifrance.gouv.fr/conv_coll/id/KALICONT000017577652"


def build_default_ccns_rule_references() -> dict[str, RuleReference]:
    """Références réglementaires initiales raccordées aux règles CCNS documentées."""

    return {
        "SENIORITY_G1_G6": RuleReference(
            code="REF_CCNS_SENIORITY_G1_G6_2026",
            title="Prime d'ancienneté standard des groupes 1 à 6",
            official_source="Convention collective nationale du sport publiée sur Légifrance",
            official_url=CCNS_OFFICIAL_URL,
            organization="Légifrance / partenaires sociaux de la branche sport",
            legal_reference="CCNS - dispositions relatives à la prime d'ancienneté",
            effective_date=date(2026, 1, 1),
            version="2026-01",
            comment="Première référence documentaire raccordée au moteur sans modifier le calcul existant.",
            status=RuleReferenceStatus.DRAFT,
            confidence_level="à consolider par revue juridique",
            calculation_mode="Pourcentage progressif paramétré dans la règle métier existante.",
        ),
        "CCNS_MIN_G1_G6_MONTHLY": RuleReference(
            code="REF_CCNS_MIN_G1_G6_MONTHLY_2026",
            title="Minima conventionnels mensuels des groupes 1 à 6",
            official_source="Convention collective nationale du sport publiée sur Légifrance",
            official_url=CCNS_OFFICIAL_URL,
            organization="Légifrance / partenaires sociaux de la branche sport",
            legal_reference="CCNS - grille des salaires minima conventionnels",
            effective_date=date(2026, 1, 1),
            version="2026-01",
            comment="Référence de traçabilité pour les minima mensuels ; les montants restent fournis par la grille existante.",
            status=RuleReferenceStatus.DRAFT,
            confidence_level="à consolider par revue juridique",
            calculation_mode="Comparaison entre la rémunération contractuelle et la ligne de grille applicable.",
        ),
    }
