from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from application.services.contract_write import (
    FIXED_TERM_CODES,
    ContractCreateCommand,
    ContractEditCommand,
    ContractEditSnapshot,
    ContractLegacyClassificationCommand,
    LegacyContractOptions,
    validate_contract_create,
    validate_contract_edit,
)
from domain.contracts.contract_creation_rules import CEEQualification
from domain.contracts.contract_operation import ContractOperation
from domain.contracts.contract_type import ContractType
from domain.contracts.probation_period import (
    ProbationUnit,
    propose_ccns_probation_period,
)
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



class ContractCreateDialog(QDialog):
    """Création Qt contrôlée : CDI/CDD CCNS et CEE, sans accès direct à la base."""

    def __init__(
        self,
        person_id: int,
        available_types: tuple[str, ...],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.person_id = person_id
        self._accepted_command: ContractCreateCommand | None = None
        self._presenter = CCNSContractCompliancePresenter()

        self.setWindowTitle("Créer un contrat")
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        intro = QLabel(
            "Création contrôlée · CDI/CDD CCNS et CEE. "
            "Les parcours historiques non extraits restent hors de ce lot."
        )
        intro.setWordWrap(True)
        intro.setProperty("muted", True)
        root.addWidget(intro)

        panel = QFrame()
        panel.setObjectName("panel")
        self.form = QFormLayout(panel)
        form = self.form

        self.contract_type = QComboBox()
        for code in available_types:
            self.contract_type.addItem(code, code)
        form.addRow("Type", self.contract_type)

        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Début", self.start_date)

        self.end_date = QDateEdit(QDate.currentDate().addYears(1))
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fin", self.end_date)

        self.group = QComboBox()
        form.addRow("Groupe CCNS", self.group)

        self.cee_qualification = QComboBox()
        self.cee_qualification.addItem("—", None)
        for code, label in _CEE_LABELS.items():
            self.cee_qualification.addItem(label, code)
        form.addRow("Qualification CEE", self.cee_qualification)

        self.weekly_hours = QDoubleSpinBox()
        self.weekly_hours.setRange(0.25, 80.0)
        self.weekly_hours.setDecimals(2)
        self.weekly_hours.setSingleStep(0.25)
        self.weekly_hours.setValue(35.0)
        form.addRow("Durée hebdomadaire", self.weekly_hours)

        self.monthly_salary = QLineEdit()
        self.monthly_salary.setPlaceholderText("ex. 2 000,00")
        form.addRow("Brut mensuel", self.monthly_salary)

        self.annual_salary = QLineEdit()
        self.annual_salary.setPlaceholderText("ex. 38 000,00")
        form.addRow("Brut annuel", self.annual_salary)

        self.trial_row = QWidget()
        trial_layout = QHBoxLayout(self.trial_row)
        trial_layout.setContentsMargins(0, 0, 0, 0)
        self.trial_value = QSpinBox()
        self.trial_value.setRange(0, 365)
        self.trial_unit = QComboBox()
        self.trial_unit.addItem("jour(s)", ProbationUnit.DAY.value)
        self.trial_unit.addItem("mois", ProbationUnit.MONTH.value)
        trial_layout.addWidget(self.trial_value)
        trial_layout.addWidget(self.trial_unit, 1)
        form.addRow("Période d'essai", self.trial_row)

        self.confirm_no_trial = QCheckBox(
            "Je confirme l'absence de période d'essai pour ce contrat"
        )
        form.addRow("", self.confirm_no_trial)

        root.addWidget(panel)

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

        self.contract_type.currentIndexChanged.connect(self._refresh_contract_type)
        self.start_date.dateChanged.connect(self._refresh_groups)
        self.end_date.dateChanged.connect(self._refresh_trial)
        self.group.currentIndexChanged.connect(self._on_group_changed)
        self.trial_value.valueChanged.connect(self._refresh_no_trial_confirmation)

        self._refresh_contract_type()
        self._refresh_groups()

    def _contract_type_code(self) -> str:
        return str(self.contract_type.currentData() or "").strip().upper()

    def _set_form_field_visible(self, field: QWidget, visible: bool) -> None:
        field.setVisible(visible)
        label = self.form.labelForField(field)
        if label is not None:
            label.setVisible(visible)

    def _refresh_contract_type(self, *_args) -> None:
        code = self._contract_type_code()
        is_cee = code == "CEE"
        self.end_date.setEnabled(code in ("CDD", "CEE"))
        self._set_form_field_visible(self.group, not is_cee)
        self._set_form_field_visible(self.weekly_hours, not is_cee)
        self._set_form_field_visible(self.cee_qualification, is_cee)
        self._set_form_field_visible(self.trial_row, not is_cee)

        if is_cee:
            self.trial_value.blockSignals(True)
            self.trial_unit.blockSignals(True)
            self.trial_value.setValue(0)
            day_index = self.trial_unit.findData(ProbationUnit.DAY.value)
            if day_index >= 0:
                self.trial_unit.setCurrentIndex(day_index)
            self.trial_unit.blockSignals(False)
            self.trial_value.blockSignals(False)
            self.confirm_no_trial.setChecked(False)
            self.confirm_no_trial.setVisible(False)
            self._refresh_salary_mode()
            return

        self._refresh_salary_mode()
        self._refresh_trial()
        self._refresh_no_trial_confirmation()

    def _refresh_groups(self, *_args) -> None:
        preserve = self.group.currentData()
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
        self._refresh_trial()

    def _on_group_changed(self, *_args) -> None:
        self._refresh_salary_mode()
        self._refresh_trial()

    def _refresh_salary_mode(self) -> None:
        if self._contract_type_code() == "CEE":
            self._set_form_field_visible(self.monthly_salary, False)
            self._set_form_field_visible(self.annual_salary, False)
            return

        code = self.group.currentData()
        annual = False
        if code:
            try:
                choice = next(
                    (
                        item
                        for item in self._presenter.group_choices(
                            _python_date(self.start_date.date())
                        )
                        if item.code == code
                    ),
                    None,
                )
                annual = bool(
                    choice and choice.periodicity is SalaryMinimumPeriodicity.ANNUAL
                )
            except Exception:
                annual = False
        self._set_form_field_visible(self.monthly_salary, not annual)
        self._set_form_field_visible(self.annual_salary, annual)

    def _refresh_trial(self, *_args) -> None:
        code = self._contract_type_code()
        group = self.group.currentData()
        if code not in ("CDI", "CDD") or not group:
            return
        try:
            proposal = propose_ccns_probation_period(
                contract_type=ContractType(code),
                operation=ContractOperation.NEW,
                start_date=_python_date(self.start_date.date()),
                end_date=(
                    _python_date(self.end_date.date())
                    if code == "CDD"
                    else None
                ),
                ccns_group=group,
            )
        except Exception:
            return
        self.trial_value.blockSignals(True)
        self.trial_unit.blockSignals(True)
        self.trial_value.setValue(proposal.value)
        unit_index = self.trial_unit.findData(proposal.unit.value)
        if unit_index >= 0:
            self.trial_unit.setCurrentIndex(unit_index)
        self.trial_unit.blockSignals(False)
        self.trial_value.blockSignals(False)
        self._refresh_no_trial_confirmation()

    def _refresh_no_trial_confirmation(self, *_args) -> None:
        if self._contract_type_code() == "CEE":
            self.confirm_no_trial.setChecked(False)
            self.confirm_no_trial.setVisible(False)
            return
        zero = self.trial_value.value() == 0
        self.confirm_no_trial.setVisible(zero)
        if not zero:
            self.confirm_no_trial.setChecked(False)

    def _build_command(self) -> ContractCreateCommand:
        code = self._contract_type_code()
        is_cee = code == "CEE"

        if is_cee:
            group = None
            cee_qualification = self.cee_qualification.currentData()
            weekly_hours = None
            monthly = None
            annual = None
            trial_value = 0
            trial_unit = ProbationUnit.DAY.value
            confirm_no_trial = False
        else:
            group = self.group.currentData()
            cee_qualification = None
            weekly_hours = Decimal(str(self.weekly_hours.value())).quantize(
                Decimal("0.01")
            )
            monthly = parse_decimal_text(self.monthly_salary.text())
            annual = parse_decimal_text(self.annual_salary.text())

            try:
                choice = next(
                    (
                        item
                        for item in self._presenter.group_choices(
                            _python_date(self.start_date.date())
                        )
                        if item.code == group
                    ),
                    None,
                )
            except Exception:
                choice = None
            if choice and choice.periodicity is SalaryMinimumPeriodicity.ANNUAL:
                monthly = None
            else:
                annual = None

            trial_value = self.trial_value.value()
            trial_unit = str(self.trial_unit.currentData())
            confirm_no_trial = self.confirm_no_trial.isChecked()

        return ContractCreateCommand(
            person_id=self.person_id,
            contract_type_code=code,
            convention_code="CCNS",
            ccns_group=group,
            cee_qualification=cee_qualification,
            weekly_hours=weekly_hours,
            gross_monthly_salary=monthly,
            gross_annual_salary=annual,
            start_date=_python_date(self.start_date.date()),
            end_date=(
                _python_date(self.end_date.date())
                if code in ("CDD", "CEE")
                else None
            ),
            trial_period_value=trial_value,
            trial_period_unit=trial_unit,
            confirm_no_trial=confirm_no_trial,
        )

    def _on_accept(self) -> None:
        command = self._build_command()
        errors = validate_contract_create(command)
        if errors:
            self.error_label.setText("\n".join(errors))
            return
        self.error_label.clear()
        self._accepted_command = command
        self.accept()

    def command(self) -> ContractCreateCommand:
        return self._accepted_command or self._build_command()



class ContractOperationDialog(ContractCreateDialog):
    """Prépare un renouvellement CDD ou un passage CDD→CDI.

    Ce dialogue n'est pas encore exposé par la barre d'outils du pilote Qt.
    Il construit uniquement une commande conforme au service Contrats avancé.
    """

    def __init__(
        self,
        person_id: int,
        previous: ContractEditSnapshot,
        operation: ContractOperation,
        parent: QWidget | None = None,
    ):
        if operation not in (
            ContractOperation.CDD_RENEWAL,
            ContractOperation.CDD_TO_CDI,
        ):
            raise ValueError("Opération de contrat avancée non prise en charge.")
        if previous.contract_type_code.strip().upper() != ContractType.CDD.value:
            raise ValueError("Le contrat précédent doit être un CDD.")
        if previous.end_date is None:
            raise ValueError("Le CDD précédent doit avoir une date de fin.")

        self.previous = previous
        self.operation = operation
        target_type = (
            ContractType.CDD.value
            if operation is ContractOperation.CDD_RENEWAL
            else ContractType.CDI.value
        )
        super().__init__(person_id, (target_type,), parent)

        self.setWindowTitle(
            "Renouveler le CDD"
            if operation is ContractOperation.CDD_RENEWAL
            else "Poursuivre le CDD en CDI"
        )
        self.contract_type.setEnabled(False)

        expected_start = previous.end_date + timedelta(days=1)
        self.start_date.setDate(_qdate(expected_start))
        self.start_date.setEnabled(False)

        previous_group = (previous.ccns_group or "").strip().upper()
        if previous_group:
            index = self.group.findData(previous_group)
            if index >= 0:
                self.group.setCurrentIndex(index)

        self._refresh_contract_type()
        self._refresh_trial()

    def _refresh_trial(self, *_args) -> None:
        code = self._contract_type_code()
        group = self.group.currentData()
        if code not in ("CDI", "CDD") or not group:
            return
        try:
            proposal = propose_ccns_probation_period(
                contract_type=ContractType(code),
                operation=self.operation,
                start_date=_python_date(self.start_date.date()),
                end_date=(
                    _python_date(self.end_date.date())
                    if code == "CDD"
                    else None
                ),
                ccns_group=group,
                previous_contract_start=self.previous.start_date,
                previous_contract_end=self.previous.end_date,
            )
        except Exception:
            return

        self.trial_value.blockSignals(True)
        self.trial_unit.blockSignals(True)
        self.trial_value.setValue(proposal.value)
        unit_index = self.trial_unit.findData(proposal.unit.value)
        if unit_index >= 0:
            self.trial_unit.setCurrentIndex(unit_index)
        self.trial_unit.blockSignals(False)
        self.trial_value.blockSignals(False)
        self._refresh_no_trial_confirmation()

    def _build_command(self) -> ContractCreateCommand:
        base = super()._build_command()
        return replace(
            base,
            operation_type=self.operation.value,
            previous_contract_id=self.previous.contract_id,
        )


class LegacyClassificationDialog(QDialog):
    """Prépare la classification historique sans confondre ID et valeur monétaire."""

    def __init__(
        self,
        options: LegacyContractOptions,
        snapshot: ContractEditSnapshot,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.options = options
        self.snapshot = snapshot
        self._accepted_command: ContractLegacyClassificationCommand | None = None

        self.setWindowTitle("Classification historique")
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        intro = QLabel(
            "Parcours historique : la classification et la valeur de point sont "
            "conservées par leurs identifiants d'origine."
        )
        intro.setWordWrap(True)
        intro.setProperty("muted", True)
        root.addWidget(intro)

        panel = QFrame()
        panel.setObjectName("panel")
        form = QFormLayout(panel)

        self.classification = QComboBox()
        for item in options.classifications:
            self.classification.addItem(item.label or f"Classification {item.classification_id}", item.classification_id)
        current_class = self.classification.findData(snapshot.legacy_classification_id)
        if current_class >= 0:
            self.classification.setCurrentIndex(current_class)
        form.addRow("Classification", self.classification)

        self.point = QComboBox()
        for item in options.point_values:
            label = (
                f"{str(item.value).replace('.', ',')} € · "
                f"à partir du {item.effective_date.strftime('%d/%m/%Y')}"
            )
            self.point.addItem(label, item.point_id)
        applicable = self.point.findData(options.applicable_point_id)
        if applicable >= 0:
            self.point.setCurrentIndex(applicable)
        self.point.setEnabled(False)
        form.addRow("Valeur de point applicable", self.point)

        root.addWidget(panel)

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

    def _build_command(self) -> ContractLegacyClassificationCommand | None:
        classification_id = self.classification.currentData()
        point_id = self.point.currentData()
        if classification_id is None or point_id is None:
            return None
        return ContractLegacyClassificationCommand(
            contract_id=self.snapshot.contract_id,
            classification_id=int(classification_id),
            point_id=int(point_id),
        )

    def _on_accept(self) -> None:
        command = self._build_command()
        if command is None:
            self.error_label.setText(
                "Classification historique ou valeur de point indisponible."
            )
            return
        self.error_label.clear()
        self._accepted_command = command
        self.accept()

    def command(self) -> ContractLegacyClassificationCommand:
        command = self._accepted_command or self._build_command()
        if command is None:
            raise ValueError("Commande de classification historique incomplète.")
        return command


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
                    label.widget().setVisible(not field.widget().isHidden())

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
