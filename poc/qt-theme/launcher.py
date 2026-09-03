from __future__ import annotations

import os
import sys
import time
import traceback

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
        before_window = time.perf_counter()
        window = PeopleContractsPilot(adapter)
        after_window = time.perf_counter()
        window.show()
        shown_at = time.perf_counter()

        data_seconds = float(getattr(window, "initial_people_load_seconds", 0.0))
        constructor_seconds = after_window - before_window
        ui_constructor_seconds = max(0.0, constructor_seconds - data_seconds)
        foundation_seconds = max(0.0, before_window - STARTED_AT)
        total_to_show_seconds = shown_at - STARTED_AT

        def report_frugality() -> None:
            snapshot = probe.snapshot(direct_dependencies=len(DIRECT_DEPENDENCIES))
            timing = (
                f"socle {foundation_seconds:.2f}s · données serveur {data_seconds:.2f}s · "
                f"construction UI {ui_constructor_seconds:.2f}s · fenêtre {total_to_show_seconds:.2f}s"
            )
            print(f"[Teamworks Qt POC] source={source} · {snapshot.compact()}")
            print(f"[Teamworks Qt POC] détail démarrage · {timing}")
            window.statusBar().showMessage(
                f"{snapshot.compact()} · {timing} · lecture seule · source {source}"
            )

        QTimer.singleShot(350, report_frugality)
        raise SystemExit(qt_app.exec())
    finally:
        close = getattr(adapter, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("[Teamworks Qt POC] Erreur fatale : traceback complet ci-dessous", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)
