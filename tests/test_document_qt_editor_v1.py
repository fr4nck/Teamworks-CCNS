import importlib.util
import os
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "poc" / "qt-theme" / "document_editor_demo.py"
spec = importlib.util.spec_from_file_location("document_editor_demo", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_qt_editor_projection_preserves_canonical_field_identity_without_qt_runtime():
    canonical = '<p><span data-pmsl-field="SALARIE_NOM">{SALARIE_NOM}</span></p>'
    editor_html = module.canonical_to_editor_html(canonical)
    restored = module.editor_to_canonical_html(editor_html)
    assert 'href="pmsl-field:SALARIE_NOM"' in editor_html
    assert "[Nom du salarié]" in editor_html
    assert 'data-pmsl-field="SALARIE_NOM"' in restored


def test_qt_projection_does_not_leak_editor_anchor_into_canonical_html():
    canonical = module.editor_to_canonical_html('<p><a href="pmsl-field:SALARIE_PRENOM">[Prénom]</a></p>')
    assert "pmsl-field:" not in canonical
    assert 'data-pmsl-field="SALARIE_PRENOM"' in canonical


def test_qtextedit_round_trip_preserves_pmsl_field_anchor():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QTextEdit
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    editor = QTextEdit(); editor.setHtml('<p><a href="pmsl-field:SALARIE_NOM">[Nom du salarié]</a></p>')
    exported = editor.toHtml()
    assert "pmsl-field:SALARIE_NOM" in exported and "Nom du salarié" in exported
    editor.deleteLater(); app.processEvents()
