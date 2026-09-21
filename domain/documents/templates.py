from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


CEE_LABELS = {
    "BAFA_HOLDER": "BAFA titulaire",
    "BAFA_TRAINEE": "BAFA stagiaire",
    "UNQUALIFIED": "Non diplômé",
    "EQUIVALENT": "Qualification équivalente",
    "BAFD_HOLDER": "BAFD titulaire",
    "BAFD_TRAINEE": "BAFD stagiaire",
}


@dataclass(frozen=True)
class TemplateTarget:
    convention_code: str | None = None
    ccns_group: str | None = None
    cee_qualification: str | None = None
    document_kind: str | None = None


@dataclass(frozen=True)
class DocumentTemplate:
    name: str
    target: TemplateTarget | None = None
    location: str | None = None

    @property
    def legacy(self) -> bool:
        return self.target is None


def _clean(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip() or None


def normalize_cee_qualification(value: object) -> str | None:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    if cleaned in CEE_LABELS:
        return cleaned
    lowered = cleaned.lower()
    for code, label in CEE_LABELS.items():
        if lowered == label.lower():
            return code
    return cleaned


def target_from_mapping(metadata: Mapping[str, object] | None) -> TemplateTarget | None:
    if metadata is None:
        return None
    return TemplateTarget(
        convention_code=_clean(metadata.get("convention_code")),
        ccns_group=_clean(metadata.get("ccns_group")),
        cee_qualification=normalize_cee_qualification(metadata.get("cee_qualification")),
        document_kind=_clean(metadata.get("document_kind")),
    )


def is_contract_target_compatible(
    contract_data: Mapping[str, object] | None,
    target: TemplateTarget | None,
) -> bool:
    """Compatibilité pure extraite de l'adaptateur DB historique."""

    if target is None:
        return True

    contract_data = contract_data or {}
    contract_convention = _clean(
        contract_data.get("CONVENTION_CODE") or contract_data.get("CONVENTION")
    )
    contract_group = _clean(contract_data.get("GROUPECCNS"))
    contract_cee = normalize_cee_qualification(
        contract_data.get("QUALIFICATIONCEE_CODE")
        or contract_data.get("QUALIFICATIONCEE")
    )

    if target.convention_code == "CCNS":
        return contract_convention == "CCNS" and (
            target.ccns_group is None or target.ccns_group == contract_group
        )
    if target.convention_code == "CEE" or target.cee_qualification:
        return (
            contract_convention == "CEE" or contract_cee is not None
        ) and (
            target.cee_qualification is None
            or target.cee_qualification == contract_cee
        )
    return (
        target.convention_code is None
        and target.ccns_group is None
        and target.cee_qualification is None
    )


def is_document_kind_compatible(
    target: TemplateTarget | None,
    document_kind: str | None,
    *,
    include_legacy: bool = True,
) -> bool:
    requested = _clean(document_kind)
    if requested is None:
        return True
    if target is None or target.document_kind is None:
        return bool(include_legacy)
    return target.document_kind == requested


def select_document_templates(
    templates: Iterable[DocumentTemplate],
    *,
    contract_data: Mapping[str, object] | None = None,
    document_kind: str | None = None,
    include_legacy: bool = True,
) -> tuple[DocumentTemplate, ...]:
    return tuple(
        template
        for template in templates
        if is_contract_target_compatible(contract_data, template.target)
        and is_document_kind_compatible(
            template.target,
            document_kind,
            include_legacy=include_legacy,
        )
    )
