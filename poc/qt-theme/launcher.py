from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

import app as legacy_poc_ui
from data_adapter import DemoAdapter
from theme_engine import ThemeEngine


def main() -> None:
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

    # Première preuve de frontière métier : l'UI ne voit qu'un adaptateur de
    # lecture. Aucune base, aucun repository production, aucun wxPython.
    adapter = DemoAdapter()
    demo_people = adapter.list_people()

    window = legacy_poc_ui.MainWindow(qt_app)
    window.statusBar().showMessage(
        f"POC isolé · moteur de thème central · adaptateur lecture OK ({len(demo_people)} fiches factices)"
    )
    window.show()
    raise SystemExit(qt_app.exec())


if __name__ == "__main__":
    main()
