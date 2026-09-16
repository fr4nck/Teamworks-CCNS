from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class MissingMergeField:
    field: str
    source: str


@dataclass(frozen=True)
class MergeContext:
    """Neutral values passed to the document core by a business-data adapter."""

    values: dict[str, object]

    def get(self, key: str, default: object = "") -> object:
        return self.values.get(key, default)

    def as_dict(self) -> dict[str, object]:
        return dict(self.values)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "MergeContext":
        normalized: dict[str, object] = {}
        for key, value in values.items():
            normalized_key = str(key).strip().upper()
            if normalized_key:
                normalized[normalized_key] = _clean_value(value)
        return cls(values=normalized)


def _clean_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return value


def _copy_prefixed(target: dict[str, object], source: Mapping[str, object] | None, prefix: str) -> None:
    if not source:
        return
    for key, value in source.items():
        normalized_key = str(key).strip().upper()
        if not normalized_key:
            continue
        target[f"{prefix}_{normalized_key}"] = _clean_value(value)


def build_merge_context(
    *,
    structure: Mapping[str, object] | None = None,
    employee: Mapping[str, object] | None = None,
    contract: Mapping[str, object] | None = None,
    extra: Mapping[str, object] | None = None,
) -> MergeContext:
    """Construit les mots-clés canoniques sans injecter de données propres à une structure."""
    values: dict[str, object] = {}
    _copy_prefixed(values, structure, "STRUCTURE")
    _copy_prefixed(values, employee, "SALARIE")
    _copy_prefixed(values, contract, "CONTRAT")
    if extra:
        for key, value in extra.items():
            normalized_key = str(key).strip().upper()
            if normalized_key:
                values.setdefault(normalized_key, _clean_value(value))
    return MergeContext(values=values)


def validate_required_fields(
    context: MergeContext,
    required_fields: tuple[str, ...] | list[str],
) -> tuple[MissingMergeField, ...]:
    missing: list[MissingMergeField] = []
    for field in required_fields:
        normalized = str(field).strip().upper()
        value = context.values.get(normalized, "")
        if value in (None, ""):
            source = normalized.split("_", 1)[0].lower() if "_" in normalized else "document"
            missing.append(MissingMergeField(field=normalized, source=source))
    return tuple(missing)
