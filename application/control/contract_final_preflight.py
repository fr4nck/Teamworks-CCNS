from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from application.control.contract_compensation_preflight import ContractCompensationPreflight
from domain.contracts.cee_contract_guardrails import CEEContractGuardrailResult
from domain.contracts.contract_rules_preflight import (
    ContractPreflightSeverity,
    ContractRulesPreflightResult,
)


class ContractFinalPreflightSeverity(str, Enum):
    INFO = "INFO"
    REVIEW = "REVIEW"
    BLOCKING = "BLOCKING"


class ContractFinalPreflightDecision(str, Enum):
    OK = "OK"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class ContractFinalPreflightIssue:
    code: str
    severity: ContractFinalPreflightSeverity
    message: str


@dataclass(frozen=True, slots=True)
class ContractFinalPreflightResult:
    decision: ContractFinalPreflightDecision
    issues: tuple[ContractFinalPreflightIssue, ...]

    @property
    def can_finalize(self) -> bool:
        return self.decision is not ContractFinalPreflightDecision.BLOCKED

    @property
    def requires_review(self) -> bool:
        return self.decision is ContractFinalPreflightDecision.REVIEW

    def blocking_messages(self) -> tuple[str, ...]:
        return tuple(issue.message for issue in self.issues if issue.severity is ContractFinalPreflightSeverity.BLOCKING)

    def review_messages(self) -> tuple[str, ...]:
        return tuple(issue.message for issue in self.issues if issue.severity is ContractFinalPreflightSeverity.REVIEW)


class ContractFinalPreflightService:
    """Agrège les contrôles finaux sans dépendre de wxPython ni de GestionDB."""

    def evaluate(
        self,
        *,
        compensation: ContractCompensationPreflight,
        ccns_rules: Optional[ContractRulesPreflightResult] = None,
        cee_guardrails: Optional[CEEContractGuardrailResult] = None,
    ) -> ContractFinalPreflightResult:
        if type(compensation) is not ContractCompensationPreflight:
            raise TypeError("compensation doit être un ContractCompensationPreflight.")
        if ccns_rules is not None and type(ccns_rules) is not ContractRulesPreflightResult:
            raise TypeError("ccns_rules doit être un ContractRulesPreflightResult ou None.")
        if cee_guardrails is not None and type(cee_guardrails) is not CEEContractGuardrailResult:
            raise TypeError("cee_guardrails doit être un CEEContractGuardrailResult ou None.")

        issues: list[ContractFinalPreflightIssue] = []
        if not compensation.compliant:
            issues.append(
                ContractFinalPreflightIssue(
                    code="COMPENSATION_NON_COMPLIANT",
                    severity=ContractFinalPreflightSeverity.BLOCKING,
                    message=compensation.message,
                )
            )

        if ccns_rules is not None:
            severity_map = {
                ContractPreflightSeverity.INFO: ContractFinalPreflightSeverity.INFO,
                ContractPreflightSeverity.REVIEW: ContractFinalPreflightSeverity.REVIEW,
                ContractPreflightSeverity.BLOCKING: ContractFinalPreflightSeverity.BLOCKING,
            }
            for issue in ccns_rules.issues:
                # Le contrôle de rémunération est déjà injecté dans le préflight
                # final : ne pas afficher deux fois le même blocage.
                if issue.code == "COMPENSATION_NON_COMPLIANT":
                    continue
                issues.append(
                    ContractFinalPreflightIssue(
                        code=issue.code,
                        severity=severity_map[issue.severity],
                        message=issue.message,
                    )
                )

        if cee_guardrails is not None:
            if cee_guardrails.days_limit_compliant is False:
                issues.append(
                    ContractFinalPreflightIssue(
                        code="CEE_DEPASSEMENT_80_JOURS",
                        severity=ContractFinalPreflightSeverity.BLOCKING,
                        message="Le plafond de 80 jours CEE sur 12 mois consécutifs est dépassé.",
                    )
                )
            if cee_guardrails.average_hours_compliant is False:
                issues.append(
                    ContractFinalPreflightIssue(
                        code="CEE_MOYENNE_48H_DEPASSEE",
                        severity=ContractFinalPreflightSeverity.BLOCKING,
                        message="La moyenne de 48 h par semaine sur six mois, tous contrats confondus, est dépassée.",
                    )
                )
            if cee_guardrails.minor_daily_hours_compliant is False:
                issues.append(
                    ContractFinalPreflightIssue(
                        code="CEE_MINEUR_DEPASSEMENT_8H_JOUR",
                        severity=ContractFinalPreflightSeverity.BLOCKING,
                        message="Le planning d'un jeune travailleur dépasse 8 h de travail effectif par jour.",
                    )
                )
            if cee_guardrails.minor_weekly_hours_compliant is False:
                issues.append(
                    ContractFinalPreflightIssue(
                        code="CEE_MINEUR_DEPASSEMENT_35H_SEMAINE",
                        severity=ContractFinalPreflightSeverity.BLOCKING,
                        message="Le planning d'un jeune travailleur dépasse 35 h de travail effectif par semaine.",
                    )
                )
            if cee_guardrails.requires_review and not cee_guardrails.has_known_non_compliance:
                issues.append(
                    ContractFinalPreflightIssue(
                        code="CEE_GUARDRAILS_INCOMPLETE",
                        severity=ContractFinalPreflightSeverity.REVIEW,
                        message=(
                            "Certaines données CEE nécessaires au contrôle complet ne sont pas disponibles ; "
                            "le contrat peut être enregistré après revue, mais ne doit pas être présenté comme entièrement contrôlé."
                        ),
                    )
                )

        decision = ContractFinalPreflightDecision.OK
        if any(issue.severity is ContractFinalPreflightSeverity.BLOCKING for issue in issues):
            decision = ContractFinalPreflightDecision.BLOCKED
        elif any(issue.severity is ContractFinalPreflightSeverity.REVIEW for issue in issues):
            decision = ContractFinalPreflightDecision.REVIEW
        return ContractFinalPreflightResult(decision=decision, issues=tuple(issues))
