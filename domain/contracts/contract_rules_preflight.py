from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from domain.contracts.ccns_contract_mentions import ContractComplianceResult
from domain.convention.classification_rules import (
    ExceptionalHigherFunctionDecision,
    PermanentPolyvalenceDecision,
    PositionChangeDecision,
)
from domain.convention.part_time_planned_week import PartTimePlannedWeekResult
from domain.convention.seniority import CCNSSeniorityResult
from domain.convention.seniority_timeline import CCNSContractSeniorityTimelineResult


class ContractPreflightSeverity(str, Enum):
    INFO = "INFO"
    REVIEW = "REVIEW"
    BLOCKING = "BLOCKING"


class ContractPreflightDecision(str, Enum):
    OK = "OK"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class ContractPreflightIssue:
    code: str
    severity: ContractPreflightSeverity
    message: str
    source_reference: str = ""

    def __post_init__(self) -> None:
        if type(self.code) is not str or not self.code.strip():
            raise ValueError("code est obligatoire.")
        if type(self.severity) is not ContractPreflightSeverity:
            raise TypeError("severity doit être un ContractPreflightSeverity.")
        if type(self.message) is not str or not self.message.strip():
            raise ValueError("message est obligatoire.")
        if type(self.source_reference) is not str:
            raise TypeError("source_reference doit être une chaîne.")


@dataclass(frozen=True, slots=True)
class ContractRulesPreflightResult:
    decision: ContractPreflightDecision
    issues: tuple[ContractPreflightIssue, ...]
    seniority_timeline: CCNSContractSeniorityTimelineResult
    seniority: CCNSSeniorityResult
    mentions: ContractComplianceResult
    part_time_week: Optional[PartTimePlannedWeekResult]

    @property
    def can_finalize_contract(self) -> bool:
        return self.decision is not ContractPreflightDecision.BLOCKED

    @property
    def requires_review(self) -> bool:
        return self.decision is ContractPreflightDecision.REVIEW


