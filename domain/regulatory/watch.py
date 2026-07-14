from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Mapping, Optional


class RegulatoryReferenceKind(str, Enum):
    """Familles de références suivies sans effet automatique sur les règles métier."""

    CCNS_TEXT = "ccns_text"
    SALARY_AMENDMENT = "salary_amendment"
    CCNS_GENERAL_CHANGE = "ccns_general_change"
    SMIC = "smic"
    EDUCATIONAL_ENGAGEMENT_CONTRACT = "educational_engagement_contract"
    EXTENSION_ORDER = "extension_order"


class RegulatoryChangeType(str, Enum):
    NEW_REFERENCE = "new_reference"
    SOURCE_CHANGED = "source_changed"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class RegulatoryReference:
    """Référence officielle ou documentaire à surveiller.

    Cette entité décrit uniquement une source à observer. Elle ne porte pas de
    règle CCNS exécutable et ne doit pas déclencher de modification automatique
    des grilles ou contrôles métier.
    """

    code: str
    label: str
    kind: RegulatoryReferenceKind
    source_url: str
    expected_scope: str

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.label.strip():
            raise ValueError("label is required")
        if not self.source_url.strip():
            raise ValueError("source_url is required")
        if not self.expected_scope.strip():
            raise ValueError("expected_scope is required")


@dataclass(frozen=True, slots=True)
class RegulatorySnapshot:
    """Version enregistrée d'une source réglementaire ou salariale."""

    reference_code: str
    fetched_at: datetime
    source_url: str
    content_hash: str
    content_length: int
    source_title: Optional[str] = None
    effective_date: Optional[date] = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_content(
        cls,
        *,
        reference_code: str,
        source_url: str,
        content: bytes,
        fetched_at: Optional[datetime] = None,
        source_title: Optional[str] = None,
        effective_date: Optional[date] = None,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> "RegulatorySnapshot":
        if not reference_code.strip():
            raise ValueError("reference_code is required")
        if not source_url.strip():
            raise ValueError("source_url is required")
        moment = fetched_at or datetime.now(timezone.utc)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return cls(
            reference_code=reference_code,
            fetched_at=moment,
            source_url=source_url,
            content_hash=sha256(content).hexdigest(),
            content_length=len(content),
            source_title=source_title,
            effective_date=effective_date,
            metadata=dict(metadata or {}),
        )

    def __post_init__(self) -> None:
        if not self.reference_code.strip():
            raise ValueError("reference_code is required")
        if not self.source_url.strip():
            raise ValueError("source_url is required")
        if not self.content_hash.strip():
            raise ValueError("content_hash is required")
        if self.content_length < 0:
            raise ValueError("content_length cannot be negative")
        if self.fetched_at.tzinfo is None:
            raise ValueError("fetched_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class RegulatoryChange:
    reference: RegulatoryReference
    change_type: RegulatoryChangeType
    previous_snapshot: Optional[RegulatorySnapshot]
    current_snapshot: RegulatorySnapshot
    requires_human_validation: bool = True

    @property
    def has_alert(self) -> bool:
        return self.change_type is not RegulatoryChangeType.UNCHANGED

    @property
    def summary(self) -> str:
        if self.change_type is RegulatoryChangeType.NEW_REFERENCE:
            return f"Nouvelle référence surveillée : {self.reference.label}"
        if self.change_type is RegulatoryChangeType.SOURCE_CHANGED:
            return f"Source modifiée pour {self.reference.label}"
        return f"Aucun changement détecté pour {self.reference.label}"


def compare_regulatory_snapshots(
    reference: RegulatoryReference,
    previous_snapshot: Optional[RegulatorySnapshot],
    current_snapshot: RegulatorySnapshot,
) -> RegulatoryChange:
    """Compare deux états sans interpréter ni appliquer les règles métier."""

    if current_snapshot.reference_code != reference.code:
        raise ValueError("current snapshot does not match reference")
    if previous_snapshot is None:
        change_type = RegulatoryChangeType.NEW_REFERENCE
    elif previous_snapshot.content_hash != current_snapshot.content_hash:
        change_type = RegulatoryChangeType.SOURCE_CHANGED
    else:
        change_type = RegulatoryChangeType.UNCHANGED
    return RegulatoryChange(
        reference=reference,
        change_type=change_type,
        previous_snapshot=previous_snapshot,
        current_snapshot=current_snapshot,
    )
