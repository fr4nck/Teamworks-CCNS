from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from application.services.contract_document_workspace import (
    ContractDocumentContext,
    prepare_contract_document_workspace,
)
from document_preview_adapter import preview_twd_template
from domain.documents import DocumentTemplate, MergeContext


def make_twd(path):
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<richtext version="1.0.0.0" '
        'xmlns="http://www.wxwidgets.org">'
        '<paragraphlayout><paragraph>'
        '<text>Bonjour {NOM}</text>'
        '</paragraph></paragraphlayout>'
        '</richtext>',
        encoding="utf-8",
    )


class Port:
    def __init__(self, path):
        self.template = DocumentTemplate(
            name=path.name, location=str(path)
        )

    def load_context(self, contract_id):
        assert contract_id == 417
        return ContractDocumentContext(
            structure={"raison_sociale": "Association Test"},
            employee={"nom": "DUPONT", "prenom": "Lou"},
            contract={"date_debut": "01/09/2026"},
            extra={},
        )

    def list_templates(self):
        return (self.template,)


def test_preview_is_readonly_and_resolves_legacy_field(tmp_path):
    path = tmp_path / "contrat.twd"
    make_twd(path)
    before = path.read_bytes()

    preview = preview_twd_template(
        DocumentTemplate(path.name, location=str(path)),
        MergeContext({"SALARIE_NOM": "DUPONT"}),
    )

    assert "DUPONT" in preview.html
    assert preview.unresolved_fields == ()
    assert path.read_bytes() == before


def test_preview_reports_unresolved_field(tmp_path):
    path = tmp_path / "contrat.twd"
    make_twd(path)

    preview = preview_twd_template(
        DocumentTemplate(path.name, location=str(path)),
        MergeContext({}),
    )

    assert preview.unresolved_fields == ("SALARIE_NOM",)
    assert "SALARIE_NOM" in preview.html


def test_preview_rejects_other_formats(tmp_path):
    path = tmp_path / "contrat.doc"
    with pytest.raises(ValueError, match="TWD"):
        preview_twd_template(
            DocumentTemplate(path.name, location=str(path)),
            MergeContext({}),
        )


def test_qt_dialog_opens_fused_preview(tmp_path):
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import (
        QApplication, QDialog, QTextBrowser,
    )
    from contract_documents import ContractDocumentsDialog

    path = tmp_path / "contrat.twd"
    make_twd(path)

    workspace = prepare_contract_document_workspace(
        Port(path), contract_id=417
    )
    assert workspace.ok
    assert workspace.merge_context is not None
    assert workspace.merge_context.get("SALARIE_NOM") == "DUPONT"

    app = QApplication.instance() or QApplication([])
    dialog = ContractDocumentsDialog(workspace)

    try:
        index = next(
            i for i, choice in enumerate(workspace.choices)
            if choice.code == "contract"
        )
        dialog.document_choice.setCurrentIndex(index)
        dialog.templates.setCurrentRow(0)

        assert dialog.preview_button.isEnabled()

        observed = []
        errors = []

        def inspect():
            modal = QApplication.activeModalWidget()
            try:
                assert isinstance(modal, QDialog)
                browser = modal.findChild(
                    QTextBrowser, "twdPreviewBrowser"
                )
                assert browser is not None
                observed.append(browser.toPlainText())
            except Exception as exc:
                errors.append(exc)
            finally:
                if modal is not None:
                    modal.reject()

        def rescue():
            modal = QApplication.activeModalWidget()
            if modal is not None:
                modal.reject()

        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(rescue)
        timeout.start(2000)

        QTimer.singleShot(0, inspect)
        try:
            dialog.preview_button.click()
        finally:
            timeout.stop()

        assert not errors, errors
        assert observed
        assert "DUPONT" in observed[0]
        assert path.exists()
    finally:
        dialog.close()
        app.processEvents()
