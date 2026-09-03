from __future__ import annotations

import sys
import time

STARTED_AT = time.perf_counter()

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from domain_read_adapter import build_domain_smoke_adapter
from frugality import DIRECT_DEPENDENCIES, FrugalityProbe
from pilot_view import PeopleContractsPilot
from theme_engine import ThemeEngine


def main() -> None:
    probe = FrugalityProbe(started_at=STARTED_AT)

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Teamworks Qt POC")
    qt_app.setOrganizationName("Pêle-Mêle Sports et Loisirs")

    theme_engine = ThemeEngine(qt_app)
    theme_engine.apply(dark=False)

    # Écran pilote vNext : aucune donnée factice dans la vue. Le modèle Qt reçoit
    # uniquement des vues normalisées depuis l'adaptateur lecture seule.
    adapter = build_domain_smoke_adapter()
    window = PeopleContractsPilot(adapter)
    window.show()

    def report_frugality() -> None:
        snapshot = probe.snapshot(direct_dependencies=len(DIRECT_DEPENDENCIES))
        print(f"[Teamworks Qt POC] {snapshot.compact()}")
        window.statusBar().showMessage(
            f"{snapshot.compact()} · lecture seule · QAbstractTableModel + proxy"
        )

    QTimer.singleShot(350, report_frugality)
    raise SystemExit(qt_app.exec())


if __name__ == "__main__":
    main()
