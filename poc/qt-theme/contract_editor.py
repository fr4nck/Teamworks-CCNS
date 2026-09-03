from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter


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
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        intro = QLabel("Simulation de saisie : aucune donnée n'est enregistrée.")
        intro.setProperty("muted", True)
        root.addWidget(intro)

        panel = QFrame()
        panel.setObjectName("panel")
        form = QFormLayout(panel)
        form.setContentsMargins(12, 12, 12, 12)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

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
        self.monthly_salary.setMaximumWidth(120)
        self.monthly_salary.setAlignment(Qt.AlignmentFlag.AlignRight)

        form.addRow("Groupe CCNS", self.group)
        form.addRow("Durée hebdomadaire", self.weekly_hours)
        form.addRow("Salaire brut mensuel", self.monthly_salary)
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

    def _set_status(self, state: str, text: str) -> None:
        self.status.setProperty("complianceState", state)
        self.status.setText(text)
        style = self.status.style()
        style.unpolish(self.status)
        style.polish(self.status)
        self.status.update()

    def _set_pending(self) -> None:
        self._set_status(PENDING, "Contrôle en attente — renseignez un salaire brut mensuel valide.")

    def _refresh_compliance(self, *_args) -> None:
        remuneration = parse_decimal_text(self.monthly_salary.text())
        group_code = self.group.currentData()
        if remuneration is None or not group_code:
            self._set_pending()
            return

        weekly_hours = decimal_from_qt_number(self.weekly_hours.value())
        preview = self._presenter.evaluate_monthly(
            group_code=str(group_code),
            reference_date=self._reference_date,
            weekly_hours=weekly_hours,
            remuneration_amount=remuneration,
        )
        state = COMPLIANT if preview.compliant else NON_COMPLIANT
        verdict = "Conforme" if preview.compliant else "Non conforme"
        self._set_status(
            state,
            (
                f"{verdict} — minimum retenu {preview.required_minimum_amount:.2f} € "
                f"({preview.source}) · écart {preview.difference_amount:+.2f} €"
            ),
        )
