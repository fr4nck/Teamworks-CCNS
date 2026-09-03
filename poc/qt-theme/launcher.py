from __future__ import annotations

import os
import sys
import time

STARTED_AT = time.perf_counter()

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from domain_read_adapter import build_domain_smoke_adapter
from frugality import DIRECT_DEPENDENCIES, FrugalityProbe
from pilot_view import PeopleContractsPilot
from theme_engine import ThemeEngine


def build_adapter():
    source = os.environ.get("TEAMWORKS_QT_SOURCE", "smoke").strip().lower()
    if source == "production":
        from production_read_adapter import build_production_adapter

        return build_production_adapter(), "production"
    if source != "smoke":
        raise ValueError("TEAMWORKS_QT_SOURCE doit valoir 'smoke' ou 'production'")
    return build_domain_smoke_adapter(), "smoke"


def main() -> None:
    probe = FrugalityProbe(started_at=STARTED_AT)

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Teamworks Qt POC")
    qt_app.setOrganizationName("Pêle-Mêle Sports et Loisirs")

    theme_engine = ThemeEngine(qt_app)
    theme_engine.apply(dark=False)

    adapter, source = build_adapter()
    window = None
    try:
        window = PeopleContractsPilot(adapter)
        window.show()

        def report_frugality() -> None:
            snapshot = probe.snapshot(direct_dependencies=len(DIRECT_DEPENDENCIES))
            print(f"[Teamworks Qt POC] source={source} · {snapshot.compact()}")
            window.statusBar().showMessage(
                f"{snapshot.compact()} · lecture seule · source {source} · QAbstractTableModel + proxy"
            )

        QTimer.singleShot(350, report_frugality)
        raise SystemExit(qt_app.exec())
    finally:
        close = getattr(adapter, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
