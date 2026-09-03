from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

from generalities_satellites import (
    CitiesPreviewDialog,
    CoordinatesPreviewDialog,
    CountriesPreviewDialog,
    SocialSituationsPreviewDialog,
)
from theme_engine import ThemeEngine
from ui.common.tokens import TOKENS, apply_typography


class SatellitesGallery(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Teamworks Qt — satellites Généralités")
        self.resize(520, 380)

        root = QVBoxLayout(self)
        root.setContentsMargins(*(TOKENS.spacing.lg,) * 4)
        root.setSpacing(TOKENS.spacing.sm)

        title = QLabel("Satellites de Généralités")
        apply_typography(title, TOKENS.typography.page_title)
        root.addWidget(title)

        note = QLabel("Galerie de recette visuelle · aucune écriture en base")
        note.setProperty("muted", True)
        root.addWidget(note)

        entries = (
            ("Coordonnées", CoordinatesPreviewDialog),
            ("Villes", CitiesPreviewDialog),
            ("Pays / Nationalités", CountriesPreviewDialog),
            ("Situations sociales", SocialSituationsPreviewDialog),
        )
        for label, dialog_cls in entries:
            button = QPushButton(label)
            button.setMinimumHeight(TOKENS.controls.height_toolbar)
            button.clicked.connect(lambda _checked=False, cls=dialog_cls: cls(self).exec())
            root.addWidget(button)
        root.addStretch(1)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    ThemeEngine(app).apply(dark=False)
    window = SatellitesGallery()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
