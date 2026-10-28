#!/usr/bin/env python3
"""QT-DOC-08: native Windows read-only Qt preview of synthetic HR data.

No database, Office automation, source writes or application secrets.
Screenshots stay in the explicit local output directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "poc" / "qt-theme"))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QTextBrowser

from application.services.contract_document_workspace import (
    ContractDocumentContext,
    prepare_contract_document_workspace,
)
from contract_documents import ContractDocumentsDialog
from domain.documents import DocumentTemplate


class SyntheticPort:
    def __init__(self, paths: tuple[Path, ...]) -> None:
        self.paths = paths

    def load_context(self, contract_id: int) -> ContractDocumentContext:
        if contract_id != 417:
            raise ValueError("Synthetic contract only")
        return ContractDocumentContext(
            structure={"raison_sociale": "Association Exemple"},
            employee={
                "nom": "MARTIN", "prenom": "Lou",
                "civilite": "Mme", "adresse": "1 rue Exemple",
                "code_postal": "35000", "ville": "Rennes",
            },
            contract={
                "date_debut": "01/09/2026",
                "date_fin": "31/08/2027",
                "classification": "Groupe 3",
                "valeur_point": "7,00",
            },
            extra={},
        )

    def list_templates(self) -> tuple[DocumentTemplate, ...]:
        return tuple(
            DocumentTemplate(name=path.name, location=str(path))
            for path in self.paths
        )


def capture(workspace, path: Path, output: Path) -> dict:
    dialog = ContractDocumentsDialog(workspace)
    errors: list[str] = []
    measurements: list[dict] = []

    try:
        idx = next(
            i for i, choice in enumerate(workspace.choices)
            if choice.code == "contract"
        )
        dialog.document_choice.setCurrentIndex(idx)
        templates = workspace.choices[idx].templates
        row = next(
            i for i, template in enumerate(templates)
            if template.location == str(path)
        )
        dialog.templates.setCurrentRow(row)
        if not dialog.preview_button.isEnabled():
            raise RuntimeError(f"Preview button disabled: {path.name}")

        def inspect() -> None:
            modal = QApplication.activeModalWidget()
            try:
                if not isinstance(modal, QDialog):
                    raise RuntimeError("Qt preview modal not found")
                banner = modal.findChild(
                    QLabel, "twdPreviewQualificationBanner"
                )
                browser = modal.findChild(
                    QTextBrowser, "twdPreviewBrowser"
                )
                if banner is None or browser is None:
                    raise RuntimeError("Required preview widgets missing")
                if "NON VALIDÉ POUR SIGNATURE" not in banner.text():
                    raise RuntimeError("Historical example warning missing")
                visible_text = browser.toPlainText()
                if len(visible_text) < 80:
                    raise RuntimeError("Document preview is unexpectedly short")
                png = output / (path.stem + ".png")
                if not modal.grab().save(str(png), "PNG"):
                    raise RuntimeError("Qt screenshot could not be saved")
                labels = [
                    label.text() for label in modal.findChildren(QLabel)
                ]
                measurements.append({
                    "model": path.name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "screenshot": png.name,
                    "text_characters": len(visible_text),
                    "has_example_banner": True,
                    "reports_missing_business_fields": any(
                        "Données métier manquantes" in x for x in labels
                    ),
                    "reports_unmapped_legacy_tokens": any(
                        "Variables historiques sans correspondance" in x
                        for x in labels
                    ),
                })
            except Exception as exc:
                errors.append(str(exc))
            finally:
                if modal is not None:
                    modal.reject()

        def rescue() -> None:
            modal = QApplication.activeModalWidget()
            if modal is not None:
                modal.reject()

        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(rescue)
        timeout.start(6000)
        QTimer.singleShot(200, inspect)
        try:
            dialog.preview_button.click()
        finally:
            timeout.stop()

        if errors:
            raise RuntimeError("; ".join(errors))
        if len(measurements) != 1:
            raise RuntimeError("Preview was not inspected")
        return measurements[0]
    finally:
        dialog.close()
        QApplication.processEvents()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "nt":
        raise RuntimeError("Native Windows required")
    app = QApplication.instance() or QApplication([])
    if app.platformName() != "windows":
        raise RuntimeError(
            f"Expected Qt platform 'windows', got {app.platformName()}"
        )

    directory = ROOT / "teamworks" / "Static" / "Documents"
    paths = tuple(sorted(directory.glob("* - Exemple.twd")))
    if len(paths) != 6:
        raise RuntimeError(f"Expected six historical models, found {len(paths)}")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    workspace = prepare_contract_document_workspace(
        SyntheticPort(paths), contract_id=417
    )
    if not workspace.ok:
        raise RuntimeError("Synthetic workspace preparation failed")

    results = []
    for path in paths:
        item = capture(workspace, path, output)
        results.append(item)
        print(
            "PASS", path.name, "characters", item["text_characters"],
            flush=True,
        )
    (output / "report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("QT_DOC_08_WINDOWS=PASS", flush=True)
    print("OUTPUT=" + str(output), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
