from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
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
from application.services.contract_write import (
    FIXED_TERM_CODES,
    ContractEditCommand,
    ContractEditSnapshot,
    validate_contract_edit,
)
from domain.contracts.contract_creation_rules import CEEQualification
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity
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




_CEE_LABELS = {
    CEEQualification.BAFA_HOLDER.value: "BAFA titulaire",
    CEEQualification.BAFA_TRAINEE.value: "BAFA stagiaire",
    CEEQualification.UNQUALIFIED.value: "Non diplômé",
    CEEQualification.EQUIVALENT.value: "Qualification équivalente",
    CEEQualification.BAFD_HOLDER.value: "BAFD titulaire",
    CEEQualification.BAFD_TRAINEE.value: "BAFD stagiaire",
}


def _qdate(value: date | None) -> QDate:
    value = value or date.today()
    return QDate(value.year, value.month, value.day)


def _python_date(value: QDate) -> date:
    return date(value.year(), value.month(), value.day())


class ContractEditDialog(QDialog):
    """Éditeur du noyau Contrat ; toute validation métier reste hors Qt."""

    def __init__(self, snapshot: ContractEditSnapshot, parent: QWidget | None = None):
        super().__init__(parent)
        self.snapshot = snapshot
        self._accepted_command: ContractEditCommand | None = None
        self._presenter = CCNSContractCompliancePresenter()

        self.setWindowTitle(f"Modifier le contrat n°{snapshot.contract_id}")
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        identity = QLabel(
            f"{snapshot.contract_type_label or snapshot.contract_type_code or 'Contrat'} · "
            f"convention {snapshot.convention_code or 'historique'}"
        )
        identity.setProperty("muted", True)
        root.addWidget(identity)

        dates_panel = QFrame()
        dates_panel.setObjectName("panel")
        dates_form = QFormLayout(dates_panel)
        self.start_date = QDateEdit(_qdate(snapshot.start_date))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        dates_form.addRow("Début", self.start_date)

        self.open_ended = QCheckBox("Contrat sans date de fin")
        self.open_ended.setChecked(snapshot.end_date is None)
        if snapshot.contract_type_code.strip().upper() in FIXED_TERM_CODES:
            self.open_ended.setChecked(False)
            self.open_ended.setEnabled(False)
        dates_form.addRow("", self.open_ended)

        self.end_date = QDateEdit(_qdate(snapshot.end_date or snapshot.start_date))
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM/yyyy")
        self.end_date.setEnabled(not self.open_ended.isChecked())
        self.open_ended.toggled.connect(lambda checked: self.end_date.setEnabled(not checked))
        dates_form.addRow("Fin", self.end_date)

        self.has_break = QCheckBox("Rupture anticipée")
        self.has_break.setChecked(snapshot.break_date is not None)
        dates_form.addRow("", self.has_break)
        self.break_date = QDateEdit(_qdate(snapshot.break_date or snapshot.start_date))
        self.break_date.setCalendarPopup(True)
        self.break_date.setDisplayFormat("dd/MM/yyyy")
        self.break_date.setEnabled(self.has_break.isChecked())
        self.has_break.toggled.connect(self.break_date.setEnabled)
        dates_form.addRow("Date de rupture", self.break_date)
        root.addWidget(dates_panel)

        self.regime_panel = QFrame()
        self.regime_panel.setObjectName("panel")
        self.regime_form = QFormLayout(self.regime_panel)

        self.group = QComboBox()
        self.weekly_hours = QDoubleSpinBox()
        self.weekly_hours.setRange(0.25, 80.0)
        self.weekly_hours.setDecimals(2)
        self.weekly_hours.setSingleStep(0.25)
        self.weekly_hours.setValue(float(snapshot.weekly_hours or Decimal("35")))

        self.monthly_salary = QLineEdit()
        if snapshot.gross_monthly_salary is not None:
            self.monthly_salary.setText(str(snapshot.gross_monthly_salary).replace(".", ","))
        self.annual_salary = QLineEdit()
        if snapshot.gross_annual_salary is not None:
            self.annual_salary.setText(str(snapshot.gross_annual_salary).replace(".", ","))

        self.cee_qualification = QComboBox()
        self.cee_qualification.addItem("—", None)
        for code, label in _CEE_LABELS.items():
            self.cee_qualification.addItem(label, code)
        current_cee = self.cee_qualification.findData(snapshot.cee_qualification)
        if current_cee >= 0:
            self.cee_qualification.setCurrentIndex(current_cee)

        self.regime_form.addRow("Groupe CCNS", self.group)
        self.regime_form.addRow("Durée hebdomadaire", self.weekly_hours)
        self.regime_form.addRow("Brut mensuel", self.monthly_salary)
        self.regime_form.addRow("Brut annuel", self.annual_salary)
        self.regime_form.addRow("Qualification CEE", self.cee_qualification)
        root.addWidget(self.regime_panel)

        self.legacy_note = QLabel(
            "Les colonnes métier modernes ne sont pas disponibles sur cette base : "
            "la modification est limitée aux dates, sans migration automatique du schéma."
        )
        self.legacy_note.setWordWrap(True)
        self.legacy_note.setProperty("muted", True)
        root.addWidget(self.legacy_note)

        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setProperty("error", True)
        root.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.start_date.dateChanged.connect(self._refresh_groups)
        self.group.currentIndexChanged.connect(self._refresh_salary_mode)
        self._configure_regime()
        self._refresh_groups()

    def _configure_regime(self) -> None:
        modern = self.snapshot.modern_fields_supported
        self.regime_panel.setVisible(modern)
        self.legacy_note.setVisible(not modern)
        if not modern:
            return
        is_cee = self.snapshot.contract_type_code.strip().upper() == "CEE"
        is_ccns = (
            (self.snapshot.convention_code or "").strip().upper() == "CCNS"
            and not is_cee
        )
        self.group.setVisible(is_ccns)
        self.weekly_hours.setVisible(is_ccns)
        self.monthly_salary.setVisible(is_ccns)
        self.annual_salary.setVisible(is_ccns)
        self.cee_qualification.setVisible(is_cee)
        for row in range(self.regime_form.rowCount()):
            label = self.regime_form.itemAt(row, QFormLayout.ItemRole.LabelRole)
            field = self.regime_form.itemAt(row, QFormLayout.ItemRole.FieldRole)
            if label is not None and field is not None:
                label.widget().setVisible(not field.widget().isHidden())

    def _refresh_groups(self, *_args) -> None:
        if not self.snapshot.modern_fields_supported:
            return
        if (self.snapshot.convention_code or "").strip().upper() != "CCNS":
            return
        if self.snapshot.contract_type_code.strip().upper() == "CEE":
            return
        preserve = self.group.currentData() or self.snapshot.ccns_group
        self.group.blockSignals(True)
        self.group.clear()
        try:
            choices = self._presenter.group_choices(_python_date(self.start_date.date()))
        except Exception:
            choices = ()
        for choice in choices:
            self.group.addItem(choice.label, choice.code)
        index = self.group.findData(preserve)
        if index >= 0:
            self.group.setCurrentIndex(index)
        self.group.blockSignals(False)
        self._refresh_salary_mode()

    def _refresh_salary_mode(self, *_args) -> None:
        code = self.group.currentData()
        annual = False
        if code:
            try:
                choices = self._presenter.group_choices(_python_date(self.start_date.date()))
                choice = next((item for item in choices if item.code == code), None)
                annual = bool(
                    choice and choice.periodicity is SalaryMinimumPeriodicity.ANNUAL
                )
            except Exception:
                annual = False
        self.monthly_salary.setVisible(not annual)
        self.annual_salary.setVisible(annual)
        if not self.regime_panel.isHidden():
            for row in range(self.regime_form.rowCount()):
                label = self.regime_form.itemAt(row, QFormLayout.ItemRole.LabelRole)
                field = self.regime_form.itemAt(row, QFormLayout.ItemRole.FieldRole)
                if label is not None and field is not None:
                    label.widget().setVisible(field.widget().isVisible())

    def _build_command(self) -> ContractEditCommand:
        end_date = None if self.open_ended.isChecked() else _python_date(self.end_date.date())
        break_date = _python_date(self.break_date.date()) if self.has_break.isChecked() else None

        convention = self.snapshot.convention_code
        group = self.snapshot.ccns_group
        cee = self.snapshot.cee_qualification
        weekly = self.snapshot.weekly_hours
        monthly = self.snapshot.gross_monthly_salary
        annual = self.snapshot.gross_annual_salary

        if self.snapshot.modern_fields_supported:
            is_cee = self.snapshot.contract_type_code.strip().upper() == "CEE"
            is_ccns = (convention or "").strip().upper() == "CCNS" and not is_cee
            if is_cee:
                cee = self.cee_qualification.currentData()
                group = None
                weekly = None
                monthly = None
                annual = None
            elif is_ccns:
                group = self.group.currentData()
                cee = None
                weekly = Decimal(str(self.weekly_hours.value())).quantize(Decimal("0.01"))
                monthly = parse_decimal_text(self.monthly_salary.text())
                annual = parse_decimal_text(self.annual_salary.text())
                try:
                    choices = self._presenter.group_choices(_python_date(self.start_date.date()))
                    choice = next((item for item in choices if item.code == group), None)
                except Exception:
                    choice = None
                if choice and choice.periodicity is SalaryMinimumPeriodicity.ANNUAL:
                    monthly = None
                else:
                    annual = None

        return ContractEditCommand(
            contract_id=self.snapshot.contract_id,
            contract_type_code=self.snapshot.contract_type_code,
            convention_code=convention,
            ccns_group=group,
            cee_qualification=cee,
            weekly_hours=weekly,
            gross_monthly_salary=monthly,
            gross_annual_salary=annual,
            start_date=_python_date(self.start_date.date()),
            end_date=end_date,
            break_date=break_date,
            modern_fields_supported=self.snapshot.modern_fields_supported,
        )

    def _on_accept(self) -> None:
        command = self._build_command()
        errors = validate_contract_edit(command, original=self.snapshot)
        if errors:
            self.error_label.setText("\n".join(errors))
            return
        self.error_label.clear()
        self._accepted_command = command
        self.accept()

    def command(self) -> ContractEditCommand:
        return self._accepted_command or self._build_command()

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
