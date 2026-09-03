from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from ui.common.tokens import TOKENS


@dataclass(frozen=True)
class ThemeTokens:
    primary: str
    on_primary: str
    surface: str
    surface_container_lowest: str
    surface_container: str
    surface_container_high: str
    on_surface: str
    on_surface_variant: str
    outline: str
    outline_variant: str
    focus: str
    disabled: str
    success: str
    warning: str
    danger: str
    selection: str
    selection_text: str


LIGHT = ThemeTokens(
    primary="#0f6cbd",
    on_primary="#ffffff",
    surface="#f7f9fb",
    surface_container_lowest="#ffffff",
    surface_container="#ffffff",
    surface_container_high="#eef3f8",
    on_surface="#1f1f1f",
    on_surface_variant="#5b5b5b",
    outline="#d1d6dc",
    outline_variant="#e1e5ea",
    focus="#0f6cbd",
    disabled="#8a8a8a",
    success="#107c10",
    warning="#8a6d00",
    danger="#c42b1c",
    selection="#dcecff",
    selection_text="#1f1f1f",
)

DARK = ThemeTokens(
    primary="#75b6e7",
    on_primary="#102238",
    surface="#16191d",
    surface_container_lowest="#1b1f24",
    surface_container="#1f2328",
    surface_container_high="#292e35",
    on_surface="#f2f2f2",
    on_surface_variant="#b8bcc2",
    outline="#414851",
    outline_variant="#343a42",
    focus="#75b6e7",
    disabled="#858b93",
    success="#54b054",
    warning="#d8b84b",
    danger="#ff8075",
    selection="#23486b",
    selection_text="#f2f2f2",
)


