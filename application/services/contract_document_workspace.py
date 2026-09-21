from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Protocol

from domain.documents import (
    DocumentScope,
    DocumentTemplate,
    GenerationStatus,
    list_document_types,
)

from .hr_document_workflow import prepare_hr_document_workflow


@dataclass(frozen=True)
class ContractDocumentContext:
    structure: Mapping[str, object]
    employee: Mapping[str, object]
    contract: Mapping[str, object]
    extra: Mapping[str, object]


class ContractDocumentPort(Protocol):
    def load_context(self, contract_id: int) -> ContractDocumentContext | None:
        ...

    def list_templates(self) -> tuple[DocumentTemplate, ...]:
        ...


class ContractDocumentWorkspaceErrorCode(str, Enum):
    INVALID_CONTRACT_ID = "invalid_contract_id"
    CONTEXT_NOT_FOUND = "context_not_found"
    READ_ERROR = "read_error"


@dataclass(frozen=True)
class ContractDocumentWorkspaceError:
    code: ContractDocumentWorkspaceErrorCode
    message: str


@dataclass(frozen=True)
class ContractDocumentChoice:
    code: str
    label: str
    generated_by_teamworks: bool
    status: GenerationStatus | None
    ready: bool
    templates: tuple[DocumentTemplate, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class ContractDocumentWorkspace:
    contract_id: int | None
    choices: tuple[ContractDocumentChoice, ...]
    errors: tuple[ContractDocumentWorkspaceError, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _valid_contract_id(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def prepare_contract_document_workspace(
    port: ContractDocumentPort,
    *,
    contract_id: int,
    include_legacy_templates: bool = True,
) -> ContractDocumentWorkspace:
    """Prépare la vue documentaire d'un contrat sans dépendance wx ou Qt."""

    if not _valid_contract_id(contract_id):
        return ContractDocumentWorkspace(
            contract_id=None,
            choices=(),
            errors=(
                ContractDocumentWorkspaceError(
                    code=ContractDocumentWorkspaceErrorCode.INVALID_CONTRACT_ID,
                    message="Identifiant historique du contrat invalide.",
                ),
            ),
        )

    try:
        context = port.load_context(contract_id)
        templates = tuple(port.list_templates())
    except Exception as exc:
        return ContractDocumentWorkspace(
            contract_id=contract_id,
            choices=(),
            errors=(
                ContractDocumentWorkspaceError(
                    code=ContractDocumentWorkspaceErrorCode.READ_ERROR,
                    message=f"Préparation documentaire impossible : {exc}",
                ),
            ),
        )

    if context is None:
        return ContractDocumentWorkspace(
            contract_id=contract_id,
            choices=(),
            errors=(
                ContractDocumentWorkspaceError(
                    code=ContractDocumentWorkspaceErrorCode.CONTEXT_NOT_FOUND,
                    message=f"Contrat n°{contract_id} introuvable.",
                ),
            ),
        )

    choices: list[ContractDocumentChoice] = []
    for document_type in list_document_types(scope=DocumentScope.CONTRACT):
        result = prepare_hr_document_workflow(
            document_type.code,
            templates=templates,
            include_legacy_templates=include_legacy_templates,
            require_template=document_type.generated_by_teamworks,
            structure=context.structure,
            employee=context.employee,
            contract=context.contract,
            extra=context.extra,
        )
        issues = [error.message for error in result.errors]
        if result.generation_plan is not None:
            issues.extend(issue.message for issue in result.generation_plan.issues)

        choices.append(
            ContractDocumentChoice(
                code=document_type.code,
                label=document_type.label,
                generated_by_teamworks=document_type.generated_by_teamworks,
                status=(
                    result.generation_plan.status
                    if result.generation_plan is not None
                    else None
                ),
                ready=result.ready,
                templates=result.templates,
                issues=tuple(issues),
            )
        )

    return ContractDocumentWorkspace(
        contract_id=contract_id,
        choices=tuple(choices),
        errors=(),
    )
