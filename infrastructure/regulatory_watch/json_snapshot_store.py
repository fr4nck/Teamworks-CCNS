from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from domain.regulatory import RegulatorySnapshot


class JsonRegulatorySnapshotStore:
    """Stockage append-only minimal des sources détectées.

    Le fichier produit sert d'historique d'observation et ne pilote aucune mise
    à jour automatique des règles CCNS ni des grilles de production.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def get_latest(self, reference_code: str) -> Optional[RegulatorySnapshot]:
        snapshots = [
            snapshot
            for snapshot in self._read_all()
            if snapshot.reference_code == reference_code
        ]
        if not snapshots:
            return None
        return max(snapshots, key=lambda snapshot: snapshot.fetched_at)

    def save(self, snapshot: RegulatorySnapshot) -> None:
        entries = [self._to_dict(item) for item in self._read_all()]
        entries.append(self._to_dict(snapshot))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _read_all(self) -> list[RegulatorySnapshot]:
        if not self.path.exists():
            return []
        content = self.path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        return [self._from_dict(item) for item in json.loads(content)]

    @staticmethod
    def _to_dict(snapshot: RegulatorySnapshot) -> dict[str, object]:
        return {
            "reference_code": snapshot.reference_code,
            "fetched_at": snapshot.fetched_at.isoformat(),
            "source_url": snapshot.source_url,
            "content_hash": snapshot.content_hash,
            "content_length": snapshot.content_length,
            "source_title": snapshot.source_title,
            "effective_date": snapshot.effective_date.isoformat()
            if snapshot.effective_date
            else None,
            "metadata": dict(snapshot.metadata),
        }

    @staticmethod
    def _from_dict(data: dict[str, object]) -> RegulatorySnapshot:
        raw_effective_date = data.get("effective_date")
        return RegulatorySnapshot(
            reference_code=str(data["reference_code"]),
            fetched_at=datetime.fromisoformat(str(data["fetched_at"])),
            source_url=str(data["source_url"]),
            content_hash=str(data["content_hash"]),
            content_length=int(data["content_length"]),
            source_title=str(data["source_title"])
            if data.get("source_title") is not None
            else None,
            effective_date=date.fromisoformat(str(raw_effective_date))
            if raw_effective_date
            else None,
            metadata={
                str(key): str(value)
                for key, value in dict(data.get("metadata", {})).items()
            },
        )
