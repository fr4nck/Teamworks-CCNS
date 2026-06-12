from __future__ import annotations

from datetime import date

from domain.engine.calculation_rule import CalculationRule
from domain.engine.rule_family import RuleFamily


def build_default_rules() -> list[CalculationRule]:
    return [
        CalculationRule(
            code="TP_COURT_LE_10H",
            label="Majoration temps partiel court jusqu'à 10h",
            family=RuleFamily.SHORT_PART_TIME,
            context="contract",
            target_object="contract",
            employment_regime_code="CCNS_STANDARD",
            effective_date=date(2026, 1, 1),
            priority=10,
            parameters={
                "threshold_hours_min": 0.0,
                "threshold_hours_max": 10.0,
                "multiplier": 1.05,
            },
        ),
        CalculationRule(
            code="TP_COURT_LT_24H",
            label="Majoration temps partiel court au-delà de 10h et sous 24h",
            family=RuleFamily.SHORT_PART_TIME,
            context="contract",
            target_object="contract",
            employment_regime_code="CCNS_STANDARD",
            effective_date=date(2026, 1, 1),
            priority=20,
            parameters={
                "threshold_hours_min": 10.0001,
                "threshold_hours_max": 23.9999,
                "multiplier": 1.02,
            },
        ),
        CalculationRule(
            code="CEE_MAX_80J",
            label="Plafond CEE 80 jours sur 12 mois",
            family=RuleFamily.CEE,
            context="counter",
            target_object="contract",
            employment_regime_code="CEE",
            effective_date=date(2026, 1, 1),
            priority=10,
            parameters={
                "rolling_period_months": 12,
                "max_days": 80,
            },
        ),
        CalculationRule(
            code="PREPA_SPORT_1_3",
            label="Préparation éducateur sportif 1/3",
            family=RuleFamily.PREPARATION,
            context="assignment",
            target_object="assignment",
            effective_date=date(2026, 1, 1),
            priority=10,
            parameters={
                "population_code": "educateur_sportif",
                "coefficient": 0.3333,
                "base_calculation": "gross_duration",
            },
        ),
        CalculationRule(
            code="PREPA_LOISIRS_1_4",
            label="Préparation loisirs adultes 1/4",
            family=RuleFamily.PREPARATION,
            context="assignment",
            target_object="assignment",
            effective_date=date(2026, 1, 1),
            priority=20,
            parameters={
                "population_code": "animateur_loisirs_adultes",
                "coefficient": 0.25,
                "base_calculation": "gross_duration",
            },
        ),
    ]
