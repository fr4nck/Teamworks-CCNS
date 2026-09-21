from __future__ import annotations

import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402

from application.services.contract_document_workspace import (  # noqa: E402
    ContractDocumentContext,
    prepare_contract_document_workspace,
)
from contract_document_adapter import QtContractDocumentReadAdapter  # noqa: E402
from contract_documents import ContractDocumentsDialog  # noqa: E402
from data_adapter import ContractView, PersonView  # noqa: E402
from domain.documents import DocumentTemplate  # noqa: E402
from pilot_view import PeopleContractsPilot  # noqa: E402


class NoSchemaMutationDb:
    def __init__(self):
        self.calls = []

    def IsTableExists(self, table):
        self.calls.append(("IsTableExists", table))
        return False

    def AjoutChamp(self, *args, **kwargs):
        raise AssertionError("l'adaptateur Documents Qt ne doit jamais migrer le schéma")

    def CreationTable(self, *args, **kwargs):
        raise AssertionError("l'adaptateur Documents Qt ne doit jamais créer de table")


def _snapshot():
    return SimpleNamespace(
        contract_id=417,
        person_id=12,
        contract_type_code="CDI",
        contract_type_label="CDI",
        convention_code="CCNS",
        ccns_group="G2",
        cee_qualification=None,
        weekly_hours=Decimal("35"),
        gross_monthly_salary=Decimal("2500"),
        gross_annual_salary=None,
        start_date=date(2026, 9, 1),
        end_date=None,
        break_date=None,
        modern_fields_supported=True,
    )


def _person_generalities():
    return SimpleNamespace(
        last_name="Martin",
        first_name="Lou",
        civility="Mme",
        birth_date="01/02/1990",
        address="1 rue du Test",
        postcode="35000",
        city="Rennes",
        coordinates=(
            SimpleNamespace(category="Mobile", text="0600000000"),
            SimpleNamespace(category="Email", text="lou@example.test"),
        ),
    )


def test_qt_document_read_adapter_reuses_readers_without_schema_mutation(tmp_path):
    (tmp_path / "legacy.twd").write_text("Bonjour {NOM}", encoding="utf-8")
    db = NoSchemaMutationDb()
    reader = SimpleNamespace(read_contract=lambda contract_id: _snapshot())

    adapter = QtContractDocumentReadAdapter(
        get_person_generalities=lambda person_id: _person_generalities(),
        contract_reader=reader,
        db=db,
        template_directory=tmp_path,
        structure_loader=lambda: {
            "raison_sociale": "Association Test",
            "adresse": "1 rue Structure",
        },
    )

    context = adapter.load_context(417)
    templates = adapter.list_templates()

    assert context is not None
    assert context.employee["nom"] == "Martin"
    assert context.employee["telephones"] == "0600000000"
    assert context.employee["emails"] == "lou@example.test"
    assert context.contract["groupe_ccns"] == "G2"
    assert context.extra["DATEDEBUT"] == "01/09/2026"
    assert [item.name for item in templates] == ["legacy.twd"]
    assert templates[0].legacy is True
    assert db.calls == [("IsTableExists", "contrats_documents_modeles")]


class PilotAdapter:
    def list_people(self):
        return (
            PersonView(
                id="—",
                id_historique=12,
                name="Lou Martin",
                first_name="Lou",
                last_name="Martin",
                birth_date="01/02/1990",
                role="Animatrice",
                classification="Groupe 2",
                contract="CDI",
                weekly_hours="35 h",
                status="—",
                site="—",
                medical="—",
                mutual="—",
            ),
        )

    def list_contracts(self, person_id):
        return (
            ContractView(
                kind="CDI",
                start="01/09/2026",
                end="—",
                classification="Groupe 2",
                duration="35 h",
                status="Actif",
                id_historique=417,
            ),
        )


class WorkspacePort:
    def load_context(self, contract_id):
        return ContractDocumentContext(
            structure={
                "raison_sociale": "Association Test",
                "adresse": "1 rue Structure",
            },
            employee={"nom": "Martin", "prenom": "Lou"},
            contract={
                "date_debut": "01/09/2026",
                "convention": "CCNS",
                "groupe_ccns": "G2",
            },
            extra={},
        )

    def list_templates(self):
        return (DocumentTemplate("legacy.twd"),)


def _app():
    return QApplication.instance() or QApplication([])


def test_qt_contract_document_action_uses_stable_contract_id_and_opens_readonly_dialog():
    _app()
    requested_ids = []

    def workspace_factory(contract_id):
        requested_ids.append(contract_id)
        return prepare_contract_document_workspace(
            WorkspacePort(),
            contract_id=contract_id,
        )

    window = PeopleContractsPilot(
        PilotAdapter(),
        contract_document_workspace_factory=workspace_factory,
    )
    try:
        window.people_table.selectRow(0)
        QApplication.processEvents()
        window.contracts_table.selectRow(0)
        QApplication.processEvents()

        assert window.contract_document_button.isEnabled() is True

        def close_dialog():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, ContractDocumentsDialog)
            assert dialog.workspace.contract_id == 417
            assert dialog.document_choice.count() > 0
            labels = [item.text() for item in dialog.findChildren(QLabel)]
            assert any(
                "génération Word / LibreOffice" in text
                for text in labels
            )
            dialog.reject()

        QTimer.singleShot(0, close_dialog)
        window.contract_document_button.click()
        QApplication.processEvents()

        assert requested_ids == [417]
        assert "Documents RH préparés pour le contrat n°417" in window.statusBar().currentMessage()
    finally:
        window.close()


def test_qt_document_widgets_contain_no_sql_or_office_automation():
    pilot_source = (POC / "pilot_view.py").read_text(encoding="utf-8")
    dialog_source = (POC / "contract_documents.py").read_text(encoding="utf-8")
    combined = pilot_source + "\n" + dialog_source

    for forbidden in (
        "SELECT ",
        "UPDATE ",
        "INSERT ",
        "DELETE FROM",
        "win32com",
        "uno.",
        "Dispatch(",
    ):
        assert forbidden not in combined
