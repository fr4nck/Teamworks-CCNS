"""Prototype Qt isolé du core documentaire PMSL/Teamworks.

Lancer depuis la racine : python poc/qt-theme/document_editor_demo.py
PySide6 n'est importé que dans run(); le core reste importable sans Qt.
"""
from __future__ import annotations

import html
import sys
from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path

from domain.documents import DEFAULT_DOCUMENT_FIELD_REGISTRY, DocumentMetadata, DocumentModel, HtmlMergeRenderer, MergeContext, sanitize_html

_FIELD_HREF_PREFIX = "pmsl-field:"


class _ProjectionParser(HTMLParser):
    def __init__(self, to_editor: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.to_editor = to_editor
        self.parts: list[str] = []
        self.field_depth = 0
        self.field_key = ""

    def handle_starttag(self, tag, attrs):
        if self.field_depth:
            self.field_depth += 1
            return
        values = {key.lower(): value for key, value in attrs if value is not None}
        if self.to_editor and tag == "span" and values.get("data-pmsl-field"):
            raw = values["data-pmsl-field"].strip().upper()
            field = DEFAULT_DOCUMENT_FIELD_REGISTRY.get(raw)
            self.field_key = field.key if field else raw
            label = field.label if field else raw
            self.parts.append(f'<a href="{_FIELD_HREF_PREFIX}{html.escape(self.field_key, quote=True)}">[{html.escape(label)}]</a>')
            self.field_depth = 1
            return
        if not self.to_editor and tag == "a" and values.get("href", "").startswith(_FIELD_HREF_PREFIX):
            raw = values["href"][len(_FIELD_HREF_PREFIX):].strip().upper()
            field = DEFAULT_DOCUMENT_FIELD_REGISTRY.get(raw)
            self.field_key = field.key if field else raw
            self.field_depth = 1
            return
        self._copy_start(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        if not self.field_depth:
            self._copy_start(tag, attrs)

    def handle_endtag(self, tag):
        if self.field_depth:
            self.field_depth -= 1
            if not self.to_editor and self.field_depth == 0:
                key = self.field_key
                self.parts.append(f'<span data-pmsl-field="{html.escape(key, quote=True)}">{{{html.escape(key)}}}</span>')
            return
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.field_depth:
            self.parts.append(html.escape(data, quote=False))

    def _copy_start(self, tag, attrs):
        attr_text = "".join(f' {name}="{html.escape(value, quote=True)}"' for name, value in attrs if value is not None)
        self.parts.append(f"<{tag}{attr_text}>")


def canonical_to_editor_html(canonical_html: str) -> str:
    parser = _ProjectionParser(True); parser.feed(canonical_html); parser.close(); return "".join(parser.parts)


def editor_to_canonical_html(editor_html: str) -> str:
    parser = _ProjectionParser(False); parser.feed(editor_html); parser.close(); return sanitize_html("".join(parser.parts))


def run() -> int:
    from PySide6.QtGui import QAction, QTextCharFormat
    from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QInputDialog, QMainWindow, QMessageBox, QTextBrowser, QTextEdit, QToolBar, QVBoxLayout

    class Window(QMainWindow):
        def __init__(self) -> None:
            super().__init__(); self.setWindowTitle("POC — Core documentaire PMSL / Teamworks Qt"); self.resize(980, 720)
            self.editor = QTextEdit(self); self.setCentralWidget(self.editor); self.path: Path | None = None
            self.document = DocumentModel.create(document_type="contract", html="<p>Commencez la saisie…</p>", metadata=DocumentMetadata(title="Document de démonstration", owner_domain="rh"))
            self.editor.setHtml(canonical_to_editor_html(self.document.html)); self._toolbar()

        def _toolbar(self):
            bar = QToolBar("Document", self); self.addToolBar(bar)
            def add(label, slot, checkable=False):
                action = QAction(label, self); action.setCheckable(checkable); action.triggered.connect(slot); bar.addAction(action)
            add("Nouveau", self.new); add("Ouvrir", self.open); add("Enregistrer", self.save); bar.addSeparator(); add("Gras", self.bold, True); add("Italique", self.italic, True); bar.addSeparator(); add("Insérer un champ", self.insert_field); add("Aperçu fusionné", self.preview)

        def current_document(self):
            return replace(self.document, html=editor_to_canonical_html(self.editor.toHtml()))

        def new(self):
            self.path = None; self.document = DocumentModel.create(document_type="contract", html="<p></p>"); self.editor.clear()

        def open(self):
            filename, _ = QFileDialog.getOpenFileName(self, "Ouvrir", "", "Document PMSL (*.json)")
            if not filename: return
            try: self.document = DocumentModel.from_json(Path(filename).read_text(encoding="utf-8"))
            except Exception as exc: QMessageBox.critical(self, "Ouverture impossible", str(exc)); return
            self.path = Path(filename); self.editor.setHtml(canonical_to_editor_html(self.document.html))

        def save(self):
            if self.path is None:
                filename, _ = QFileDialog.getSaveFileName(self, "Enregistrer", "document.json", "Document PMSL (*.json)")
                if not filename: return
                self.path = Path(filename)
            self.document = self.current_document(); self.path.write_text(self.document.to_json() + "\n", encoding="utf-8")

        def bold(self, checked):
            fmt = QTextCharFormat(); fmt.setFontWeight(700 if checked else 400); self.editor.mergeCurrentCharFormat(fmt)

        def italic(self, checked):
            fmt = QTextCharFormat(); fmt.setFontItalic(checked); self.editor.mergeCurrentCharFormat(fmt)

        def insert_field(self):
            fields = DEFAULT_DOCUMENT_FIELD_REGISTRY.list_fields(context="contract"); labels = [f"{f.label} — {f.key}" for f in fields]
            selected, ok = QInputDialog.getItem(self, "Insérer un champ métier", "Champ :", labels, 0, False)
            if not ok: return
            field = fields[labels.index(selected)]; self.editor.textCursor().insertHtml(f'<a href="{_FIELD_HREF_PREFIX}{field.key}">[{html.escape(field.label)}]</a> ')

        def preview(self):
            result = HtmlMergeRenderer().render(self.current_document(), MergeContext({"SALARIE_PRENOM": "Marie", "SALARIE_NOM": "DUPONT", "CONTRAT_DATE_DEBUT": "01/10/2026"}))
            dialog = QDialog(self); dialog.setWindowTitle("Aperçu fusionné"); dialog.resize(800, 650); layout = QVBoxLayout(dialog); view = QTextBrowser(dialog); view.setOpenExternalLinks(False); view.setHtml(result.content); layout.addWidget(view); dialog.exec()

    app = QApplication(sys.argv); window = Window(); window.show(); return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
