from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from application.services.expense_reimbursement_write import ReimbursementCommand
from application.services.expense_trip_write import TripCommand
from ui.common import ActionSpec, TOKENS, TwActionBar, TwDataTable, TwDialogShell, TwFormSection


def _date_edit() -> QDateEdit:
    control = QDateEdit(QDate.currentDate())
    control.setCalendarPopup(True)
    control.setDisplayFormat("dd/MM/yyyy")
    return control


def _readonly_banner() -> QLabel:
    label = QLabel("Aperçu de disposition · aucune écriture en base")
    label.setProperty("muted", True)
    return label


def _empty_table(headers: tuple[str, ...], parent: QWidget) -> TwDataTable:
    model = QStandardItemModel(0, len(headers), parent)
    model.setHorizontalHeaderLabels(list(headers))
    return TwDataTable(model=model)


class ScenarioPreviewDialog(TwDialogShell):
    """Transposition visuelle de ``DLG_Scenario.Dialog`` sans moteur de reports."""

    DETAIL_LEVELS = ("Aucun", "Jour", "Mois", "Année")
    MINUTE_MODES = ("Normal", "Décimal")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Création d'un scénario",
            parent,
            profile="wide",
            primary_label="Ok",
            cancel_label="Annuler",
        )
        self.resize(1020, 740)
        self.setMinimumSize(760, 560)

        body = QWidget(self)
        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(TOKENS.spacing.md)
        root.addWidget(_readonly_banner())

        top = QHBoxLayout()
        top.setSpacing(TOKENS.spacing.md)

        parameters = TwFormSection("Paramètres du scénario", compact=True)
        form_host = QWidget()
        form = QGridLayout(form_host)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(TOKENS.spacing.sm)
        form.setVerticalSpacing(TOKENS.spacing.sm)

        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(82)
        self.person_choice = QComboBox()
        self.person_choice.setEnabled(False)
        self.start_date = _date_edit()
        self.end_date = _date_edit()
        self.all_categories = QCheckBox("Inclure toutes les catégories utilisées")
        self.all_categories.setChecked(True)

        form.addWidget(QLabel("Nom"), 0, 0)
        form.addWidget(self.name_edit, 0, 1)
        form.addWidget(QLabel("Description"), 1, 0, Qt.AlignmentFlag.AlignTop)
        form.addWidget(self.description_edit, 1, 1)
        form.addWidget(QLabel("Personne"), 2, 0)
        form.addWidget(self.person_choice, 2, 1)
        form.addWidget(QLabel("Période du"), 3, 0)
        period = QHBoxLayout()
        period.setContentsMargins(0, 0, 0, 0)
        period.addWidget(self.start_date)
        period.addWidget(QLabel("au"))
        period.addWidget(self.end_date)
        period.addSpacing(TOKENS.spacing.sm)
        period.addWidget(self.all_categories)
        period.addStretch(1)
        form.addLayout(period, 3, 1)
        form.setColumnStretch(1, 1)
        parameters.add_widget(form_host)
        top.addWidget(parameters, 3)

        legend = TwFormSection("Légende", compact=True)
        legend_note = QLabel("La légende dépend des catégories du scénario.")
        legend_note.setProperty("muted", True)
        legend_note.setWordWrap(True)
        legend.add_widget(legend_note)
        legend.add_widget(QWidget(), 1)
        top.addWidget(legend, 1)
        root.addLayout(top)

        detail = TwFormSection("Détail du scénario", compact=True)
        # La grille wx est dynamique : ses colonnes dépendent des catégories et de
        # la période. Le POC ne fabrique donc aucun faux axe métier.
        self.detail_grid = QTableWidget(0, 0)
        self.detail_grid.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_grid.setAlternatingRowColors(True)
        self.detail_grid.setMinimumHeight(250)
        detail.add_widget(self.detail_grid, 1)

        options = QWidget()
        options_row = QHBoxLayout(options)
        options_row.setContentsMargins(0, 0, 0, 0)
        options_row.setSpacing(TOKENS.spacing.sm)
        options_row.addWidget(QLabel("Détail"))
        self.detail_choice = QComboBox()
        self.detail_choice.addItems(self.DETAIL_LEVELS)
        options_row.addWidget(self.detail_choice)
        options_row.addSpacing(TOKENS.spacing.sm)
        options_row.addWidget(QLabel("Mode minutes"))
        self.minute_mode = QComboBox()
        self.minute_mode.addItems(self.MINUTE_MODES)
        options_row.addWidget(self.minute_mode)
        options_row.addStretch(1)
        self.categories_button = QPushButton("Ajouter ou supprimer des catégories")
        self.categories_button.setEnabled(False)
        options_row.addWidget(self.categories_button)
        detail.add_widget(options)
        root.addWidget(detail, 1)

        self.output_actions = TwActionBar(
            [
                ActionSpec("excel", "Excel", "Excel.png", "Exporter le tableau", enabled=False),
                ActionSpec("print", "Imprimer", "Imprimante.png", "Publier le tableau au format PDF", enabled=False),
            ]
        )
        root.addWidget(self.output_actions)

        self.set_content(body)
        self.help_button.setEnabled(False)
        self.set_primary_enabled(False)


