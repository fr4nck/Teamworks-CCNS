"""Canonical fingerprint for an ephemeral DPAE preparation.

The fingerprint deliberately covers the DPAE projection of Teamworks source
records, not complete database rows. Unrelated changes must not make a
preparation stale. In particular, planning changes are not DPAE source data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, time
from hashlib import sha256
import json


FINGERPRINT_SCHEMA_VERSION = 1
DPAE_RULES_VERSION = "2026-09-27.1"


@dataclass(frozen=True)
class DpaeSourceProjection:
    """Minimal canonical projection used to prepare a DPAE.

    ``employee_fields`` and ``contract_fields`` contain only fields actually
    consumed by the DPAE payload/validation layer. They must not contain row
    versions, ``updated_at`` values, UI state, planning data or unrelated HR
    data.
    """

    contract_id: str
    employee_id: str
    hiring_date: date
    hiring_time: time
    employer_siret: str
    employee_fields: dict[str, object]
    contract_fields: dict[str, object]
    employer_fields: dict[str, object]


def _normalise(value: object) -> object:
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _normalise(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    return value


def canonical_fingerprint_document(
    source: DpaeSourceProjection,
    *,
    rules_version: str = DPAE_RULES_VERSION,
    schema_version: int = FINGERPRINT_SCHEMA_VERSION,
) -> dict[str, object]:
    return {
        "fingerprint_schema_version": schema_version,
        "dpae_rules_version": rules_version,
        "source": _normalise(asdict(source)),
    }


def compute_source_fingerprint(
    source: DpaeSourceProjection,
    *,
    rules_version: str = DPAE_RULES_VERSION,
    schema_version: int = FINGERPRINT_SCHEMA_VERSION,
) -> str:
    document = canonical_fingerprint_document(
        source,
        rules_version=rules_version,
        schema_version=schema_version,
    )
    canonical = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()
