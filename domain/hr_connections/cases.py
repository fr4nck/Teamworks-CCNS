from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from enum import Enum
from typing import FrozenSet, Iterable


class HrCaseSubjectKind(str, Enum):
    """Nature de l'objet métier concerné par une démarche RH."""

    PERSON = "person"
    STRUCTURE = "structure"


@dataclass(frozen=True)
class HrCaseSubject:
    """Référence métier légère vers la personne ou la structure concernée."""

    kind: HrCaseSubjectKind
    identifier: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, HrCaseSubjectKind):
            raise TypeError("La nature du sujet du dossier RH est invalide.")
        if not self.identifier.strip():
            raise ValueError("L'identifiant du sujet du dossier RH est obligatoire.")

    @classmethod
    def create(cls, *, kind: HrCaseSubjectKind, identifier: str) -> "HrCaseSubject":
        return cls(kind=kind, identifier=identifier.strip())


@dataclass(frozen=True)
class HrCaseType:
    """Type extensible de démarche RH, identifié par un code stable."""

    code: str
    label: str

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Le code du type de démarche RH est obligatoire.")
        if not self.label.strip():
            raise ValueError("Le libellé du type de démarche RH est obligatoire.")

    @classmethod
    def create(cls, *, code: str, label: str) -> "HrCaseType":
        return cls(code=code.strip(), label=label.strip())


@dataclass(frozen=True)
class ExpectedDocument:
    """Pièce attendue pour instruire une démarche, sans contenir le document lui-même."""

    code: str
    label: str
    required: bool = True

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Le code de la pièce attendue est obligatoire.")
        if not self.label.strip():
            raise ValueError("Le libellé de la pièce attendue est obligatoire.")
        if not isinstance(self.required, bool):
            raise TypeError("Le caractère obligatoire d'une pièce attendue doit être booléen.")

    @classmethod
    def create(
        cls,
        *,
        code: str,
        label: str,
        required: bool = True,
    ) -> "ExpectedDocument":
        return cls(code=code.strip(), label=label.strip(), required=required)


class HrCaseStatus(str, Enum):
    """État métier d'une démarche RH."""

    TODO = "todo"
    PREPARED = "prepared"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    ANOMALY = "anomaly"
    REGULARIZATION = "regularization"
    CANCELLED = "cancelled"


