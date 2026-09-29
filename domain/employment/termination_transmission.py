"""Transmission à Impact Emploi : payload canonique et snapshots immuables (SORTIE-003).

Un snapshot est la trace de ce que Teamworks *affirme avoir communiqué* à
Impact Emploi, quand, par qui et par quel canal. Il ne prouve ni la réception,
ni l'acceptation par Impact Emploi, ni une DSN, un FCTU ou une AER.

Contrôle RH et contenu transmis sont distincts : ``HrInputChecks`` dit si des
éléments existent (UNKNOWN / NONE / PROVIDED) ; ``CommunicatedHrItem`` décrit,
en texte, ce qui a réellement été communiqué pour une catégorie PROVIDED.
Aucun montant ni donnée de paie n'est fabriqué ou calculé ici.

Il n'existe pas de snapshot « préparé » persisté : un snapshot n'est créé qu'au
moment où l'on enregistre une communication déjà effectuée. La prévisualisation
se fait avec ``build_transmission_payload`` sans rien écrire.

Format canonique (``CANONICAL_FORMAT``) :

- JSON UTF-8, clés triées, séparateurs ``,`` et ``:``, sans espace ni NaN ;
- caractères non ASCII écrits tels quels (pas d'échappement ``\\uXXXX``) ;
- toutes les chaînes normalisées en Unicode NFC ;
- dates ``AAAA-MM-JJ`` ; datetimes en UTC ``AAAA-MM-JJTHH:MM:SSZ`` (seconde) ;
- énumérations par leur valeur ; ``None`` -> ``null`` ; booléens JSON ;
- les flottants sont refusés ; les éléments RH sont triés (catégorie, texte).

Le hash est le SHA-256 (hex minuscule) des octets UTF-8 exacts du payload.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Iterable, Mapping, Optional
from uuid import uuid4

from domain.employment.termination import (
    CheckState,
    ContractTermination,
    TerminationDomainError,
)

PAYLOAD_SCHEMA = "teamworks.termination-transmission.v1"
CANONICAL_FORMAT = "json-utf8-nfc-sorted-compact.v1"
HR_CATEGORIES = ("hours", "absences", "leave", "variable_pay", "exceptional_items")
HR_ITEM_MAX_LENGTH = 2000
EXTERNAL_REFERENCE_MAX_LENGTH = 255
ACTOR_MAX_LENGTH = 128
COMMAND_ID_MAX_LENGTH = 128


class TransmissionChannel(str, Enum):
    MANUAL = "MANUAL"
    EMAIL = "EMAIL"
    PORTAL = "PORTAL"
    OTHER = "OTHER"


# --------------------------------------------------------------------------
# Canonicalisation et hash
# --------------------------------------------------------------------------

def _utc_seconds(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise TerminationDomainError("TIMESTAMP_TIMEZONE_REQUIRED", "timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _canonical_value(value: object) -> object:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, Enum):
        return _canonical_value(value.value)
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise TerminationDomainError("CANONICAL_FLOAT_FORBIDDEN", "floats are not canonical")
    if isinstance(value, datetime):
        return _utc_seconds(value).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TerminationDomainError("CANONICAL_KEY_NOT_STRING", "mapping keys must be strings")
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in result:
                raise TerminationDomainError("CANONICAL_DUPLICATE_KEY", f"duplicate key {normalized_key!r}")
            result[normalized_key] = _canonical_value(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    raise TerminationDomainError(
        "CANONICAL_TYPE_FORBIDDEN", f"type {type(value).__name__} has no canonical form"
    )


def canonical_json(value: object) -> str:
    try:
        text = json.dumps(
            _canonical_value(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise TerminationDomainError("CANONICAL_INVALID_UNICODE", "payload is not valid UTF-8 text") from None
    return text


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Contenu RH réellement communiqué
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class CommunicatedHrItem:
    """Élément RH effectivement communiqué, tel que décrit par l'utilisateur."""

    category: str
    description: str

    def __post_init__(self) -> None:
        if self.category not in HR_CATEGORIES:
            raise TerminationDomainError("HR_ITEM_CATEGORY_INVALID", f"unknown HR category {self.category!r}")
        if not isinstance(self.description, str):
            raise TerminationDomainError("HR_ITEM_DESCRIPTION_REQUIRED", "description must be text")
        text = unicodedata.normalize("NFC", self.description).strip()
        if not text:
            raise TerminationDomainError("HR_ITEM_DESCRIPTION_REQUIRED", "description cannot be blank")
        if len(text) > HR_ITEM_MAX_LENGTH:
            raise TerminationDomainError("HR_ITEM_DESCRIPTION_TOO_LONG", "description is too long")
        object.__setattr__(self, "description", text)