class CCNSContractRulesPreflightService:
    """Agrège les décisions CCNS avant validation finale d'un contrat.

    Le service ne remplace pas les moteurs spécialisés. Il traduit leurs résultats
    en trois états simples pour l'application : OK, revue nécessaire, blocage.
    Une saisie temps partiel justifiée peut donc rester enregistrable tout en
    conservant une anomalie de conformité visible.
    """

    def evaluate(
        self,
        *,
        seniority_timeline: CCNSContractSeniorityTimelineResult,
        seniority: CCNSSeniorityResult,
        mentions: ContractComplianceResult,
        part_time_week: Optional[PartTimePlannedWeekResult] = None,
        compensation_compliant: Optional[bool] = None,
        compensation_message: str = "",
        position_change: Optional[PositionChangeDecision] = None,
        permanent_polyvalence: Optional[PermanentPolyvalenceDecision] = None,
        exceptional_higher_function: Optional[ExceptionalHigherFunctionDecision] = None,
    ) -> ContractRulesPreflightResult:
        if type(seniority_timeline) is not CCNSContractSeniorityTimelineResult:
            raise TypeError("seniority_timeline doit être un CCNSContractSeniorityTimelineResult.")
        if type(seniority) is not CCNSSeniorityResult:
            raise TypeError("seniority doit être un CCNSSeniorityResult.")
        if type(mentions) is not ContractComplianceResult:
            raise TypeError("mentions doit être un ContractComplianceResult.")
        if part_time_week is not None and type(part_time_week) is not PartTimePlannedWeekResult:
            raise TypeError("part_time_week doit être un PartTimePlannedWeekResult ou None.")
        if compensation_compliant is not None and type(compensation_compliant) is not bool:
            raise TypeError("compensation_compliant doit être un booléen ou None.")
        if type(compensation_message) is not str:
            raise TypeError("compensation_message doit être une chaîne.")

        issues: list[ContractPreflightIssue] = []

        if compensation_compliant is False:
            issues.append(
                ContractPreflightIssue(
                    code="COMPENSATION_NON_COMPLIANT",
                    severity=ContractPreflightSeverity.BLOCKING,
                    message=compensation_message.strip() or "La rémunération n'est pas conforme au minimum applicable.",
                )
            )
        elif compensation_compliant is None:
            issues.append(
                ContractPreflightIssue(
                    code="COMPENSATION_NOT_EVALUATED",
                    severity=ContractPreflightSeverity.REVIEW,
                    message="Le contrôle de rémunération n'a pas encore été exécuté.",
                )
            )

        if mentions.applicable:
            if mentions.missing_requirements:
                missing_labels = ", ".join(item.label for item in mentions.missing_requirements)
                issues.append(
                    ContractPreflightIssue(
                        code="MANDATORY_CONTRACT_MENTIONS_MISSING",
                        severity=ContractPreflightSeverity.BLOCKING,
                        message=f"Mentions contractuelles obligatoires manquantes : {missing_labels}.",
                    )
                )
            if mentions.unresolved_conditional_codes:
                issues.append(
                    ContractPreflightIssue(
                        code="CONDITIONAL_CONTRACT_MENTION_UNRESOLVED",
                        severity=ContractPreflightSeverity.BLOCKING,
                        message="Une condition nécessaire au contrôle des mentions contractuelles reste indéterminée.",
                    )
                )

        if seniority_timeline.prior_history_requires_review:
            issues.append(
                ContractPreflightIssue(
                    code="SENIORITY_PRIOR_HISTORY_UNCONFIRMED",
                    severity=ContractPreflightSeverity.REVIEW,
                    message=(
                        "L'ancienneté acquise pendant le contrat en cours est calculée, mais l'historique antérieur "
                        "n'a pas encore été explicitement reconnu."
                    ),
                    source_reference=seniority.source_reference,
                )
            )

        if seniority.applicable and seniority.monthly_due_amount > 0:
            issues.append(
                ContractPreflightIssue(
                    code="SENIORITY_PREMIUM_DUE",
                    severity=ContractPreflightSeverity.INFO,
                    message=(
                        f"Prime d'ancienneté calculée : {seniority.monthly_due_amount:.2f} € par mois "
                        f"({seniority.total_rate_percent:.2f} %)."
                    ),
                    source_reference=seniority.source_reference,
                )
            )

        if part_time_week is not None and not part_time_week.compliant:
            severity = (
                ContractPreflightSeverity.REVIEW
                if part_time_week.recording_allowed
                else ContractPreflightSeverity.BLOCKING
            )
            message = "La semaine planifiée n'est pas conforme aux limites du temps partiel."
            if part_time_week.manual_override_used:
                message += " La saisie reste enregistrable avec la justification fournie, sans être marquée conforme."
            else:
                message += " Une justification explicite est requise pour enregistrer la situation réelle."
            issues.append(
                ContractPreflightIssue(
                    code="PART_TIME_WEEK_NON_COMPLIANT",
                    severity=severity,
                    message=message,
                    source_reference="; ".join(part_time_week.source_references),
                )
            )

        if position_change is not None and position_change.reclassification_required:
            issues.append(
                ContractPreflightIssue(
                    code="CLASSIFICATION_RECLASSIFICATION_REQUIRED",
                    severity=ContractPreflightSeverity.BLOCKING,
                    message=(
                        f"Le poste évalué relève de {position_change.evaluated_group_code} : "
                        "le groupe du contrat doit être mis à jour."
                    ),
                    source_reference=position_change.source_reference,
                )
            )

        if permanent_polyvalence is not None and permanent_polyvalence.reclassification_required:
            issues.append(
                ContractPreflightIssue(
                    code="PERMANENT_POLYVALENCE_RECLASSIFICATION_REQUIRED",
                    severity=ContractPreflightSeverity.BLOCKING,
                    message=(
                        f"La polyvalence permanente impose le classement en {permanent_polyvalence.target_group_code}."
                    ),
                    source_reference=permanent_polyvalence.source_reference,
                )
            )

        if exceptional_higher_function is not None and exceptional_higher_function.premium_due:
            issues.append(
                ContractPreflightIssue(
                    code="EXCEPTIONAL_HIGHER_FUNCTION_PREMIUM_DUE",
                    severity=ContractPreflightSeverity.REVIEW,
                    message="Une prime de fonction supérieure est due pour la période contrôlée.",
                    source_reference=exceptional_higher_function.source_reference,
                )
            )

        decision = ContractPreflightDecision.OK
        if any(issue.severity is ContractPreflightSeverity.BLOCKING for issue in issues):
            decision = ContractPreflightDecision.BLOCKED
        elif any(issue.severity is ContractPreflightSeverity.REVIEW for issue in issues):
            decision = ContractPreflightDecision.REVIEW

        return ContractRulesPreflightResult(
            decision=decision,
            issues=tuple(issues),
            seniority_timeline=seniority_timeline,
            seniority=seniority,
            mentions=mentions,
            part_time_week=part_time_week,
        )
