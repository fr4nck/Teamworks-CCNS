from __future__ import annotations

from application.services.contract_document_workspace import (
    ContractDocumentContext,
    ContractDocumentWorkspaceErrorCode,
    prepare_contract_document_workspace,
)
from domain.documents import DocumentTemplate, GenerationStatus, TemplateTarget


class FakePort:
    def __init__(self, *, context=None, templates=(), error=None):
        self.context = context
        self.templates = tuple(templates)
        self.error = error
        self.loaded_ids = []

    def load_context(self, contract_id):
        self.loaded_ids.append(contract_id)
        if self.error:
            raise self.error
        return self.context

    def list_templates(self):
        if self.error:
            raise self.error
        return self.templates


def _context():
    return ContractDocumentContext(
        structure={
            "raison_sociale": "Association Test",
            "adresse": "1 rue du Test",
        },
        employee={
            "nom": "Martin",
            "prenom": "Lou",
        },
        contract={
            "date_debut": "01/09/2026",
            "convention": "CCNS",
            "groupe_ccns": "G2",
        },
        extra={},
    )


def test_workspace_prepares_contract_document_choices_and_filters_templates():
    port = FakePort(
        context=_context(),
        templates=(
            DocumentTemplate("legacy.twd"),
            DocumentTemplate(
                "g2-contract.twd",
                target=TemplateTarget(
                    convention_code="CCNS",
                    ccns_group="G2",
                    document_kind="contract",
                ),
            ),
            DocumentTemplate(
                "g3-contract.twd",
                target=TemplateTarget(
                    convention_code="CCNS",
                    ccns_group="G3",
                    document_kind="contract",
                ),
            ),
        ),
    )

    workspace = prepare_contract_document_workspace(port, contract_id=417)

    assert workspace.ok is True
    assert port.loaded_ids == [417]
    by_code = {choice.code: choice for choice in workspace.choices}
    contract = by_code["contract"]
    assert contract.status is GenerationStatus.READY
    assert contract.ready is True
    assert [item.name for item in contract.templates] == [
        "legacy.twd",
        "g2-contract.twd",
    ]
    external = by_code["france_travail_certificate"]
    assert external.status is GenerationStatus.EXTERNAL_PREPARATION
    assert external.ready is False


def test_workspace_rejects_invalid_contract_id_without_reading():
    port = FakePort(context=_context())

    workspace = prepare_contract_document_workspace(port, contract_id=0)

    assert workspace.ok is False
    assert port.loaded_ids == []
    assert workspace.errors[0].code is ContractDocumentWorkspaceErrorCode.INVALID_CONTRACT_ID


def test_workspace_distinguishes_missing_context_from_read_error():
    missing = prepare_contract_document_workspace(FakePort(context=None), contract_id=417)
    failed = prepare_contract_document_workspace(
        FakePort(context=_context(), error=RuntimeError("db indisponible")),
        contract_id=417,
    )

    assert missing.errors[0].code is ContractDocumentWorkspaceErrorCode.CONTEXT_NOT_FOUND
    assert failed.errors[0].code is ContractDocumentWorkspaceErrorCode.READ_ERROR
    assert "db indisponible" in failed.errors[0].message
