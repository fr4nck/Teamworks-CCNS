from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum


class HrCaseDocumentState(str, Enum):
    """État administratif d'une pièce attendue, sans jugement de conformité."""

    RECEIVED = "received"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True)
class HrCaseDocumentReceipt:
    """Trace courante de réception d'une pièce attendue d'une démarche RH.

    L'objet indique uniquement qu'une pièce a été enregistrée comme reçue, puis
    éventuellement retirée du suivi. Il ne signifie ni authenticité, ni validité,
    ni conformité juridique. ``artifact_ref`` est une référence opaque facultative
    vers un document géré ailleurs ; aucun contenu binaire ni chemin local n'est
    porté par ce modèle.
    """

    case_id: str
    document_code: str
    state: HrCaseDocumentState
    received_on: date
    withdrawn_on: date | None = None
    artifact_ref: str | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.case_id, "L'identifiant de la démarche RH est obligatoire.")
        _required_text(self.document_code, "Le code de la pièce RH est obligatoire.")
        if not isinstance(self.state, HrCaseDocumentState):
            raise TypeError("L'état administratif de la pièce RH est invalide.")
        if not isinstance(self.received_on, date):
            raise TypeError("La date de réception de la pièce RH est invalide.")
        if self.withdrawn_on is not None and not isinstance(self.withdrawn_on, date):
            raise TypeError("La date de retrait de la pièce RH est invalide.")
        if self.state is HrCaseDocumentState.RECEIVED and self.withdrawn_on is not None:
            raise ValueError("Une pièce reçue ne peut pas porter de date de retrait.")
        if self.state is HrCaseDocumentState.WITHDRAWN and self.withdrawn_on is None:
            raise ValueError("Une pièce retirée doit porter une date de retrait.")
        if self.withdrawn_on is not None and self.withdrawn_on < self.received_on:
            raise ValueError("La date de retrait ne peut pas précéder la réception de la pièce RH.")
        _optional_text(self.artifact_ref, "La référence documentaire de la pièce RH est invalide.")
        _optional_text(self.source, "La provenance de la pièce RH est invalide.")

    @classmethod
    def received(
        cls,
        *,
        case_id: str,
        document_code: str,
        received_on: date,
        artifact_ref: str | None = None,
        source: str | None = None,
    ) -> "HrCaseDocumentReceipt":
        return cls(
            case_id=_required_text(
                case_id,
                "L'identifiant de la démarche RH est obligatoire.",
            ),
            document_code=_required_text(
                document_code,
                "Le code de la pièce RH est obligatoire.",
            ),
            state=HrCaseDocumentState.RECEIVED,
            received_on=received_on,
            artifact_ref=_optional_text(
                artifact_ref,
                "La référence documentaire de la pièce RH est invalide.",
            ),
            source=_optional_text(
                source,
                "La provenance de la pièce RH est invalide.",
            ),
        )

    def withdraw(self, *, withdrawn_on: date) -> "HrCaseDocumentReceipt":
        if self.state is not HrCaseDocumentState.RECEIVED:
            raise ValueError("Seule une pièce actuellement reçue peut être retirée du suivi.")
        if not isinstance(withdrawn_on, date):
            raise TypeError("La date de retrait de la pièce RH est invalide.")
        if withdrawn_on < self.received_on:
            raise ValueError("La date de retrait ne peut pas précéder la réception de la pièce RH.")
        return replace(
            self,
            state=HrCaseDocumentState.WITHDRAWN,
            withdrawn_on=withdrawn_on,
        )

    @property
    def is_received(self) -> bool:
        return self.state is HrCaseDocumentState.RECEIVED


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


def _optional_text(value: str | None, message: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(message)
    return value.strip() or None