def _normalize_items(termination: ContractTermination, items: Iterable[CommunicatedHrItem]) -> list:
    items = list(items)
    if any(not isinstance(item, CommunicatedHrItem) for item in items):
        raise TerminationDomainError("HR_ITEM_INVALID", "hr_items must be CommunicatedHrItem")
    ordered = sorted(items, key=lambda item: (HR_CATEGORIES.index(item.category), item.description))
    for previous, current in zip(ordered, ordered[1:]):
        if previous == current:
            raise TerminationDomainError("HR_ITEM_DUPLICATE", f"duplicate item for {current.category}")
    for category in HR_CATEGORIES:
        state = getattr(termination.hr_checks, category)
        present = any(item.category == category for item in ordered)
        if state is CheckState.PROVIDED and not present:
            raise TerminationDomainError(
                f"HR_ITEM_REQUIRED_{category.upper()}",
                f"{category} is PROVIDED: describe what was communicated",
            )
        if state is not CheckState.PROVIDED and present:
            raise TerminationDomainError(
                f"HR_ITEM_NOT_PROVIDED_{category.upper()}",
                f"{category} is {state.value}: nothing to communicate",
            )
    return [{"category": item.category, "description": item.description} for item in ordered]


def build_transmission_payload(
    termination: ContractTermination, hr_items: Iterable[CommunicatedHrItem] = ()
) -> dict:
    """Informations communiquées à Impact Emploi, et rien d'autre.

    Exclus volontairement : commentaires internes, date de décision, workflow,
    horodatages et acteurs Teamworks, version, identifiants personne.
    """
    readiness = termination.readiness_errors()
    if readiness:
        raise TerminationDomainError(readiness[0], ", ".join(readiness))
    checks = termination.hr_checks
    return {
        "schema": PAYLOAD_SCHEMA,
        "termination_id": termination.termination_id,
        "contract_id": termination.contract_id,
        "effective_end_date": termination.effective_end_date,
        "termination_reason": termination.termination_reason,
        "notification_date": termination.notification_date,
        "last_worked_date": termination.last_worked_date,
        "notice": {
            "status": termination.notice_status,
            "start": termination.notice_start,
            "end": termination.notice_end,
        },
        "hr_checks": {category: getattr(checks, category) for category in HR_CATEGORIES},
        "hr_items": _normalize_items(termination, hr_items),
    }


def canonical_transmission_payload(
    termination: ContractTermination, hr_items: Iterable[CommunicatedHrItem] = ()
) -> str:
    return canonical_json(build_transmission_payload(termination, hr_items))


# --------------------------------------------------------------------------
# Snapshot immuable
# --------------------------------------------------------------------------

