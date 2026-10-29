#!/usr/bin/env python3
"""Capture the real Qt pilot with in-memory fixtures, never a user database.

Runs once per process so QT_SCALE_FACTOR is applied before QApplication exists.
The captures are synthetic offscreen previews, not a Windows visual acceptance.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
for module_path in (ROOT, ROOT / "teamworks", POC):
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))


def capture(output: Path, expected_scale: str) -> None:
    if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
        raise RuntimeError("This recipe must use Qt offscreen; never control the real desktop")
    if os.environ.get("QT_SCALE_FACTOR") != expected_scale:
        raise RuntimeError("QT_SCALE_FACTOR must be set before QApplication starts")

    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication
    from domain_read_adapter import build_domain_smoke_adapter
    from pilot_generalities import PeopleContractsGeneralitiesPilot
    from theme_engine import ThemeEngine

    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Teamworks Qt visual proof — fake data")
    ThemeEngine(app).apply(dark=False)
    window = PeopleContractsGeneralitiesPilot(build_domain_smoke_adapter())
    measurements = []
    try:
        window.show()
        app.processEvents()
        window.people_table.selectRow(0)
        app.processEvents()
        if window.detail_stack.currentIndex() != 1:
            raise AssertionError("The fake individual record did not open")

        for width, height in ((900, 620), (1380, 860)):
            window.resize(width, height)
            app.processEvents()
            nav = window.section_navigation
            expected_columns = 2 if width == 900 else 4
            if nav.columns != expected_columns:
                raise AssertionError(
                    f"At {width}px, expected {expected_columns} navigation columns, got {nav.columns}"
                )
            if len(window.section_buttons) != 8:
                raise AssertionError("Eight sections must be accessible")
            button_widths = {}
            for button in window.section_buttons:
                label = button.text()
                minimum = button.fontMetrics().horizontalAdvance(label) + 8
                if not button.isVisible() or button.width() <= minimum:
                    raise AssertionError(
                        f"Section '{label}' clipped at {width}px: {button.width()} <= {minimum}"
                    )
                if not nav.rect().contains(button.geometry()):
                    raise AssertionError(f"Section '{label}' outside navigation area")
                button_widths[label] = button.width()

            for section, section_name in ((0, "generalites"), (3, "contrats")):
                window.tabs.setCurrentIndex(section)
                app.processEvents()
                if not window.section_buttons[section].isChecked():
                    raise AssertionError(f"Selected section {section_name} is not checked")
                if not window.people_table.isVisible():
                    raise AssertionError("People list missing from visible screen")
                if section == 3:
                    if not window.contracts_table.isVisible():
                        raise AssertionError("Contracts table missing from visible screen")
                    if window.contracts_table.height() < 160:
                        raise AssertionError("Contracts table compressed below its readable minimum")
                    table_y = window.contracts_table.mapToGlobal(QPoint(0, 0)).y()
                    buttons_y = max(
                        button.mapToGlobal(QPoint(0, 0)).y() + button.height()
                        for button in (
                            window.contract_create_button, window.contract_edit_button,
                            window.contract_delete_button, window.contract_signature_button,
                            window.contract_due_button, window.contract_document_button,
                        )
                    )
                    if buttons_y > table_y:
                        raise AssertionError("Contracts command rows overlap the table")
                    if width == 900 and window.contracts_scroll.verticalScrollBar().maximum() <= 0:
                        raise AssertionError("Short contracts tab must offer vertical scrolling")
                image = window.grab()
                if image.isNull():
                    raise AssertionError("Qt returned an empty capture")
                filename = f"qt-{width}x{height}-{section_name}.png"
                if not image.save(str(output / filename), "PNG"):
                    raise RuntimeError(f"Cannot save {filename}")
                measurements.append(
                    {
                        "image": filename,
                        "window_logical_px": [window.width(), window.height()],
                        "image_physical_px": [image.width(), image.height()],
                        "device_pixel_ratio": image.devicePixelRatio(),
                        "navigation_logical_px": nav.width(),
                        "navigation_columns": nav.columns,
                        "button_widths_logical_px": button_widths,
                        "people_table_logical_px": window.people_table.width(),
                        "contracts_table_logical_px": window.contracts_table.width(),
                    }
                )
    finally:
        window.close()
        app.processEvents()

    report = {
        "purpose": "offscreen visual evidence — human Windows acceptance still required",
        "data_source": "in-memory synthetic domain smoke adapter (no SQL)",
        "qt_platform": os.environ["QT_QPA_PLATFORM"],
        "requested_scale_factor": expected_scale,
        "measurements": measurements,
    }
    (output / "measurements.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Qt visual proof: {len(measurements)} captures at scale {expected_scale}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale", choices=("1", "1.25", "1.5"), required=True)
    args = parser.parse_args()
    capture(args.output, args.scale)


if __name__ == "__main__":
    main()