class ExchangeStatus(str, Enum):
    """État technique d'un éventuel échange, distinct du statut métier."""

    NOT_APPLICABLE = "not_applicable"
    NOT_STARTED = "not_started"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[HrCaseStatus, FrozenSet[HrCaseStatus]] = {
    HrCaseStatus.TODO: frozenset({HrCaseStatus.PREPARED, HrCaseStatus.CANCELLED}),
    HrCaseStatus.PREPARED: frozenset(
        {HrCaseStatus.TODO, HrCaseStatus.SUBMITTED, HrCaseStatus.CANCELLED}
    ),
    HrCaseStatus.SUBMITTED: frozenset(
        {HrCaseStatus.ACCEPTED, HrCaseStatus.ANOMALY, HrCaseStatus.CANCELLED}
    ),
    HrCaseStatus.ANOMALY: frozenset(
        {HrCaseStatus.REGULARIZATION, HrCaseStatus.CANCELLED}
    ),
    HrCaseStatus.REGULARIZATION: frozenset(
        {
            HrCaseStatus.SUBMITTED,
            HrCaseStatus.ACCEPTED,
            HrCaseStatus.ANOMALY,
            HrCaseStatus.CANCELLED,
        }
    ),
    HrCaseStatus.ACCEPTED: frozenset(),
    HrCaseStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class HrCase:
    """Dossier de démarche RH indépendant de l'interface et de la persistance.

    Le statut métier décrit l'avancement administratif du dossier. Le statut
    technique décrit uniquement un éventuel échange automatisé. Les deux axes ne
    doivent jamais être confondus : un transfert technique réussi ne signifie pas
    qu'un organisme a accepté la démarche.
    """

    case_id: str
    case_type: HrCaseType
    subject: HrCaseSubject
    organization_code: str
    opened_on: date
    due_on: date | None = None
    status: HrCaseStatus = HrCaseStatus.TODO
    exchange_status: ExchangeStatus = ExchangeStatus.NOT_APPLICABLE
    expected_documents: FrozenSet[ExpectedDocument] = field(default_factory=frozenset)
    source: str | None = None
    result: str | None = None
    comment: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("L'identifiant du dossier RH est obligatoire.")
        if not isinstance(self.case_type, HrCaseType):
            raise TypeError("Le type de démarche RH est invalide.")
        if not isinstance(self.subject, HrCaseSubject):
            raise TypeError("Le sujet du dossier RH est invalide.")
        if not self.organization_code.strip():
            raise ValueError("Le code de l'organisme est obligatoire.")
        if not isinstance(self.opened_on, date):
            raise TypeError("La date d'ouverture du dossier RH est invalide.")
        if self.due_on is not None and not isinstance(self.due_on, date):
            raise TypeError("L'échéance du dossier RH est invalide.")
        if self.due_on is not None and self.due_on < self.opened_on:
            raise ValueError("L'échéance ne peut pas précéder l'ouverture du dossier RH.")
        if not isinstance(self.status, HrCaseStatus):
            raise TypeError("Le statut métier du dossier RH est invalide.")
        if not isinstance(self.exchange_status, ExchangeStatus):
            raise TypeError("Le statut technique du dossier RH est invalide.")
        if any(not isinstance(item, ExpectedDocument) for item in self.expected_documents):
            raise TypeError("La liste des pièces attendues du dossier RH est invalide.")
        document_codes = tuple(item.code for item in self.expected_documents)
        if len(document_codes) != len(set(document_codes)):
            raise ValueError("Deux pièces attendues ne peuvent pas partager le même code.")

    @classmethod
    def create(
        cls,
        *,
        case_id: str,
        case_type: HrCaseType,
        subject: HrCaseSubject,
        organization_code: str,
        opened_on: date,
        due_on: date | None = None,
        expected_documents: Iterable[ExpectedDocument] = (),
        source: str | None = None,
        comment: str | None = None,
    ) -> "HrCase":
        normalized_source = source.strip() if source is not None else None
        normalized_comment = comment.strip() if comment is not None else None
        return cls(
            case_id=case_id.strip(),
            case_type=case_type,
            subject=subject,
            organization_code=organization_code.strip(),
            opened_on=opened_on,
            due_on=due_on,
            expected_documents=frozenset(expected_documents),
            source=normalized_source or None,
            comment=normalized_comment or None,
        )

    @property
    def is_closed(self) -> bool:
        return self.status in {HrCaseStatus.ACCEPTED, HrCaseStatus.CANCELLED}

    def is_overdue(self, *, as_of: date) -> bool:
        return self.due_on is not None and not self.is_closed and self.due_on < as_of

    def can_transition_to(self, status: HrCaseStatus) -> bool:
        if not isinstance(status, HrCaseStatus):
            return False
        return status in _ALLOWED_TRANSITIONS[self.status]

    def transition_to(
        self,
        status: HrCaseStatus,
        *,
        result: str | None = None,
        comment: str | None = None,
    ) -> "HrCase":
        if not isinstance(status, HrCaseStatus):
            raise TypeError("Le statut métier du dossier RH est invalide.")
        if not self.can_transition_to(status):
            raise ValueError(
                f"Transition de dossier RH interdite : {self.status.value} -> {status.value}."
            )

        normalized_result = result.strip() if result is not None else self.result
        normalized_comment = comment.strip() if comment is not None else self.comment
        return replace(
            self,
            status=status,
            result=normalized_result or None,
            comment=normalized_comment or None,
        )

    def with_exchange_status(self, status: ExchangeStatus) -> "HrCase":
        if not isinstance(status, ExchangeStatus):
            raise TypeError("Le statut technique du dossier RH est invalide.")
        return replace(self, exchange_status=status)
