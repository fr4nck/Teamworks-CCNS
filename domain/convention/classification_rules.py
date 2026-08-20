from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Optional


CCNS_CLASSIFICATION_CHOICE_SOURCE = "CCNS, article 9.1.1"
CCNS_POLYVALENCE_SOURCE = "CCNS, article 9.1.2"
CCNS_EXCEPTIONAL_HIGHER_FUNCTION_SOURCE = "CCNS, article 9.1.3"

_ZERO = Decimal("0.00")
_ONE = Decimal("1.00")
_POLYVALENCE_THRESHOLD = Decimal("0.20")
_ONE_WEEK = Decimal("1.00")


def _parse_group(group_code: str) -> int:
    if type(group_code) is not str:
        raise TypeError("group_code doit être une chaîne stricte.")
    normalized = group_code.strip().upper()
    if normalized.startswith("G"):
        normalized = normalized[1:]
    if not normalized.isdigit():
        raise ValueError("Le groupe CCNS doit être compris entre G1 et G8.")
    group = int(normalized)
    if not 1 <= group <= 8:
        raise ValueError("Le groupe CCNS doit être compris entre G1 et G8.")
    return group


def _canonical_group(group_code: str) -> str:
    return f"G{_parse_group(group_code)}"


@dataclass(frozen=True, slots=True)
class PositionChangeDecision:
    current_group_code: str
    evaluated_group_code: str
    position_definition_changed: bool
    remuneration_review_required: bool
    reclassification_required: bool
    specific_interview_and_report_required: bool
    source_reference: str = CCNS_CLASSIFICATION_CHOICE_SOURCE


@dataclass(frozen=True, slots=True)
class PermanentPolyvalenceDecision:
    current_group_code: str
    highest_activity_group_code: str
    highest_group_activity_ratio: Decimal
    threshold_ratio: Decimal
    reclassification_required: bool
    target_group_code: str
    source_reference: str = CCNS_POLYVALENCE_SOURCE


@dataclass(frozen=True, slots=True)
class ExceptionalHigherFunctionDecision:
    current_group_code: str
    temporary_group_code: str
    continuous_duration_weeks: Decimal
    higher_position_occupied_for_whole_period: bool
    premium_due: bool
    remuneration_difference_amount: Optional[Decimal]
    source_reference: str = CCNS_EXCEPTIONAL_HIGHER_FUNCTION_SOURCE


class CCNSClassificationRulesService:
    """Règles transversales de classification CCNS, indépendantes de l'UI.

    Le choix initial du groupe reste une évaluation métier fondée sur l'emploi
    réellement occupé (responsabilité, autonomie, technicité). Ce service ne
    remplace pas cette évaluation par un score arbitraire ; il automatise les
    conséquences explicites des articles 9.1.1 à 9.1.3.
    """

    def evaluate_position_change(
        self,
        *,
        current_group_code: str,
        evaluated_group_code: str,
        position_definition_changed: bool,
    ) -> PositionChangeDecision:
        current = _parse_group(current_group_code)
        evaluated = _parse_group(evaluated_group_code)
        if type(position_definition_changed) is not bool:
            raise TypeError("position_definition_changed doit être un booléen strict.")

        reclassification = position_definition_changed and evaluated > current
        return PositionChangeDecision(
            current_group_code=f"G{current}",
            evaluated_group_code=f"G{evaluated}",
            position_definition_changed=position_definition_changed,
            remuneration_review_required=position_definition_changed,
            reclassification_required=reclassification,
            specific_interview_and_report_required=position_definition_changed,
        )

    def evaluate_permanent_polyvalence(
        self,
        *,
        current_group_code: str,
        highest_activity_group_code: str,
        highest_group_activity_ratio: Decimal,
    ) -> PermanentPolyvalenceDecision:
        current = _parse_group(current_group_code)
        highest = _parse_group(highest_activity_group_code)
        if type(highest_group_activity_ratio) is not Decimal:
            raise TypeError("highest_group_activity_ratio doit être un Decimal strict.")
        if not _ZERO <= highest_group_activity_ratio <= _ONE:
            raise ValueError("highest_group_activity_ratio doit être compris entre 0 et 1.")

        # Le texte dit « dépassent 20 % » : exactement 20 % ne déclenche pas la règle.
        reclassification = highest > current and highest_group_activity_ratio > _POLYVALENCE_THRESHOLD
        target = highest if reclassification else current
        return PermanentPolyvalenceDecision(
            current_group_code=f"G{current}",
            highest_activity_group_code=f"G{highest}",
            highest_group_activity_ratio=highest_group_activity_ratio,
            threshold_ratio=_POLYVALENCE_THRESHOLD,
            reclassification_required=reclassification,
            target_group_code=f"G{target}",
        )

    def evaluate_exceptional_higher_function(
        self,
        *,
        current_group_code: str,
        temporary_group_code: str,
        continuous_duration_weeks: Decimal,
        higher_position_occupied_for_whole_period: bool,
        current_group_remuneration_reference: Optional[Decimal] = None,
        temporary_group_remuneration_reference: Optional[Decimal] = None,
    ) -> ExceptionalHigherFunctionDecision:
        current = _parse_group(current_group_code)
        temporary = _parse_group(temporary_group_code)
        if type(continuous_duration_weeks) is not Decimal:
            raise TypeError("continuous_duration_weeks doit être un Decimal strict.")
        if continuous_duration_weeks < _ZERO:
            raise ValueError("continuous_duration_weeks ne peut pas être négatif.")
        if type(higher_position_occupied_for_whole_period) is not bool:
            raise TypeError("higher_position_occupied_for_whole_period doit être un booléen strict.")
        for name, value in (
            ("current_group_remuneration_reference", current_group_remuneration_reference),
            ("temporary_group_remuneration_reference", temporary_group_remuneration_reference),
        ):
            if value is not None and type(value) is not Decimal:
                raise TypeError(f"{name} doit être un Decimal strict ou None.")
            if value is not None and value < _ZERO:
                raise ValueError(f"{name} ne peut pas être négatif.")

        premium_due = (
            temporary > current
            and continuous_duration_weeks >= _ONE_WEEK
            and higher_position_occupied_for_whole_period
        )
        difference = None
        if premium_due and current_group_remuneration_reference is not None and temporary_group_remuneration_reference is not None:
            with localcontext() as ctx:
                ctx.prec = 28
                difference = max(
                    temporary_group_remuneration_reference - current_group_remuneration_reference,
                    _ZERO,
                )

        return ExceptionalHigherFunctionDecision(
            current_group_code=f"G{current}",
            temporary_group_code=f"G{temporary}",
            continuous_duration_weeks=continuous_duration_weeks,
            higher_position_occupied_for_whole_period=higher_position_occupied_for_whole_period,
            premium_due=premium_due,
            remuneration_difference_amount=difference,
        )
