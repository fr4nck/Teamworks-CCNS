"""Contrat commun des lectures applicatives.

Une lecture ne possède jamais d'état de commit. Elle expose uniquement :
- sa complétude ;
- les sources qui ont échoué ou été dégradées ;
- une politique de retry sûre pour une opération idempotente ;
- une priorité stable permettant à l'UI de choisir l'incident principal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


class ReadCompleteness(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ReadIssueCode(str, Enum):
    INVALID_QUERY = "INVALID_QUERY"
    OPTIONAL_SOURCE_UNAVAILABLE = "OPTIONAL_SOURCE_UNAVAILABLE"
    REQUIRED_SOURCE_UNAVAILABLE = "REQUIRED_SOURCE_UNAVAILABLE"
    SOURCE_DATA_INVALID = "SOURCE_DATA_INVALID"
    SOURCE_MAPPING_FAILED = "SOURCE_MAPPING_FAILED"
    INTERNAL_READ_ERROR = "INTERNAL_READ_ERROR"


class ReadSourceRequirement(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


class ReadRetryPolicy(str, Enum):
    """Politique de nouvelle tentative pour une lecture idempotente."""

    NEVER = "NEVER"
    AUTOMATIC_ONCE = "AUTOMATIC_ONCE"
    USER_ACTION = "USER_ACTION"


@dataclass(frozen=True)
class ReadIssue:
    code: ReadIssueCode
    message: str
    source: Optional[str] = None
    requirement: ReadSourceRequirement = ReadSourceRequirement.REQUIRED
    retry_policy: ReadRetryPolicy = ReadRetryPolicy.NEVER
    diagnostic: Optional[str] = None

    @property
    def blocking(self) -> bool:
        return self.requirement is ReadSourceRequirement.REQUIRED

    @property
    def priority(self) -> int:
        """Priorité d'affichage : valeur haute = incident plus important."""

        if self.code is ReadIssueCode.INTERNAL_READ_ERROR:
            return 100
        if self.code is ReadIssueCode.INVALID_QUERY:
            return 95
        if self.code is ReadIssueCode.REQUIRED_SOURCE_UNAVAILABLE:
            return 90
        if self.requirement is ReadSourceRequirement.REQUIRED:
            if self.code is ReadIssueCode.SOURCE_DATA_INVALID:
                return 80
            if self.code is ReadIssueCode.SOURCE_MAPPING_FAILED:
                return 75
        if self.code is ReadIssueCode.OPTIONAL_SOURCE_UNAVAILABLE:
            return 40
        if self.code is ReadIssueCode.SOURCE_DATA_INVALID:
            return 35
        if self.code is ReadIssueCode.SOURCE_MAPPING_FAILED:
            return 30
        return 0


@dataclass(frozen=True)
class ReadResult(Generic[T]):
    completeness: ReadCompleteness
    value: Optional[T] = None
    issues: tuple[ReadIssue, ...] = ()

    def __post_init__(self) -> None:
        if self.completeness is ReadCompleteness.COMPLETE:
            if self.issues:
                raise ValueError(
                    "Une lecture COMPLETE ne peut pas contenir d'incident."
                )
            if self.value is None:
                raise ValueError(
                    "Une lecture COMPLETE doit fournir une valeur, même vide."
                )

        if self.completeness is ReadCompleteness.PARTIAL:
            if self.value is None:
                raise ValueError(
                    "Une lecture PARTIAL doit fournir les données disponibles."
                )
            if not self.issues:
                raise ValueError(
                    "Une lecture PARTIAL doit expliquer sa dégradation."
                )
            if any(issue.blocking for issue in self.issues):
                raise ValueError(
                    "Une lecture PARTIAL ne peut pas contenir d'incident bloquant."
                )

        if self.completeness is ReadCompleteness.FAILED:
            if self.value is not None:
                raise ValueError(
                    "Une lecture FAILED ne doit pas exposer de snapshot exploitable."
                )
            if not self.issues:
                raise ValueError(
                    "Une lecture FAILED doit exposer au moins un incident."
                )
            if not any(issue.blocking for issue in self.issues):
                raise ValueError(
                    "Une lecture FAILED doit contenir au moins un incident bloquant."
                )

    @property
    def ok(self) -> bool:
        return self.completeness is not ReadCompleteness.FAILED

    @property
    def partial(self) -> bool:
        return self.completeness is ReadCompleteness.PARTIAL

    @property
    def primary_issue(self) -> Optional[ReadIssue]:
        """Incident principal choisi de manière stable pour l'UI."""

        if not self.issues:
            return None
        return sorted(
            self.issues,
            key=lambda issue: (
                -issue.priority,
                issue.source or "",
                issue.code.value,
            ),
        )[0]

    @property
    def automatic_retry_allowed(self) -> bool:
        """Indique qu'une source autorise une tentative automatique."""

        return any(
            issue.retry_policy is ReadRetryPolicy.AUTOMATIC_ONCE
            for issue in self.issues
        )

    def should_retry_automatically(self, attempts_already_made: int) -> bool:
        """Autorise au maximum une nouvelle tentative automatique.

        attempts_already_made compte les retries déjà effectués, pas la lecture
        initiale. Avec AUTOMATIC_ONCE : 0 => oui, 1 ou plus => non.
        """

        if attempts_already_made < 0:
            raise ValueError("Le nombre de retries déjà effectués est invalide.")
        return (
            attempts_already_made == 0
            and self.automatic_retry_allowed
        )

    @property
    def user_retry_allowed(self) -> bool:
        return any(
            issue.retry_policy in (
                ReadRetryPolicy.AUTOMATIC_ONCE,
                ReadRetryPolicy.USER_ACTION,
            )
            for issue in self.issues
        )

    @classmethod
    def complete(cls, value: T) -> "ReadResult[T]":
        return cls(
            completeness=ReadCompleteness.COMPLETE,
            value=value,
        )

    @classmethod
    def partial_result(
        cls,
        *,
        value: T,
        issues: tuple[ReadIssue, ...],
    ) -> "ReadResult[T]":
        return cls(
            completeness=ReadCompleteness.PARTIAL,
            value=value,
            issues=issues,
        )

    @classmethod
    def failed(
        cls,
        *,
        issues: tuple[ReadIssue, ...],
    ) -> "ReadResult[T]":
        return cls(
            completeness=ReadCompleteness.FAILED,
            issues=issues,
        )


def optional_source_unavailable(
    *,
    source: str,
    message: str,
    diagnostic: Optional[str] = None,
    retry_policy: ReadRetryPolicy = ReadRetryPolicy.AUTOMATIC_ONCE,
) -> ReadIssue:
    return ReadIssue(
        code=ReadIssueCode.OPTIONAL_SOURCE_UNAVAILABLE,
        message=message,
        source=source,
        requirement=ReadSourceRequirement.OPTIONAL,
        retry_policy=retry_policy,
        diagnostic=diagnostic,
    )


def required_source_unavailable(
    *,
    source: str,
    message: str,
    diagnostic: Optional[str] = None,
    retry_policy: ReadRetryPolicy = ReadRetryPolicy.AUTOMATIC_ONCE,
) -> ReadIssue:
    return ReadIssue(
        code=ReadIssueCode.REQUIRED_SOURCE_UNAVAILABLE,
        message=message,
        source=source,
        requirement=ReadSourceRequirement.REQUIRED,
        retry_policy=retry_policy,
        diagnostic=diagnostic,
    )
