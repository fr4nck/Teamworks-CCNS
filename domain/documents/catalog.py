from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class DocumentKind(str, Enum):
    CONTRACT = "contract"
    AMENDMENT = "amendment"
    MUTUAL_INSURANCE_WAIVER = "mutual_insurance_waiver"
    EMPLOYMENT_CERTIFICATE = "employment_certificate"
    EXPERIENCE_CERTIFICATE = "experience_certificate"
    MINOR_AUTHORIZATION = "minor_authorization"
    WORK_CERTIFICATE = "work_certificate"
    TRAINING_DOCUMENT = "training_document"
    END_OF_CONTRACT_DOCUMENT = "end_of_contract_document"
    FRANCE_TRAVAIL_CERTIFICATE = "france_travail_certificate"


class DocumentScope(str, Enum):
    EMPLOYEE = "employee"
    CONTRACT = "contract"


class DocumentGenerationMode(str, Enum):
    INTERNAL_TEMPLATE = "internal_template"
    EXTERNAL_PREPARATION = "external_preparation"


@dataclass(frozen=True)
class DocumentType:
    kind: DocumentKind
    label: str
    scope: DocumentScope
    generation_mode: DocumentGenerationMode = DocumentGenerationMode.INTERNAL_TEMPLATE
    required_fields: tuple[str, ...] = ()
    description: str = ""

    @property
    def code(self) -> str:
        return self.kind.value

    @property
    def generated_by_teamworks(self) -> bool:
        return self.generation_mode is DocumentGenerationMode.INTERNAL_TEMPLATE


_COMMON_STRUCTURE_FIELDS = (
    "STRUCTURE_RAISON_SOCIALE",
    "STRUCTURE_ADRESSE",
)
_COMMON_EMPLOYEE_FIELDS = (
    "SALARIE_NOM",
    "SALARIE_PRENOM",
)
_COMMON_CONTRACT_FIELDS = (
    "CONTRAT_DATE_DEBUT",
)


DEFAULT_HR_DOCUMENT_CATALOG: tuple[DocumentType, ...] = (
    DocumentType(
        kind=DocumentKind.CONTRACT,
        label="Contrat de travail",
        scope=DocumentScope.CONTRACT,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS + _COMMON_CONTRACT_FIELDS,
        description="Contrat généré à partir d'un modèle Teamworks et des données structure, salarié et contrat.",
    ),
    DocumentType(
        kind=DocumentKind.AMENDMENT,
        label="Avenant au contrat",
        scope=DocumentScope.CONTRACT,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS + _COMMON_CONTRACT_FIELDS,
        description="Avenant généré à partir du dossier salarié et du contrat concerné.",
    ),
    DocumentType(
        kind=DocumentKind.MUTUAL_INSURANCE_WAIVER,
        label="Dispense de mutuelle",
        scope=DocumentScope.EMPLOYEE,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS,
        description="Document de dispense alimenté par les données de la structure et du salarié.",
    ),
    DocumentType(
        kind=DocumentKind.EMPLOYMENT_CERTIFICATE,
        label="Attestation d'emploi",
        scope=DocumentScope.EMPLOYEE,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS,
    ),
    DocumentType(
        kind=DocumentKind.EXPERIENCE_CERTIFICATE,
        label="Attestation d'expérience",
        scope=DocumentScope.EMPLOYEE,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS,
    ),
    DocumentType(
        kind=DocumentKind.MINOR_AUTHORIZATION,
        label="Autorisation pour salarié mineur",
        scope=DocumentScope.EMPLOYEE,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS,
    ),
    DocumentType(
        kind=DocumentKind.WORK_CERTIFICATE,
        label="Certificat de travail",
        scope=DocumentScope.CONTRACT,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS + _COMMON_CONTRACT_FIELDS,
    ),
    DocumentType(
        kind=DocumentKind.TRAINING_DOCUMENT,
        label="Document de formation",
        scope=DocumentScope.EMPLOYEE,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS,
    ),
    DocumentType(
        kind=DocumentKind.END_OF_CONTRACT_DOCUMENT,
        label="Document de fin de contrat",
        scope=DocumentScope.CONTRACT,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS + _COMMON_CONTRACT_FIELDS,
    ),
    DocumentType(
        kind=DocumentKind.FRANCE_TRAVAIL_CERTIFICATE,
        label="Attestation France Travail",
        scope=DocumentScope.CONTRACT,
        generation_mode=DocumentGenerationMode.EXTERNAL_PREPARATION,
        required_fields=_COMMON_STRUCTURE_FIELDS + _COMMON_EMPLOYEE_FIELDS + _COMMON_CONTRACT_FIELDS,
        description=(
            "Teamworks prépare et suit les données nécessaires, mais le document réglementé reste produit "
            "et transmis via le service externe compétent."
        ),
    ),
)


def _catalog_by_code(catalog: Iterable[DocumentType]) -> dict[str, DocumentType]:
    result: dict[str, DocumentType] = {}
    for document_type in catalog:
        if document_type.code in result:
            raise ValueError(f"Code de document dupliqué : {document_type.code}")
        result[document_type.code] = document_type
    return result


def list_document_types(
    *,
    scope: DocumentScope | None = None,
    generated_by_teamworks: bool | None = None,
    catalog: Iterable[DocumentType] = DEFAULT_HR_DOCUMENT_CATALOG,
) -> tuple[DocumentType, ...]:
    items = tuple(catalog)
    if scope is not None:
        items = tuple(item for item in items if item.scope is scope)
    if generated_by_teamworks is not None:
        items = tuple(item for item in items if item.generated_by_teamworks is generated_by_teamworks)
    return items


def get_document_type(
    code: str | DocumentKind,
    *,
    catalog: Iterable[DocumentType] = DEFAULT_HR_DOCUMENT_CATALOG,
) -> DocumentType:
    normalized = code.value if isinstance(code, DocumentKind) else str(code).strip()
    by_code = _catalog_by_code(catalog)
    try:
        return by_code[normalized]
    except KeyError as exc:
        raise KeyError(f"Type de document RH inconnu : {normalized}") from exc
