from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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
    """Transposition de ``DLG_Saisie_deplacement.SaisieDeplacement`` sans persistance."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Saisie d'un déplacement",
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
        root.addWidget(_readonly_banner())

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
        self.departure_city = QLineEdit()
        self.arrival_postcode = QLineEdit()
        self.arrival_postcode.setMaximumWidth(100)
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
        distance_row.addWidget(QLabel("Km (aller simple)"))
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
        self.set_primary_enabled(False)


class ReimbursementPreviewDialog(TwDialogShell):
    """Transposition de ``DLG_Saisie_remboursement`` sans rattachement ni écriture."""

    TRIP_HEADERS = ("N°", "Date", "Objet", "Trajet", "Distance", "Tarif", "Montant")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Saisie d'un remboursement",
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
        user_row.addWidget(self.user_choice, 1)
        characteristics_layout.addLayout(user_row)
        characteristics.add_widget(characteristics_host)
        root.addWidget(characteristics)

        attached = TwFormSection("Déplacements rattachés", compact=True)
        self.attachment_status = QLabel("Veuillez sélectionner un utilisateur dans la liste proposée.")
        self.attachment_status.setProperty("muted", True)
        attached.add_widget(self.attachment_status)
        self.trip_table = _empty_table(self.TRIP_HEADERS, self)
        self.trip_table.setEnabled(False)
        attached.add_widget(self.trip_table, 1)
        root.addWidget(attached, 1)

        self.set_content(body)
        self.help_button.setEnabled(False)
        self.set_primary_enabled(False)
