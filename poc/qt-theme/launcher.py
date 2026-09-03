from __future__ import annotations

import sys
import time

STARTED_AT = time.perf_counter()

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

import app as legacy_poc_ui
from data_adapter import DemoAdapter
from domain_read_adapter import build_domain_smoke_adapter
from frugality import DIRECT_DEPENDENCIES, FrugalityProbe
from theme_engine import ThemeEngine


def main() -> None:
    probe = FrugalityProbe(started_at=STARTED_AT)

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Teamworks Qt POC")
    qt_app.setOrganizationName("Pêle-Mêle Sports et Loisirs")

    theme_engine = ThemeEngine(qt_app)

    # Le gros fichier app.py reste volontairement un stress-test UI jetable.
    # On remplace son ancien helper de thème par le moteur central sans devoir
    # réécrire toutes les fenêtres pour valider l'architecture.
    def apply_theme(_app: QApplication, dark: bool) -> None:
        theme_engine.apply(dark=dark)

    legacy_poc_ui.apply_teamworks_theme = apply_theme
    theme_engine.apply(dark=False)

    # Deux validations en parallèle :
    # 1) l'adaptateur factice continue d'alimenter le stress-test visuel ;
    # 2) un adaptateur séparé consomme déjà les vraies classes domaine/repository.
    demo_adapter = DemoAdapter()
    demo_people = demo_adapter.list_people()
    domain_adapter = build_domain_smoke_adapter()
    domain_people = domain_adapter.list_people()

    window = legacy_poc_ui.MainWindow(qt_app)
    window.statusBar().showMessage(
        "POC isolé · thème central · "
        f"UI démo {len(demo_people)} fiches · domaine Teamworks {len(domain_people)} fiches"
    )
    window.show()

    # Mesure après le premier affichage, sans dépendance type psutil.
    def report_frugality() -> None:
        snapshot = probe.snapshot(direct_dependencies=len(DIRECT_DEPENDENCIES))
        print(f"[Teamworks Qt POC] {snapshot.compact()}")
        window.statusBar().showMessage(
            f"{snapshot.compact()} · domaine Teamworks branché en lecture seule"
        )

    QTimer.singleShot(350, report_frugality)
    raise SystemExit(qt_app.exec())


if __name__ == "__main__":
    main()
