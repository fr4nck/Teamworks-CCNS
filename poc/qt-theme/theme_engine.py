from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet


@dataclass(frozen=True)
class ThemeTokens:
    primary: str
    surface: str
    surface_container: str
    surface_container_high: str
    on_surface: str
    on_surface_variant: str
    outline: str
    success: str
    warning: str
    danger: str
    selection: str


LIGHT = ThemeTokens(
    primary="#0f6cbd",
    surface="#f7f9fb",
    surface_container="#ffffff",
    surface_container_high="#eef3f8",
    on_surface="#1f1f1f",
    on_surface_variant="#5b5b5b",
    outline="#d1d6dc",
    success="#107c10",
    warning="#8a6d00",
    danger="#c42b1c",
    selection="#dcecff",
)

DARK = ThemeTokens(
    primary="#75b6e7",
    surface="#16191d",
    surface_container="#1f2328",
    surface_container_high="#292e35",
    on_surface="#f2f2f2",
    on_surface_variant="#b8bcc2",
    outline="#414851",
    success="#54b054",
    warning="#d8b84b",
    danger="#ff8075",
    selection="#23486b",
)


class ThemeEngine:
    """Petit moteur de thème isolé du POC.

    Qt Material n'est utilisé que comme couche de base. Les rôles métier et les
    surfaces Teamworks vivent ici afin de pouvoir remplacer le moteur plus tard
    sans réécrire chaque écran.
    """

    def __init__(self, app: QApplication):
        self.app = app
        self.dark = False

    @property
    def tokens(self) -> ThemeTokens:
        return DARK if self.dark else LIGHT

    def apply(self, dark: bool = False) -> None:
        self.dark = dark
        theme = "dark_blue.xml" if dark else "light_blue.xml"
        apply_stylesheet(
            self.app,
            theme=theme,
            extra={"density_scale": "0", "font_family": "Segoe UI"},
        )
        t = self.tokens
        self.app.setStyleSheet(
            self.app.styleSheet()
            + f"""
            QMainWindow, QWidget {{
                color: {t.on_surface};
            }}
            QFrame#navigation {{
                background: {t.surface_container};
                border-right: 1px solid {t.outline};
            }}
            QFrame#panel, QFrame#metricCard, QFrame#warningCard {{
                background: {t.surface_container};
                border: 1px solid {t.outline};
                border-radius: 8px;
            }}
            QFrame#commandBar {{
                background: {t.surface_container_high};
                border: 1px solid {t.outline};
                border-radius: 7px;
            }}
            QFrame#personSummary {{
                background: {t.surface_container_high};
                border: 1px solid {t.outline};
                border-radius: 8px;
            }}
            QLabel#personAvatar {{
                background: {t.selection};
                color: {t.primary};
                border: 1px solid {t.outline};
                border-radius: 29px;
                font-size: 17px;
                font-weight: 700;
            }}
            QLabel#personSummaryName {{
                font-size: 16px;
                font-weight: 600;
            }}
            QFrame#alertRow {{
                background: {t.surface_container_high};
                border-radius: 6px;
            }}
            QLabel[muted="true"] {{
                color: {t.on_surface_variant};
            }}
            QLabel#statusBadge {{
                padding: 6px 10px;
                background: {t.surface_container_high};
                border: 1px solid {t.outline};
                border-radius: 8px;
                font-weight: 600;
            }}
            QLabel#complianceStatus {{
                padding: 8px 10px;
                background: {t.surface_container_high};
                border: 1px solid {t.outline};
                border-radius: 7px;
                font-weight: 600;
            }}
            QLabel#complianceStatus[complianceState="pending"] {{
                color: {t.on_surface_variant};
                border-color: {t.outline};
            }}
            QLabel#complianceStatus[complianceState="compliant"] {{
                color: {t.success};
                border-color: {t.success};
            }}
            QLabel#complianceStatus[complianceState="non_compliant"] {{
                color: {t.danger};
                border-color: {t.danger};
            }}
            QLabel#roundBadge {{
                background: {t.warning};
                color: {t.surface_container};
                border-radius: 12px;
                font-weight: 700;
            }}
            QTableView, QTableWidget {{
                background: {t.surface_container};
                alternate-background-color: {t.surface_container_high};
                gridline-color: {t.outline};
                selection-background-color: {t.selection};
                selection-color: {t.on_surface};
                border: 0;
            }}
            QHeaderView::section {{
                background: {t.surface_container_high};
                border: 0;
                border-right: 1px solid {t.outline};
                border-bottom: 1px solid {t.outline};
                padding: 6px;
                font-weight: 600;
            }}
            QTabWidget::pane {{
                border: 0;
            }}
            """
        )
