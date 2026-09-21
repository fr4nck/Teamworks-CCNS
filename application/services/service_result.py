"""Résultats structurés communs des services applicatifs.

Ce module ne dépend ni d'un toolkit UI ni d'un moteur SQL. Il distingue :
- les erreurs globales d'une opération ;
- les incidents propres à certains éléments d'un batch ;
- l'état réel du commit, y compris après une erreur de readback.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


class ServiceErrorCode(str, Enum):
    INVALID_TARGET_ID = "INVALID_TARGET_ID"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"

    OVERLAP_CONFLICT = "OVERLAP_CONFLICT"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"

    UNEXPECTED_ROWCOUNT = "UNEXPECTED_ROWCOUNT"
    DATABASE_ERROR = "DATABASE_ERROR"
    READBACK_ERROR = "READBACK_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class BatchDisposition(str, Enum):
    SKIPPED = "SKIPPED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ServiceError:
    """Erreur structurée exposée à la couche de présentation.

    message est affichable à l'utilisateur.
    diagnostic est réservé aux logs techniques.
    """

    code: ServiceErrorCode
    message: str
    field: Optional[str] = None
    target_id: Optional[int] = None
    conflicting_target_id: Optional[int] = None
    expected_revision: Optional[str] = None
    actual_revision: Optional[str] = None
    retryable: bool = False
    diagnostic: Optional[str] = None


@dataclass(frozen=True)
class BatchItemRef:
    """Référence d'un élément demandé dans une opération de lot."""

    index: int
    target_id: Optional[int] = None
    person_id: Optional[int] = None
    presence_date: Optional[date] = None


@dataclass(frozen=True)
class BatchIssue:
    """Incident métier propre à un élément d'un lot."""

    item: BatchItemRef
    disposition: BatchDisposition
    error: ServiceError


@dataclass(frozen=True)
class BatchReport:
    """Bilan exhaustif d'une opération batch terminée."""

    requested_count: int
    succeeded_count: int
    skipped_count: int = 0
    rejected_count: int = 0
    issues: tuple[BatchIssue, ...] = ()

    def __post_init__(self) -> None:
        counters = (
            self.requested_count,
            self.succeeded_count,
            self.skipped_count,
            self.rejected_count,
        )
        if any(value < 0 for value in counters):
            raise ValueError("Les compteurs batch ne peuvent pas être négatifs.")

        accounted = (
            self.succeeded_count
            + self.skipped_count
            + self.rejected_count
        )
        if accounted != self.requested_count:
            raise ValueError(
                "Le bilan batch doit comptabiliser exactement tous les éléments."
            )

        if len(self.issues) != self.skipped_count + self.rejected_count:
            raise ValueError(
                "Chaque élément ignoré ou rejeté doit posséder un BatchIssue."
            )


@dataclass(frozen=True)
class ServiceResult(Generic[T]):
    """Résultat unique d'un service applicatif.

    Un succès ne porte aucune erreur.
    Un échec porte obligatoirement une ServiceError.
    committed=True signifie qu'un commit est déjà confirmé.
    batch décrit seulement les incidents élémentaires d'un lot terminé.
    """

    ok: bool
    value: Optional[T] = None
    error: Optional[ServiceError] = None
    target_id: Optional[int] = None
    committed: bool = False
    batch: Optional[BatchReport] = None

    def __post_init__(self) -> None:
        if self.ok and self.error is not None:
            raise ValueError(
                "Un ServiceResult réussi ne peut pas contenir ServiceError."
            )
        if not self.ok and self.error is None:
            raise ValueError(
                "Un ServiceResult en échec doit contenir ServiceError."
            )

    @property
    def code(self) -> str:
        """Compatibilité transitoire avec l'ancien WriteResult."""
        if self.ok:
            return "OK"
        assert self.error is not None
        return self.error.code.value

    @property
    def message(self) -> str:
        """Compatibilité transitoire avec l'ancien WriteResult."""
        if self.error is None:
            return ""
        return self.error.message

    @classmethod
    def success(
        cls,
        *,
        value: Optional[T] = None,
        target_id: Optional[int] = None,
        committed: bool = False,
        batch: Optional[BatchReport] = None,
    ) -> "ServiceResult[T]":
        return cls(
            ok=True,
            value=value,
            target_id=target_id,
            committed=committed,
            batch=batch,
        )

    @classmethod
    def failure(
        cls,
        *,
        error: ServiceError,
        target_id: Optional[int] = None,
        committed: bool = False,
        batch: Optional[BatchReport] = None,
    ) -> "ServiceResult[T]":
        return cls(
            ok=False,
            error=error,
            target_id=target_id,
            committed=committed,
            batch=batch,
        )
