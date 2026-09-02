"""Contrat métier reçu par le domaine RH pour le réalisé d'une séance.

Ce module valide uniquement le message inter-domaines. Il ne modifie ni le
planning prévisionnel, ni un contrat de travail, ni la paie.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from typing import Any, Mapping, Optional


SOURCE_DOMAIN = "operations_portal"
CONTRACT_VERSION = "session-actual/1"
EVENT_TYPE = "session_actual_validated"
ACCEPTED_STATUSES = frozenset(("realisee", "annulee"))


class SessionActualContractError(ValueError):
    """Message de réalisé invalide ou incompatible avec le contrat supporté."""


def _required_text(value: Any, field_name: str, maximum: int) -> str:
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise SessionActualContractError(f"{field_name} obligatoire")
    if len(normalized) > maximum or any(ord(character) < 32 for character in normalized):
        raise SessionActualContractError(f"{field_name} invalide")
    return normalized


def _optional_text(value: Any, field_name: str, maximum: int) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SessionActualContractError(f"{field_name} invalide")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > maximum or any(ord(character) < 32 for character in normalized):
        raise SessionActualContractError(f"{field_name} invalide")
    return normalized


def _strict_date(value: Any, field_name: str) -> date:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value
    value = _required_text(value, field_name, 10)
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise SessionActualContractError(f"{field_name} invalide") from error


def _optional_time(value: Any, field_name: str) -> Optional[str]:
    if value in (None, ""):
        return None
    value = _required_text(value, field_name, 5)
    try:
        return datetime.strptime(value, "%H:%M").strftime("%H:%M")
    except ValueError as error:
        raise SessionActualContractError(f"{field_name} invalide") from error


def _positive_revision(value: Any) -> int:
    try:
        revision = int(value)
    except (TypeError, ValueError) as error:
        raise SessionActualContractError("actual_revision invalide") from error
    if revision < 1:
        raise SessionActualContractError("actual_revision invalide")
    return revision


def _duration_minutes(start_time: str, end_time: str) -> int:
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    minutes = int((end - start).total_seconds() // 60)
    if minutes <= 0:
        raise SessionActualContractError("actual_end_time doit être postérieure à actual_start_time")
    return minutes


@dataclass(frozen=True, slots=True)
class SessionActual:
    """Vue RH immuable d'un réalisé validé dans le domaine opérations."""

    actual_uuid: str
    actual_revision: int
    session_uid: str
    session_status: str
    assignment_date: date
    validated_at: str
    actual_staff_uid: Optional[str]
    actual_place_uid: Optional[str]
    actual_start_time: Optional[str]
    actual_end_time: Optional[str]
    actual_duration_minutes: Optional[int]
    actual_comment: Optional[str]
    contract_version: str = CONTRACT_VERSION
    event_type: str = EVENT_TYPE

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "SessionActual":
        if not isinstance(payload, Mapping):
            raise SessionActualContractError("payload invalide")

        contract_version = _required_text(payload.get("contract_version"), "contract_version", 64)
        if contract_version != CONTRACT_VERSION:
            raise SessionActualContractError("version de contrat non supportée")

        event_type = _required_text(payload.get("event_type"), "event_type", 64)
        if event_type != EVENT_TYPE:
            raise SessionActualContractError("type d'événement non supporté")

        actual_uuid = _required_text(payload.get("actual_uuid"), "actual_uuid", 64)
        session_uid = _required_text(payload.get("session_uid"), "session_uid", 128)
        revision = _positive_revision(payload.get("actual_revision"))
        status = _required_text(payload.get("session_status"), "session_status", 32)
        if status not in ACCEPTED_STATUSES:
            raise SessionActualContractError("session_status doit être realisee ou annulee")

        assignment_date = _strict_date(payload.get("assignment_date"), "assignment_date")
        validated_at = _required_text(payload.get("validated_at"), "validated_at", 64)
        staff_uid = _optional_text(payload.get("actual_staff_uid"), "actual_staff_uid", 100)
        place_uid = _optional_text(payload.get("actual_place_uid"), "actual_place_uid", 128)
        start_time = _optional_time(payload.get("actual_start_time"), "actual_start_time")
        end_time = _optional_time(payload.get("actual_end_time"), "actual_end_time")
        comment = _optional_text(payload.get("actual_comment"), "actual_comment", 2000)
        duration = payload.get("actual_duration_minutes")

        if status == "realisee":
            if staff_uid is None:
                raise SessionActualContractError("actual_staff_uid obligatoire pour une séance réalisée")
            if start_time is None or end_time is None:
                raise SessionActualContractError("horaires réels obligatoires pour une séance réalisée")
            try:
                duration = int(duration)
            except (TypeError, ValueError) as error:
                raise SessionActualContractError("actual_duration_minutes invalide") from error
            if duration != _duration_minutes(start_time, end_time):
                raise SessionActualContractError("durée réelle incohérente avec les horaires")
        else:
            if any(value is not None for value in (staff_uid, place_uid, start_time, end_time)) or duration not in (None, ""):
                raise SessionActualContractError(
                    "une séance annulée ne porte ni intervenant, ni lieu, ni horaires réels"
                )
            if comment is None:
                raise SessionActualContractError("actual_comment obligatoire pour une séance annulée")
            duration = None

        return cls(
            contract_version=contract_version,
            event_type=event_type,
            actual_uuid=actual_uuid,
            actual_revision=revision,
            session_uid=session_uid,
            session_status=status,
            assignment_date=assignment_date,
            validated_at=validated_at,
            actual_staff_uid=staff_uid,
            actual_place_uid=place_uid,
            actual_start_time=start_time,
            actual_end_time=end_time,
            actual_duration_minutes=duration,
            actual_comment=comment,
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "event_type": self.event_type,
            "actual_uuid": self.actual_uuid,
            "actual_revision": self.actual_revision,
            "session_uid": self.session_uid,
            "session_status": self.session_status,
            "assignment_date": self.assignment_date.isoformat(),
            "validated_at": self.validated_at,
            "actual_staff_uid": self.actual_staff_uid,
            "actual_place_uid": self.actual_place_uid,
            "actual_start_time": self.actual_start_time,
            "actual_end_time": self.actual_end_time,
            "actual_duration_minutes": self.actual_duration_minutes,
            "actual_comment": self.actual_comment,
        }

    def payload_sha256(self) -> str:
        serialized = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