class ThemeEngine:
    """Moteur de thème isolé du POC.

    Qt Material n'est utilisé que comme couche de base. Les rôles métier, les
    surfaces et les états Teamworks vivent ici afin de pouvoir remplacer le
    moteur plus tard sans réécrire chaque écran.
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
        r = TOKENS.radius
        c = TOKENS.controls
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
                border-radius: {r.panel}px;
            }}
            QFrame#commandBar {{
                background: {t.surface_container_high};
                border: 1px solid {t.outline};
                border-radius: {r.panel}px;
            }}
            QFrame#twFormSection, QFrame#twCrudPanel {{
                background: {t.surface_container};
                border: 1px solid {t.outline_variant};
                border-radius: {r.dialog_section}px;
            }}
            QFrame#twDialogContent {{
                background: transparent;
                border: 0;
            }}
            QFrame#personSummary {{
                background: {t.surface_container};
                border: 0;
                border-bottom: 1px solid {t.outline};
                border-radius: 0;
            }}
            QLabel#personAvatar {{
                background: {t.selection};
                color: {t.primary};
                border: 1px solid {t.outline};
                border-radius: 48px;
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#personSummaryName {{
                font-size: 18px;
                font-weight: 600;
            }}
            QLabel#twDialogTitle, QLabel#twSectionTitle {{
                background: transparent;
            }}
            QLabel[muted="true"] {{
                color: {t.on_surface_variant};
            }}

            QToolButton#legacyToolButton,
            QToolButton#twActionButton,
            QToolButton#twChoiceButton,
            QPushButton#twSecondaryButton {{
                min-height: {c.height_standard}px;
                background: {t.surface_container_lowest};
                color: {t.on_surface};
                border: 1px solid {t.outline_variant};
                border-radius: {r.button}px;
                padding: 4px 8px;
            }}
            QToolButton#twActionButton[twDensity="compact"],
            QToolButton#twChoiceButton[twDensity="compact"],
            QPushButton#twSecondaryButton[twDensity="compact"] {{
                min-height: {c.height_compact}px;
                max-height: {c.height_compact}px;
                padding: 2px 6px;
            }}
            QToolButton#legacyToolButton:hover,
            QToolButton#twActionButton:hover,
            QToolButton#twChoiceButton:hover,
            QPushButton#twSecondaryButton:hover {{
                background: {t.surface_container_high};
                border-color: {t.outline};
            }}
            QToolButton#legacyToolButton:pressed,
            QToolButton#twActionButton:pressed,
            QToolButton#twChoiceButton:pressed,
            QPushButton#twSecondaryButton:pressed {{
                background: {t.selection};
                border-color: {t.focus};
            }}
            QToolButton#twChoiceButton:checked {{
                background: {t.selection};
                color: {t.selection_text};
                border-color: {t.focus};
            }}
            QToolButton#twActionButton[actionRole="destructive"] {{
                color: {t.danger};
            }}
            QToolButton#legacyToolButton:focus,
            QToolButton#twActionButton:focus,
            QToolButton#twChoiceButton:focus,
            QPushButton#twSecondaryButton:focus,
            QPushButton#twPrimaryButton:focus {{
                border: 2px solid {t.focus};
            }}
            QToolButton#legacyToolButton:disabled,
            QToolButton#twActionButton:disabled,
            QToolButton#twChoiceButton:disabled,
            QPushButton#twSecondaryButton:disabled {{
                background: {t.surface_container_high};
                color: {t.disabled};
                border-color: {t.outline_variant};
            }}
            QPushButton#twPrimaryButton {{
                min-height: {c.height_standard}px;
                background: {t.primary};
                color: {t.on_primary};
                border: 1px solid {t.primary};
                border-radius: {r.button}px;
                padding: 4px 12px;
                font-weight: 600;
            }}
            QPushButton#twPrimaryButton:hover {{
                border-color: {t.focus};
            }}
            QPushButton#twPrimaryButton:pressed {{
                background: {t.selection};
                color: {t.selection_text};
            }}
            QPushButton#twPrimaryButton:disabled {{
                background: {t.surface_container_high};
                color: {t.disabled};
                border-color: {t.outline_variant};
            }}

            QLineEdit,
            QComboBox,
            QDateEdit,
            QTimeEdit,
            QSpinBox,
            QDoubleSpinBox,
            QPlainTextEdit,
            QTextEdit {{
                min-height: {c.height_standard}px;
                background: {t.surface_container_lowest};
                color: {t.on_surface};
                border: 1px solid {t.outline_variant};
                border-radius: {r.field}px;
                selection-background-color: {t.selection};
                selection-color: {t.selection_text};
            }}
            QLineEdit[twDensity="compact"],
            QComboBox[twDensity="compact"],
            QDateEdit[twDensity="compact"],
            QTimeEdit[twDensity="compact"],
            QSpinBox[twDensity="compact"],
            QDoubleSpinBox[twDensity="compact"] {{
                min-height: {c.height_compact}px;
                max-height: {c.height_compact}px;
            }}
            QLineEdit[twReadOnly="true"],
            QPlainTextEdit[twReadOnly="true"],
            QTextEdit[twReadOnly="true"] {{
                background: {t.surface_container};
            }}
            QLineEdit:hover,
            QComboBox:hover,
            QDateEdit:hover,
            QTimeEdit:hover,
            QSpinBox:hover,
            QDoubleSpinBox:hover,
            QPlainTextEdit:hover,
            QTextEdit:hover {{
                background: {t.surface_container_high};
                border-color: {t.outline};
            }}
            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus,
            QTimeEdit:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus,
            QPlainTextEdit:focus,
            QTextEdit:focus {{
                border: 2px solid {t.focus};
            }}
            QLineEdit:disabled,
            QComboBox:disabled,
            QDateEdit:disabled,
            QTimeEdit:disabled,
            QSpinBox:disabled,
            QDoubleSpinBox:disabled,
            QPlainTextEdit:disabled,
            QTextEdit:disabled {{
                background: {t.surface_container_high};
                color: {t.disabled};
                border-color: {t.outline_variant};
            }}

            QLineEdit[validationState="error"],
            QComboBox[validationState="error"],
            QDateEdit[validationState="error"],
            QSpinBox[validationState="error"],
            QDoubleSpinBox[validationState="error"],
            QPlainTextEdit[validationState="error"],
            QTextEdit[validationState="error"] {{ border-color: {t.danger}; }}

            QLineEdit[validationState="warning"],
            QComboBox[validationState="warning"],
            QDateEdit[validationState="warning"],
            QSpinBox[validationState="warning"],
            QDoubleSpinBox[validationState="warning"],
            QPlainTextEdit[validationState="warning"],
            QTextEdit[validationState="warning"] {{ border-color: {t.warning}; }}

            QLineEdit[validationState="valid"],
            QLineEdit[validationState="success"],
            QComboBox[validationState="valid"],
            QComboBox[validationState="success"],
            QDateEdit[validationState="valid"],
            QDateEdit[validationState="success"],
            QSpinBox[validationState="valid"],
            QSpinBox[validationState="success"],
            QDoubleSpinBox[validationState="valid"],
            QDoubleSpinBox[validationState="success"],
            QPlainTextEdit[validationState="valid"],
            QPlainTextEdit[validationState="success"],
            QTextEdit[validationState="valid"],
            QTextEdit[validationState="success"] {{ border-color: {t.success}; }}

            /* Focus reste perceptible même lorsqu'un état métier est présent. */
            QLineEdit[validationState="error"]:focus,
            QPlainTextEdit[validationState="error"]:focus,
            QTextEdit[validationState="error"]:focus {{ border: 2px solid {t.danger}; }}
            QLineEdit[validationState="warning"]:focus,
            QPlainTextEdit[validationState="warning"]:focus,
            QTextEdit[validationState="warning"]:focus {{ border: 2px solid {t.warning}; }}
            QLineEdit[validationState="valid"]:focus,
            QLineEdit[validationState="success"]:focus,
            QPlainTextEdit[validationState="valid"]:focus,
            QPlainTextEdit[validationState="success"]:focus,
            QTextEdit[validationState="valid"]:focus,
            QTextEdit[validationState="success"]:focus {{ border: 2px solid {t.success}; }}

            QLabel#twValidationMessage[validationState="error"] {{ color: {t.danger}; }}
            QLabel#twValidationMessage[validationState="warning"] {{ color: {t.warning}; }}
            QLabel#twValidationMessage[validationState="valid"],
            QLabel#twValidationMessage[validationState="success"] {{ color: {t.success}; }}

            QFrame#alertRow {{
                background: {t.surface_container_high};
                border-radius: 6px;
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
                selection-color: {t.selection_text};
                border: 0;
            }}
            QTableView::item:hover,
            QTableWidget::item:hover {{
                background: {t.surface_container_high};
            }}
            QTableView::item:selected,
            QTableWidget::item:selected {{
                background: {t.selection};
                color: {t.selection_text};
            }}
            QTableView:focus, QTableWidget:focus {{
                border: 2px solid {t.focus};
            }}
            QTableView:disabled, QTableWidget:disabled {{
                color: {t.disabled};
                background: {t.surface_container_high};
            }}
            QTableView#twDataTable {{
                border: 1px solid {t.outline_variant};
                border-radius: {r.field}px;
            }}
            QHeaderView::section {{
                min-height: {c.table_header}px;
                background: {t.surface_container_high};
                border: 0;
                border-right: 1px solid {t.outline};
                border-bottom: 1px solid {t.outline};
                padding: 6px;
                font-weight: 600;
            }}
            QTabWidget::pane {{
                border: 1px solid {t.outline};
                border-radius: 4px;
                top: -1px;
            }}
            QTabBar::tab {{
                padding: 7px 9px;
            }}
            QTabBar::tab:hover {{
                background: {t.surface_container_high};
            }}
            QTabBar::tab:selected {{
                background: {t.selection};
                color: {t.selection_text};
            }}
            """
        )