def _require_text(value: object, code: str, max_length: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TerminationDomainError(code, f"{code.lower()}: non-empty text required")
    if len(value) > max_length:
        raise TerminationDomainError(code, f"{code.lower()}: too long")
    return value


@dataclass(frozen=True, slots=True)
class TerminationTransmissionSnapshot:
    """Ce que Teamworks affirme avoir communiqué. Immuable ; corriger = nouvelle version."""

    snapshot_id: str
    termination_id: str
    version: int
    canonical_payload: str
    payload_hash: str
    created_at: datetime
    created_by: str
    transmitted_at: datetime
    transmitted_by: str
    channel: TransmissionChannel
    external_reference: Optional[str] = None
    supersedes_snapshot_id: Optional[str] = None
    correction_reason: Optional[str] = None

    def __post_init__(self) -> None:
        _require_text(self.snapshot_id, "SNAPSHOT_ID_REQUIRED", 64)
        _require_text(self.termination_id, "TERMINATION_ID_REQUIRED", 64)
        if type(self.version) is not int or self.version < 1:
            raise TerminationDomainError("SNAPSHOT_VERSION_INVALID", "snapshot version starts at 1")
        if not isinstance(self.canonical_payload, str) or sha256_hex(self.canonical_payload) != self.payload_hash:
            raise TerminationDomainError("SNAPSHOT_HASH_MISMATCH", "payload_hash does not match canonical_payload")
        try:
            decoded = json.loads(self.canonical_payload)
        except ValueError:
            raise TerminationDomainError("SNAPSHOT_PAYLOAD_INVALID", "payload is not JSON") from None
        if canonical_json(decoded) != self.canonical_payload:
            raise TerminationDomainError("SNAPSHOT_PAYLOAD_NOT_CANONICAL", "payload is not in canonical form")
        if decoded.get("schema") != PAYLOAD_SCHEMA or decoded.get("termination_id") != self.termination_id:
            raise TerminationDomainError("SNAPSHOT_PAYLOAD_MISMATCH", "payload does not describe this termination")
        for name in ("created_at", "transmitted_at"):
            value = getattr(self, name)
            if _utc_seconds(value) != value or value.tzinfo is not timezone.utc:
                raise TerminationDomainError("SNAPSHOT_TIMESTAMP_NOT_NORMALIZED", f"{name} must be UTC seconds")
        if self.transmitted_at > self.created_at:
            raise TerminationDomainError(
                "TRANSMITTED_AFTER_RECORDING", "a communication cannot be recorded before it happened"
            )
        _require_text(self.created_by, "CREATED_BY_REQUIRED", ACTOR_MAX_LENGTH)
        _require_text(self.transmitted_by, "TRANSMITTED_BY_REQUIRED", ACTOR_MAX_LENGTH)
        try:
            object.__setattr__(self, "channel", TransmissionChannel(self.channel))
        except ValueError:
            raise TerminationDomainError("TRANSMISSION_CHANNEL_INVALID", f"unknown channel {self.channel!r}") from None
        if self.external_reference is not None:
            _require_text(self.external_reference, "EXTERNAL_REFERENCE_INVALID", EXTERNAL_REFERENCE_MAX_LENGTH)
        first = self.version == 1
        if first != (self.supersedes_snapshot_id is None):
            raise TerminationDomainError(
                "SNAPSHOT_SUPERSESSION_INVALID", "only V1 has no predecessor; V2+ must supersede one"
            )
        if first != (self.correction_reason is None):
            raise TerminationDomainError(
                "SNAPSHOT_CORRECTION_REASON_INVALID", "V2+ carries its correction reason, V1 none"
            )
        if self.supersedes_snapshot_id == self.snapshot_id:
            raise TerminationDomainError("SNAPSHOT_SUPERSESSION_CYCLE", "a snapshot cannot supersede itself")

    @property
    def payload(self) -> dict:
        return json.loads(self.canonical_payload)


def _clean_reference(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TerminationDomainError("EXTERNAL_REFERENCE_INVALID", "external_reference must be text")
    value = unicodedata.normalize("NFC", value).strip()
    return value or None


def validate_supersession(
    previous: Optional[TerminationTransmissionSnapshot], termination_id: str, version: int
) -> None:
    """V1 sans prédécesseur ; Vn supersède exactement V(n-1) de la même sortie."""
    if version == 1:
        if previous is not None:
            raise TerminationDomainError("SNAPSHOT_ALREADY_TRANSMITTED", "V1 already exists")
        return
    if previous is None:
        raise TerminationDomainError("SNAPSHOT_PREDECESSOR_REQUIRED", "a correction needs the previous snapshot")
    if previous.termination_id != termination_id:
        raise TerminationDomainError(
            "SNAPSHOT_SUPERSESSION_FOREIGN", "cannot supersede a snapshot of another termination"
        )
    if previous.version != version - 1:
        raise TerminationDomainError("SNAPSHOT_VERSION_GAP", "versions must follow each other")


def create_transmission_snapshot(
    termination: ContractTermination,
    *,
    previous: Optional[TerminationTransmissionSnapshot],
    hr_items: Iterable[CommunicatedHrItem],
    created_at: datetime,
    created_by: str,
    transmitted_at: datetime,
    transmitted_by: str,
    channel: TransmissionChannel,
    external_reference: Optional[str] = None,
    expected_payload_hash: Optional[str] = None,
    snapshot_id: Optional[str] = None,
) -> TerminationTransmissionSnapshot:
    """Constitue le snapshot suivant de la sortie (V1, puis V2, V3…)."""
    version = 1 if previous is None else previous.version + 1
    validate_supersession(previous, termination.termination_id, version)
    if previous is not None and termination.open_correction is None:
        raise TerminationDomainError("CORRECTION_NOT_OPEN", "no open correction to transmit")
    payload = canonical_transmission_payload(termination, hr_items)
    payload_hash = sha256_hex(payload)
    if expected_payload_hash is not None and expected_payload_hash != payload_hash:
        raise TerminationDomainError(
            "PAYLOAD_CHANGED_SINCE_PREVIEW", "the data changed since the payload was previewed"
        )
    if previous is not None and previous.payload_hash == payload_hash:
        raise TerminationDomainError(
            "CORRECTION_WITHOUT_CHANGE", "the correction communicates exactly the same information"
        )
    transmitted_at = _utc_seconds(transmitted_at)
    if transmitted_at < _utc_seconds(termination.known_at):
        raise TerminationDomainError(
            "TRANSMITTED_BEFORE_KNOWN", "cannot have communicated a termination before it was known"
        )
    if previous is not None:
        if transmitted_at < previous.transmitted_at:
            raise TerminationDomainError(
                "CORRECTION_BEFORE_PREVIOUS", "a correction cannot precede the transmission it corrects"
            )
        if transmitted_at < _utc_seconds(termination.open_correction.requested_at):
            raise TerminationDomainError(
                "CORRECTION_BEFORE_REQUEST", "a correction cannot be sent before being requested"
            )
    return TerminationTransmissionSnapshot(
        snapshot_id=snapshot_id or uuid4().hex,
        termination_id=termination.termination_id,
        version=version,
        canonical_payload=payload,
        payload_hash=payload_hash,
        created_at=_utc_seconds(created_at),
        created_by=created_by,
        transmitted_at=transmitted_at,
        transmitted_by=transmitted_by,
        channel=channel,
        external_reference=_clean_reference(external_reference),
        supersedes_snapshot_id=None if previous is None else previous.snapshot_id,
        correction_reason=None if previous is None else termination.open_correction.reason,
    )


# --------------------------------------------------------------------------
# Commandes idempotentes
# --------------------------------------------------------------------------

class CommandType(str, Enum):
    TRANSMIT = "TRANSMIT"
    REQUEST_CORRECTION = "REQUEST_CORRECTION"
    TRANSMIT_CORRECTION = "TRANSMIT_CORRECTION"


def _require_command_id(command_id: str) -> None:
    _require_text(command_id, "COMMAND_ID_REQUIRED", COMMAND_ID_MAX_LENGTH)


@dataclass(frozen=True, slots=True)
class TransmitTermination:
    """Enregistre une communication effectuée (V1 si première, correction sinon)."""

    command_id: str
    termination_id: str
    expected_version: int
    actor_id: str
    transmitted_at: datetime
    transmitted_by: str
    channel: TransmissionChannel
    external_reference: Optional[str] = None
    hr_items: tuple = field(default_factory=tuple)
    expected_payload_hash: Optional[str] = None

    def __post_init__(self) -> None:
        _require_command_id(self.command_id)
        _require_text(self.actor_id, "ACTOR_REQUIRED", ACTOR_MAX_LENGTH)
        object.__setattr__(self, "hr_items", tuple(self.hr_items))
        object.__setattr__(self, "transmitted_at", _utc_seconds(self.transmitted_at))
        object.__setattr__(self, "external_reference", _clean_reference(self.external_reference))
        try:
            object.__setattr__(self, "channel", TransmissionChannel(self.channel))
        except ValueError:
            raise TerminationDomainError("TRANSMISSION_CHANNEL_INVALID", f"unknown channel {self.channel!r}") from None

    def fingerprint(self, command_type: CommandType) -> str:
        items = sorted(
            ({"category": i.category, "description": i.description} for i in self.hr_items),
            key=lambda item: (item["category"], item["description"]),
        )
        return sha256_hex(canonical_json({
            "command_type": command_type,
            "termination_id": self.termination_id,
            "expected_version": self.expected_version,
            "actor_id": self.actor_id,
            "transmitted_at": self.transmitted_at,
            "transmitted_by": self.transmitted_by,
            "channel": self.channel,
            "external_reference": self.external_reference,
            "hr_items": items,
            "expected_payload_hash": self.expected_payload_hash,
        }))


@dataclass(frozen=True, slots=True)
class RequestCorrection:
    command_id: str
    termination_id: str
    expected_version: int
    reason: str
    requested_by: str

    def __post_init__(self) -> None:
        _require_command_id(self.command_id)
        _require_text(self.requested_by, "ACTOR_REQUIRED", ACTOR_MAX_LENGTH)

    def fingerprint(self) -> str:
        return sha256_hex(canonical_json({
            "command_type": CommandType.REQUEST_CORRECTION,
            "termination_id": self.termination_id,
            "expected_version": self.expected_version,
            "reason": self.reason,
            "requested_by": self.requested_by,
        }))


@dataclass(frozen=True, slots=True)
class TransmissionResult:
    snapshot: TerminationTransmissionSnapshot
    termination_version: int
    replayed: bool


@dataclass(frozen=True, slots=True)
class CorrectionRequestResult:
    termination_id: str
    termination_version: int
    replayed: bool
