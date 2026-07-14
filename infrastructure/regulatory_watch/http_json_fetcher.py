from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from domain.regulatory import RegulatoryReference, RegulatorySnapshot


class RegulatorySourceFetchError(RuntimeError):
    """Erreur technique lors de la récupération d'une source officielle."""


@dataclass(frozen=True, slots=True)
class HttpJsonRegulatorySourceFetcher:
    """Récupère une source JSON officielle et produit un instantané réglementaire.

    Ce prototype reste volontairement générique : il ne connaît aucune règle CCNS,
    n'interprète pas le contenu juridique et se limite à normaliser la réponse JSON
    pour obtenir un hash stable compatible avec le socle de veille.
    """

    timeout_seconds: float = 10.0
    headers: Mapping[str, str] = field(default_factory=dict)
    opener: Callable[..., object] = urlopen

    def fetch(self, reference: RegulatoryReference) -> RegulatorySnapshot:
        request = Request(
            reference.source_url,
            headers={"Accept": "application/json", **dict(self.headers)},
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                raw_content = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise RegulatorySourceFetchError(
                f"Impossible de récupérer la source réglementaire {reference.code}"
            ) from exc

        normalized_content, metadata = self._normalize_json(raw_content)
        return RegulatorySnapshot.from_content(
            reference_code=reference.code,
            source_url=reference.source_url,
            content=normalized_content,
            fetched_at=datetime.now(timezone.utc),
            source_title=reference.label,
            effective_date=self._extract_effective_date(metadata),
            metadata=metadata,
        )

    @staticmethod
    def _normalize_json(raw_content: bytes) -> tuple[bytes, dict[str, str]]:
        try:
            payload = json.loads(raw_content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RegulatorySourceFetchError("La source ne retourne pas un JSON valide") from exc

        normalized = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        metadata: dict[str, str] = {"format": "json"}
        if isinstance(payload, dict):
            for source_key, metadata_key in (
                ("id", "source_id"),
                ("title", "title"),
                ("slug", "slug"),
                ("last_update", "last_update"),
                ("last_modified", "last_modified"),
            ):
                value = payload.get(source_key)
                if value is not None:
                    metadata[metadata_key] = str(value)
        return normalized, metadata

    @staticmethod
    def _extract_effective_date(metadata: Mapping[str, str]) -> Optional[date]:
        for key in ("last_update", "last_modified"):
            value = metadata.get(key)
            if not value:
                continue
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                continue
        return None