class TripPreviewDialog(TwDialogShell):
    """Dialogue Déplacement Qt raccordable à la frontière métier commune."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        person_id: int | None = None,
        snapshot=None,
        writable: bool = False,
    ) -> None:
        self.person_id = person_id
        self.snapshot = snapshot
        self._writable = bool(writable)
        self._confirm_empty_purpose = False
        self._confirm_zero_distance = False
        self._confirm_zero_tariff = False
        self._loading = True

        title = (
            "Modification d'un déplacement"
            if snapshot is not None
            else "Saisie d'un déplacement"
        )
        super().__init__(
            title,
            parent,
            profile="wide",
            primary_label="Valider",
            cancel_label="Annuler",
        )
        self.resize(820, 690)

        body = QWidget(self)
        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(TOKENS.spacing.md)

        banner = QLabel(
            "Écriture contrôlée · validation métier puis transaction et relecture"
            if writable
            else "Aperçu de disposition · aucune écriture en base"
        )
        banner.setProperty("muted", True)
        root.addWidget(banner)

        general = TwFormSection("Généralités", compact=True)
        general_host = QWidget()
        general_layout = QVBoxLayout(general_host)
        general_layout.setContentsMargins(0, 0, 0, 0)
        general_layout.setSpacing(TOKENS.spacing.sm)
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Date"))
        self.date_edit = _date_edit()
        date_row.addWidget(self.date_edit)
        date_row.addSpacing(TOKENS.spacing.md)
        date_row.addWidget(QLabel("Utilisateur"))
        self.user_choice = QComboBox()
        self.user_choice.setEnabled(False)
        if person_id is not None:
            self.user_choice.addItem(f"ID {person_id}", person_id)
        date_row.addWidget(self.user_choice, 1)
        general_layout.addLayout(date_row)
        general_layout.addWidget(QLabel("Objet"))
        self.object_edit = QTextEdit()
        self.object_edit.setMinimumHeight(72)
        self.object_edit.setMaximumHeight(100)
        general_layout.addWidget(self.object_edit)
        general.add_widget(general_host)
        root.addWidget(general)

        trip = TwFormSection("Trajet", compact=True)
        trip_host = QWidget()
        trip_layout = QVBoxLayout(trip_host)
        trip_layout.setContentsMargins(0, 0, 0, 0)
        trip_layout.setSpacing(TOKENS.spacing.sm)

        self.departure_postcode = QLineEdit()
        self.departure_postcode.setMaximumWidth(100)
        self.departure_postcode.setMaxLength(5)
        self.departure_city = QLineEdit()
        self.arrival_postcode = QLineEdit()
        self.arrival_postcode.setMaximumWidth(100)
        self.arrival_postcode.setMaxLength(5)
        self.arrival_city = QLineEdit()
        self.distance_edit = QLineEdit("0")
        self.distance_edit.setMaximumWidth(110)
        self.round_trip = QCheckBox()

        for label, postcode, city in (
            ("Ville de départ", self.departure_postcode, self.departure_city),
            ("Ville d'arrivée", self.arrival_postcode, self.arrival_city),
        ):
            trip_layout.addWidget(QLabel(label))
            row = QHBoxLayout()
            row.addWidget(postcode)
            row.addWidget(city, 1)
            search = QPushButton("Rechercher")
            search.setEnabled(False)
            row.addWidget(search)
            trip_layout.addLayout(row)

        distance_row = QHBoxLayout()
        distance_row.addWidget(QLabel("Distance"))
        distance_row.addWidget(self.distance_edit)
        self.distance_unit = QLabel("Km (aller simple)")
        distance_row.addWidget(self.distance_unit)
        distance_row.addStretch(1)
        distance_row.addWidget(QLabel("Aller / retour"))
        distance_row.addWidget(self.round_trip)
        trip_layout.addLayout(distance_row)
        trip.add_widget(trip_host)
        root.addWidget(trip)

        reimbursement = TwFormSection("Remboursement", compact=True)
        reimbursement_host = QWidget()
        reimbursement_layout = QVBoxLayout(reimbursement_host)
        reimbursement_layout.setContentsMargins(0, 0, 0, 0)
        reimbursement_layout.setSpacing(TOKENS.spacing.sm)
        tariff_row = QHBoxLayout()
        tariff_row.addWidget(QLabel("Tarif du km"))
        self.tariff_edit = QLineEdit("0.00")
        self.tariff_edit.setMaximumWidth(110)
        tariff_row.addWidget(self.tariff_edit)
        tariff_row.addWidget(QLabel("€"))
        tariff_row.addStretch(1)
        tariff_row.addWidget(QLabel("Montant"))
        self.amount_label = QLabel("0.00 €")
        self.amount_label.setObjectName("twDataLarge")
        tariff_row.addWidget(self.amount_label)
        reimbursement_layout.addLayout(tariff_row)
        linked_row = QHBoxLayout()
        linked_row.addWidget(QLabel("Remboursement associé"))
        self.linked_reimbursement = QLabel("Aucun remboursement.")
        self.linked_reimbursement.setProperty("muted", True)
        linked_row.addWidget(self.linked_reimbursement, 1)
        reimbursement_layout.addLayout(linked_row)
        reimbursement.add_widget(reimbursement_host)
        root.addWidget(reimbursement)
        root.addStretch(1)

        self.set_content(body)
        self.help_button.setEnabled(False)
        self.set_primary_enabled(writable)

        if snapshot is not None:
            self._load_snapshot(snapshot)

        self._loading = False
        self.distance_edit.textChanged.connect(self._refresh_amount)
        self.tariff_edit.textChanged.connect(self._refresh_amount)
        self.round_trip.toggled.connect(self._on_round_trip_toggled)
        self._refresh_amount()

        if writable:
            self.validateRequested.connect(self._validate_and_accept)

    @staticmethod
    def _decimal(text: str) -> Decimal:
        value = text.strip().replace(",", ".")
        if not value:
            raise InvalidOperation
        return Decimal(value)

    def _load_snapshot(self, snapshot) -> None:
        travel_date = snapshot.travel_date
        self.date_edit.setDate(
            QDate(travel_date.year, travel_date.month, travel_date.day)
        )
        self.object_edit.setPlainText(snapshot.purpose)
        self.departure_postcode.setText(snapshot.departure_postcode)
        self.departure_city.setText(snapshot.departure_city)
        self.arrival_postcode.setText(snapshot.arrival_postcode)
        self.arrival_city.setText(snapshot.arrival_city)
        self.distance_edit.setText(str(snapshot.distance))
        self.round_trip.setChecked(bool(snapshot.round_trip))
        self.tariff_edit.setText(str(snapshot.tariff_per_km))
        reimbursement_id = snapshot.reimbursement_id
        if reimbursement_id not in (None, 0):
            self.linked_reimbursement.setText(f"N°{reimbursement_id}")
            self.linked_reimbursement.setProperty("muted", False)

    def _refresh_amount(self) -> None:
        try:
            amount = self._decimal(self.distance_edit.text()) * self._decimal(
                self.tariff_edit.text()
            )
        except (InvalidOperation, ValueError):
            self.amount_label.setText("—")
            return
        self.amount_label.setText(f"{amount:.2f} €")

    def _on_round_trip_toggled(self, checked: bool) -> None:
        self.distance_unit.setText(
            "Km (aller / retour)" if checked else "Km (aller simple)"
        )
        if self._loading:
            return
        try:
            distance = self._decimal(self.distance_edit.text())
        except (InvalidOperation, ValueError):
            return
        distance = distance * 2 if checked else distance / 2
        self.distance_edit.setText(str(distance.normalize()))

    def _warning(self, title: str, text: str) -> None:
        QMessageBox.warning(self, title, text)

    def _validate_and_accept(self) -> None:
        if self.person_id is None:
            self._warning("Utilisateur invalide", "Aucun utilisateur n'est sélectionné.")
            return

        purpose = self.object_edit.toPlainText().strip()
        if not purpose:
            answer = QMessageBox.question(
                self,
                "Objet vide",
                "Aucun objet n'est saisi. Valider quand même ce déplacement ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self._confirm_empty_purpose = True

        for control, label in (
            (self.departure_postcode, "code postal de départ"),
            (self.departure_city, "ville de départ"),
            (self.arrival_postcode, "code postal d'arrivée"),
            (self.arrival_city, "ville d'arrivée"),
        ):
            if not control.text().strip():
                self._warning("Champ obligatoire", f"Le {label} est obligatoire.")
                return

        for control, label in (
            (self.departure_postcode, "départ"),
            (self.arrival_postcode, "arrivée"),
        ):
            postcode = control.text().strip()
            if len(postcode) != 5 or not postcode.isdigit():
                self._warning(
                    "Code postal invalide",
                    f"Le code postal de {label} doit contenir 5 chiffres.",
                )
                return

        try:
            distance = self._decimal(self.distance_edit.text())
        except (InvalidOperation, ValueError):
            self._warning("Distance invalide", "Saisissez une distance valide.")
            return
        if distance < 0:
            self._warning("Distance invalide", "La distance ne peut pas être négative.")
            return
        if distance == 0:
            answer = QMessageBox.question(
                self,
                "Distance nulle",
                "La distance est de 0 km. Valider quand même ce déplacement ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self._confirm_zero_distance = True

        try:
            tariff = self._decimal(self.tariff_edit.text())
        except (InvalidOperation, ValueError):
            self._warning("Tarif invalide", "Saisissez un tarif kilométrique valide.")
            return
        if tariff < 0:
            self._warning("Tarif invalide", "Le tarif ne peut pas être négatif.")
            return
        if tariff == 0:
            answer = QMessageBox.question(
                self,
                "Tarif nul",
                "Le tarif kilométrique est de 0 €. Valider quand même ce déplacement ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self._confirm_zero_tariff = True

        self.accept()

    def command(self) -> TripCommand:
        if not self._writable or self.person_id is None:
            raise RuntimeError("Dialogue déplacement non configuré pour l'écriture.")
        qdate = self.date_edit.date()
        return TripCommand(
            person_id=int(self.person_id),
            travel_date=qdate.toPython(),
            purpose=self.object_edit.toPlainText().strip(),
            departure_postcode=self.departure_postcode.text().strip(),
            departure_city=self.departure_city.text().strip(),
            arrival_postcode=self.arrival_postcode.text().strip(),
            arrival_city=self.arrival_city.text().strip(),
            distance=self._decimal(self.distance_edit.text()),
            round_trip=self.round_trip.isChecked(),
            tariff_per_km=self._decimal(self.tariff_edit.text()),
            trip_id=getattr(self.snapshot, "trip_id", None),
            confirm_empty_purpose=self._confirm_empty_purpose,
            confirm_zero_distance=self._confirm_zero_distance,
            confirm_zero_tariff=self._confirm_zero_tariff,
        )


class ReimbursementPreviewDialog(TwDialogShell):
    """Dialogue remboursement Qt, utilisable en aperçu ou en écriture contrôlée."""

    TRIP_HEADERS = ("N°", "Date", "Objet", "Trajet", "Distance", "Tarif", "Montant")

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        person_id: int | None = None,
        trips=(),
        reimbursement=None,
        writable: bool = False,
    ) -> None:
        self.person_id = person_id
        self.reimbursement = reimbursement
        self._writable = bool(writable)
        self._confirm_zero_amount = False
        title = "Modification d'un remboursement" if reimbursement is not None else "Saisie d'un remboursement"
        super().__init__(
            title,
            parent,
            profile="wide",
            primary_label="Valider",
            cancel_label="Annuler",
        )
        self.resize(860, 620)

        body = QWidget(self)
        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(TOKENS.spacing.md)
        if writable:
            banner = QLabel("Écriture contrôlée · validation métier puis transaction et relecture")
            banner.setProperty("muted", True)
            root.addWidget(banner)
        else:
            root.addWidget(_readonly_banner())

        characteristics = TwFormSection("Caractéristiques", compact=True)
        characteristics_host = QWidget()
        characteristics_layout = QVBoxLayout(characteristics_host)
        characteristics_layout.setContentsMargins(0, 0, 0, 0)
        characteristics_layout.setSpacing(TOKENS.spacing.sm)
        first_row = QHBoxLayout()
        first_row.addWidget(QLabel("Date"))
        self.date_edit = _date_edit()
        first_row.addWidget(self.date_edit)
        first_row.addSpacing(TOKENS.spacing.md)
        first_row.addWidget(QLabel("Montant"))
        self.amount_edit = QLineEdit()
        first_row.addWidget(self.amount_edit, 1)
        first_row.addWidget(QLabel("€"))
        characteristics_layout.addLayout(first_row)
        user_row = QHBoxLayout()
        user_row.addWidget(QLabel("Utilisateur"))
        self.user_choice = QComboBox()
        self.user_choice.setEnabled(False)
        if person_id is not None:
            self.user_choice.addItem(f"ID {person_id}", person_id)
        user_row.addWidget(self.user_choice, 1)
        characteristics_layout.addLayout(user_row)
        characteristics.add_widget(characteristics_host)
        root.addWidget(characteristics)

        attached = TwFormSection("Déplacements rattachés", compact=True)
        self.attachment_status = QLabel(
            "Cochez les déplacements à rattacher au remboursement."
            if writable
            else "Veuillez sélectionner un utilisateur dans la liste proposée."
        )
        self.attachment_status.setProperty("muted", True)
        attached.add_widget(self.attachment_status)
        self.trip_table = _empty_table(self.TRIP_HEADERS, self)
        self.trip_table.setEnabled(writable)
        attached.add_widget(self.trip_table, 1)
        root.addWidget(attached, 1)

        self.set_content(body)
        self.help_button.setEnabled(False)
        self.set_primary_enabled(writable)

        if reimbursement is not None:
            payment_date = getattr(reimbursement, "payment_date_value", None)
            if payment_date is not None:
                self.date_edit.setDate(QDate(payment_date.year, payment_date.month, payment_date.day))
            amount = getattr(reimbursement, "amount_value", None)
            if amount is not None:
                self.amount_edit.setText(f"{amount:.2f}")

        if writable:
            self._populate_trips(tuple(trips))
            self.validateRequested.connect(self._validate_and_accept)

    def _populate_trips(self, trips) -> None:
        model = self.trip_table.model()
        model.setRowCount(0)
        current_id = getattr(self.reimbursement, "id_historique", None)
        checked_ids = set(getattr(self.reimbursement, "attached_trip_ids", ()) or ())
        for trip in trips:
            assigned_id = getattr(trip, "reimbursement_id", None)
            if assigned_id not in (None, current_id):
                continue
            values = (
                trip.number,
                trip.date,
                trip.purpose,
                trip.route,
                trip.distance,
                trip.tariff,
                trip.amount,
            )
            items = [QStandardItem(str(value or "")) for value in values]
            first = items[0]
            first.setCheckable(True)
            first.setEditable(False)
            first.setData(getattr(trip, "id_historique", None), Qt.ItemDataRole.UserRole)
            first.setCheckState(
                Qt.CheckState.Checked
                if getattr(trip, "id_historique", None) in checked_ids
                else Qt.CheckState.Unchecked
            )
            for item in items[1:]:
                item.setEditable(False)
            model.appendRow(items)
        self.attachment_status.setText(
            f"{model.rowCount()} déplacement(s) disponible(s) pour ce remboursement."
        )

    def _amount(self) -> Decimal:
        text = self.amount_edit.text().strip().replace(",", ".")
        if not text:
            raise InvalidOperation
        return Decimal(text)

    def _validate_and_accept(self) -> None:
        try:
            amount = self._amount()
        except (InvalidOperation, ValueError):
            QMessageBox.warning(self, "Montant invalide", "Saisissez un montant valide.")
            return
        if amount < Decimal("0"):
            QMessageBox.warning(self, "Montant invalide", "Le montant ne peut pas être négatif.")
            return
        if amount == Decimal("0"):
            answer = QMessageBox.question(
                self,
                "Remboursement à 0 €",
                "Confirmer explicitement l'enregistrement d'un remboursement à 0 € ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self._confirm_zero_amount = True
        self.accept()

    def _checked_trip_ids(self) -> tuple[int, ...]:
        model = self.trip_table.model()
        result = []
        for row in range(model.rowCount()):
            item = model.item(row, 0)
            if item.checkState() != Qt.CheckState.Checked:
                continue
            trip_id = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(trip_id, int) and not isinstance(trip_id, bool) and trip_id > 0:
                result.append(trip_id)
        return tuple(result)

    def command(self) -> ReimbursementCommand:
        if not self._writable or self.person_id is None:
            raise RuntimeError("Dialogue remboursement non configuré pour l'écriture.")
        checked = self._checked_trip_ids()
        original = set(getattr(self.reimbursement, "attached_trip_ids", ()) or ())
        unchecked = tuple(sorted(original - set(checked)))
        qdate = self.date_edit.date()
        return ReimbursementCommand(
            person_id=int(self.person_id),
            payment_date=qdate.toPython(),
            amount=self._amount(),
            checked_trip_ids=checked,
            unchecked_trip_ids=unchecked,
            reimbursement_id=getattr(self.reimbursement, "id_historique", None),
            confirm_zero_amount=self._confirm_zero_amount,
        )

