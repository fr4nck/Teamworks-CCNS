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


def test_preview_classifies_known_missing_and_unknown_historical_tokens():
    path = (
        ROOT / "teamworks" / "Static" / "Documents"
        / "Contrat d'engagement éducatif - Exemple.twd"
    )
    before = path.read_bytes()
    preview = preview_twd_template(
        DocumentTemplate(path.name, location=str(path)),
        MergeContext({"SALARIE_NOM": "MARTIN"}),
    )
    assert preview.is_example_template
    assert "SALARIE_DATE_NAISSANCE" in preview.missing_known_fields
    assert "CONTRAT_DUREE_ESSAI_JOURS" in preview.missing_known_fields
    assert "{NBREJOURS}" in preview.unknown_legacy_tokens
    assert "{REPARTITION}" in preview.unknown_legacy_tokens
    assert "{BRUTJOUR}" in preview.unknown_legacy_tokens
    assert all(not field.startswith("{") for field in preview.missing_known_fields)
    assert path.read_bytes() == before


def test_preview_distinguishes_regular_template_from_example(tmp_path):
    path = tmp_path / "document.twd"
    make_twd(path)
    preview = preview_twd_template(
        DocumentTemplate(path.name, location=str(path)),
        MergeContext({}),
    )
    assert preview.is_example_template is False
    assert preview.missing_known_fields == ("SALARIE_NOM",)
    assert preview.unknown_legacy_tokens == ()


def test_qt_preview_displays_example_warning_and_both_field_categories():
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QApplication, QDialog, QLabel, QTextBrowser
    from contract_documents import ContractDocumentsDialog

    path = (
        ROOT / "teamworks" / "Static" / "Documents"
        / "Contrat d'engagement éducatif - Exemple.twd"
    )
    workspace = prepare_contract_document_workspace(
        Port(path), contract_id=417
    )
    app = QApplication.instance() or QApplication([])
    dialog = ContractDocumentsDialog(workspace)
    # Reproduce the dark host theme that previously rendered black
    # historical text on a dark QTextBrowser viewport.
    dialog.setStyleSheet(
        "QTextBrowser { background-color: #2e2e2e; color: #050505; }"
    )
    errors = []
    observed = []

    try:
        index = next(
            i for i, choice in enumerate(workspace.choices)
            if choice.code == "contract"
        )
        dialog.document_choice.setCurrentIndex(index)
        dialog.templates.setCurrentRow(0)
        assert dialog.preview_button.isEnabled()

        def inspect():
            modal = QApplication.activeModalWidget()
            try:
                assert isinstance(modal, QDialog)
                banner = modal.findChild(
                    QLabel, "twdPreviewQualificationBanner"
                )
                assert banner is not None
                assert "NON VALIDÉ POUR SIGNATURE" in banner.text()
                labels = [label.text() for label in modal.findChildren(QLabel)]
                assert any("Données métier manquantes" in x for x in labels)
                assert any("Variables historiques sans correspondance" in x
                           for x in labels)
                browser = modal.findChild(QTextBrowser, "twdPreviewBrowser")
                assert browser is not None
                paper = browser.palette().color(QPalette.ColorRole.Base)
                text = browser.palette().color(QPalette.ColorRole.Text)
                assert paper.name() == "#ffffff"
                assert text.name() == "#111111"
                # Check actual painting, not only palette properties.
                screenshot = browser.viewport().grab().toImage()
                assert screenshot.width() > 20 and screenshot.height() > 20
                pixel = screenshot.pixelColor(8, 8)
                assert min(pixel.red(), pixel.green(), pixel.blue()) >= 245
                observed.append(True)
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
        timeout.start(3000)
        QTimer.singleShot(0, inspect)
        try:
            dialog.preview_button.click()
        finally:
            timeout.stop()
        assert not errors, errors
        assert observed
    finally:
        dialog.close()
        app.processEvents()
