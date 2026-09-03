from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from legacy_contract_wizard import LegacyContractWizardDialog


PENDING = "pending"
COMPLIANT = "compliant"
NON_COMPLIANT = "non_compliant"


def decimal_from_qt_number(value: object) -> Decimal:
    """Convertit une valeur numérique issue de Qt sans propager de float au domaine."""
    return Decimal(str(value))


def parse_decimal_text(text: str) -> Decimal | None:
    """Normalise une saisie monétaire française ; une saisie incomplète reste neutre."""
    normalized = text.strip().replace("\u202f", "").replace(" ", "").replace(",", ".")
    if not normalized:
        return None
    try:
        value = Decimal(normalized)
    except InvalidOperation:
        return None
    if not value.is_finite() or value < Decimal("0"):
        return None
    return value


class ContractComplianceDialog(QDialog):
    """Formulaire Qt de raccordement au moteur CCNS, sans persistance.

    Le POC reste strictement isolé : le dialogue permet de saisir et contrôler les
    données mais n'écrit rien en base. La conformité est entièrement calculée par
    CCNSContractCompliancePresenter.
    """

    def __init__(self, parent: QWidget | None = None, *, reference_date: date | None = None):
        super().__init__(parent)
        self._reference_date = reference_date or date.today()
        self._presenter = CCNSContractCompliancePresenter()

        self.setWindowTitle("Contrôle contrat CCNS — POC")
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        intro_row = QHBoxLayout()
        intro = QLabel("Simulation de saisie : aucune donnée n'est enregistrée.")
        intro.setProperty("muted", True)
        intro_row.addWidget(intro, 1)
        legacy_button = QPushButton("Assistant contrat historique…")
        legacy_button.setToolTip("Ouvrir la transposition Qt des six étapes de création de contrat")
        legacy_button.clicked.connect(self._open_legacy_wizard)
        intro_row.addWidget(legacy_button)
        root.addLayout(intro_row)

        panel = QFrame()
        panel.setObjectName("panel")
        grid = QGridLayout(panel)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        self.group = QComboBox()
        for choice in self._presenter.group_choices(self._reference_date):
            self.group.addItem(choice.label, choice.code)

        self.weekly_hours = QDoubleSpinBox()
        self.weekly_hours.setDecimals(2)
        self.weekly_hours.setSingleStep(0.25)
        self.weekly_hours.setRange(0.25, 48.00)
        self.weekly_hours.setValue(35.00)
        self.weekly_hours.setSuffix(" h")
        self.weekly_hours.setMinimumWidth(100)
        self.weekly_hours.setMaximumWidth(120)

        self.monthly_salary = QLineEdit()
        self.monthly_salary.setPlaceholderText("ex. 1 850,00")
        self.monthly_salary.setMinimumWidth(100)
        self.monthly_salary.setMaximumWidth(120)
        self.monthly_salary.setAlignment(Qt.AlignmentFlag.AlignRight)

        grid.addWidget(QLabel("Groupe CCNS"), 0, 0)
        grid.addWidget(self.group, 0, 1, 1, 3)
        grid.addWidget(QLabel("Durée hebdomadaire"), 1, 0)
        grid.addWidget(self.weekly_hours, 1, 1)
        grid.addWidget(QLabel("Salaire brut mensuel"), 1, 2)
        grid.addWidget(self.monthly_salary, 1, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        root.addWidget(panel)

        self.status = QLabel()
        self.status.setObjectName("complianceStatus")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.group.currentIndexChanged.connect(self._refresh_compliance)
        self.weekly_hours.valueChanged.connect(self._refresh_compliance)
        self.monthly_salary.textChanged.connect(self._refresh_compliance)
        self._set_pending()

    def _open_legacy_wizard(self) -> None:
        dialog = LegacyContractWizardDialog(self)
        dialog.exec()

    def _set_status(self, state: str, text: str) -> None:
        self.status.setProperty("complianceState", state)
        self.status.setText(text)
        style = self.status.style()
        style.unpolish(self.status)
        style.polish(self.status)
        self.status.update()

    def _set_pending(self, text: str = "Contrôle en attente — renseignez un salaire brut mensuel valide.") -> None:
        self._set_status(PENDING, text)

    def _refresh_compliance(self, *_args) -> None:
        remuneration = parse_decimal_text(self.monthly_salary.text())
        group_code = self.group.currentData()
        if remuneration is None or not group_code:
            self._set_pending()
            return

        weekly_hours = decimal_from_qt_number(self.weekly_hours.value())
        try:
            preview = self._presenter.evaluate_monthly(
                group_code=str(group_code),
                reference_date=self._reference_date,
                weekly_hours=weekly_hours,
                remuneration_amount=remuneration,
            )
        except ValueError as exc:
            if "minimum annuel" not in str(exc):
                raise
            self._set_pending("Contrôle mensuel indisponible — ce groupe CCNS est défini par un minimum annuel.")
            return

        state = COMPLIANT if preview.compliant else NON_COMPLIANT
        verdict = "Conforme" if preview.compliant else "Non conforme"
        self._set_status(
            state,
            (
                f"{verdict} — minimum retenu {preview.required_minimum_amount:.2f} € "
                f"({preview.source}) · écart {preview.difference_amount:+.2f} €"
            ),
        )
