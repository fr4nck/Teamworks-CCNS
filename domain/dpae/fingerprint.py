"""Canonical fingerprint for the minimal DPAE source projection."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, time
from hashlib import sha256
import json

FINGERPRINT_SCHEMA_VERSION = 1
DPAE_RULES_VERSION = "2026-09-27.1"


@dataclass(frozen=True)
class DpaeSourceProjection:
    """Only values that can influence DPAE preparation belong here.

    Teamworks technical person identifiers, UI state, planning data and row
    versions are deliberately excluded. ``hiring_time`` is not a top-level
    source because DATA-001 found no canonical contract source for it.
    """
    contract_id: str
    hiring_date: date
    employer_siret: str
    employee_fields: dict[str, object]
    contract_fields: dict[str, object]
    employer_fields: dict[str, object]


def _normalise(value: object) -> object:
    if isinstance(value,(date,time)): return value.isoformat()
    if isinstance(value,dict): return {key:_normalise(value[key]) for key in sorted(value)}
    if isinstance(value,(list,tuple)): return [_normalise(item) for item in value]
    return value


def canonical_fingerprint_document(source:DpaeSourceProjection,*,rules_version:str=DPAE_RULES_VERSION,schema_version:int=FINGERPRINT_SCHEMA_VERSION)->dict[str,object]:
    return {"fingerprint_schema_version":schema_version,"dpae_rules_version":rules_version,"source":_normalise(asdict(source))}


def compute_source_fingerprint(source:DpaeSourceProjection,*,rules_version:str=DPAE_RULES_VERSION,schema_version:int=FINGERPRINT_SCHEMA_VERSION)->str:
    canonical=json.dumps(canonical_fingerprint_document(source,rules_version=rules_version,schema_version=schema_version),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return sha256(canonical).hexdigest()
