from __future__ import annotations

from datetime import date

from domain.engine.calculation_rule import CalculationRule
from domain.engine.rule_family import RuleFamily


def build_default_ccns_rules() -> list[CalculationRule]:
    return [
        CalculationRule(
            code="SENIORITY_G1_G6",
            label="Prime d'ancienneté standard groupes 1 à 6",
            family=RuleFamily.SENIORITY,
            context="contract",
            target_object="contract",
            effective_date=date(2026, 1, 1),
            priority=10,
            parameters={
                "groups_from": 1,
                "groups_to": 6,
                "step_years": 2,
                "percent_per_step": 1.0,
                "max_percent": 15.0,
                "base_reference": "SMC_GROUPE_3",
            },
        ),
        CalculationRule(
            code="APPRENTICESHIP_SCALE_STANDARD",
            label="Barème standard apprentissage",
            family=RuleFamily.APPRENTICESHIP,
            context="contract",
            target_object="contract",
            employment_regime_code="APPRENTICE",
            effective_date=date(2026, 1, 1),
            priority=10,
            parameters={
                "base_reference": "SMIC_OR_MORE_FAVORABLE_MINIMUM",
                "age_and_execution_year_matrix": {
                    "16_17": {"1": 27, "2": 39, "3": 55},
                    "18_20": {"1": 43, "2": 51, "3": 67},
                    "21_25": {"1": 53, "2": 61, "3": 78},
                    "26_plus": {"1": 100, "2": 100, "3": 100},
                },
            },
        ),
        CalculationRule(
            code="CCNS_MIN_G1_G6_MONTHLY",
            label="Minima mensuels groupes 1 à 6",
            family=RuleFamily.CCNS_MINIMUM,
            context="contract",
            target_object="contract",
            effective_date=date(2026, 1, 1),
            priority=10,
            parameters={
                "base_type": "MONTHLY",
                "groups": [1, 2, 3, 4, 5, 6],
            },
        ),
        CalculationRule(
            code="CCNS_MIN_G7_G8_ANNUAL",
            label="Minima annuels groupes 7 à 8",
            family=RuleFamily.CCNS_MINIMUM,
            context="contract",
            target_object="contract",
            effective_date=date(2026, 1, 1),
            priority=20,
            parameters={
                "base_type": "ANNUAL",
                "groups": [7, 8],
            },
        ),
    ]
