from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Protocol

from domain.regulatory import (
    RegulatoryChange,
    RegulatoryReference,
    RegulatorySnapshot,
    compare_regulatory_snapshots,
)


class RegulatorySourceFetcher(Protocol):
    def fetch(self, reference: RegulatoryReference) -> RegulatorySnapshot:
        """Retourne un instantané de la source sans modifier les données métier."""


class RegulatorySnapshotStore(Protocol):
    def get_latest(self, reference_code: str) -> Optional[RegulatorySnapshot]:
        """Retourne le dernier instantané connu pour une référence."""

    def save(self, snapshot: RegulatorySnapshot) -> None:
        """Enregistre la source observée pour audit et validation humaine."""


@dataclass(slots=True)
class RegulatoryWatchService:
    """Orchestre la détection réglementaire en lecture seule côté métier CCNS."""

    fetcher: RegulatorySourceFetcher
    store: RegulatorySnapshotStore

    def check_reference(self, reference: RegulatoryReference) -> RegulatoryChange:
        previous = self.store.get_latest(reference.code)
        current = self.fetcher.fetch(reference)
        change = compare_regulatory_snapshots(reference, previous, current)
        self.store.save(current)
        return change

    def check_references(
        self, references: Iterable[RegulatoryReference]
    ) -> list[RegulatoryChange]:
        return [self.check_reference(reference) for reference in references]
