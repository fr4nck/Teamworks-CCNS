from __future__ import annotations

from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)


class LegacyPreviewDialog(QDialog):
    """Aperçu Qt d'une fiche wx historique, sans persistance."""

    def __init__(self, title: str, parent=None, *, size=(760, 620)):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(*size)
        self.setMinimumSize(min(size[0], 640), min(size[1], 480))
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(12, 12, 12, 12)
        self.root.setSpacing(10)

        banner = QLabel("Aperçu de disposition · aucune écriture en base")
        banner.setProperty("muted", True)
        self.root.addWidget(banner)

    def section(self, title: str, layout=None) -> tuple[QGroupBox, object]:
        group = QGroupBox(title)
        if layout is None:
            layout = QVBoxLayout(group)
        else:
            group.setLayout(layout)
        self.root.addWidget(group)
        return group, layout

    def actions(self, *, extra: tuple[str, ...] = ()) -> None:
        row = QHBoxLayout()
        aide = QPushButton("Aide")
        aide.setEnabled(False)
        row.addWidget(aide)
        for label in extra:
            button = QPushButton(label)
            button.setEnabled(False)
            row.addWidget(button)
        row.addStretch(1)
        validate = QPushButton("Valider")
        validate.setEnabled(False)
        row.addWidget(validate)
        close = QPushButton("Fermer")
        close.clicked.connect(self.reject)
        row.addWidget(close)
        self.root.addLayout(row)

    @staticmethod
    def date_edit() -> QDateEdit:
        edit = QDateEdit(QDate.currentDate())
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd/MM/yyyy")
        return edit

    @staticmethod
    def time_edit() -> QTimeEdit:
        edit = QTimeEdit(QTime.currentTime())
        edit.setDisplayFormat("HH:mm")
        return edit

    @staticmethod
    def readonly_table(headers: list[str], rows: int = 0) -> QTableWidget:
        table = QTableWidget(rows, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return table


class PiecePreviewDialog(LegacyPreviewDialog):
    def __init__(self, parent=None):
        super().__init__("Saisie d'une pièce", parent, size=(860, 620))

        body = QHBoxLayout()
        left = QVBoxLayout()
        type_group = QGroupBox("1. Sélectionnez un type de pièce")
        type_layout = QVBoxLayout(type_group)
        required = QRadioButton("Dans la liste de pièces que la personne doit fournir")
        required.setChecked(True)
        type_layout.addWidget(required)
        required_list = QListWidget()
        required_list.addItems(["Diplôme / qualification", "Pièce d'identité", "Justificatif"])
        type_layout.addWidget(required_list, 1)
        other = QRadioButton("Dans la liste des autres types de pièces")
        type_layout.addWidget(other)
        other_combo = QComboBox()
        other_combo.addItems(["Autre type de pièce"])
        other_combo.setEnabled(False)
        type_layout.addWidget(other_combo)
        left.addWidget(type_group, 1)

        dates = QHBoxLayout()
        start_group = QGroupBox("2. Saisissez la date de début")
        start_form = QFormLayout(start_group)
        start_form.addRow("Date", self.date_edit())
        dates.addWidget(start_group, 1)
        end_group = QGroupBox("3. Saisissez la date de fin")
        end_layout = QVBoxLayout(end_group)
        limited = QRadioButton("Date")
        limited.setChecked(True)
        limited_row = QHBoxLayout()
        limited_row.addWidget(limited)
        limited_row.addWidget(self.date_edit(), 1)
        end_layout.addLayout(limited_row)
        end_layout.addWidget(QRadioButton("Validité illimitée"))
        dates.addWidget(end_group, 1)
        left.addLayout(dates)
        body.addLayout(left, 3)

        docs = QGroupBox("Documents associés")
        docs_layout = QHBoxLayout(docs)
        thumbnails = QListWidget()
        thumbnails.addItem("Aucun document associé")
        docs_layout.addWidget(thumbnails, 1)
        tools = QVBoxLayout()
        for label in ("+", "−", "Voir", "Zoom +", "Zoom −"):
            button = QPushButton(label)
            button.setEnabled(False)
            tools.addWidget(button)
        tools.addStretch(1)
        docs_layout.addLayout(tools)
        body.addWidget(docs, 2)
        self.root.addLayout(body, 1)
        self.actions()


class PresencePreviewDialog(LegacyPreviewDialog):
    def __init__(self, parent=None):
        super().__init__("Saisie d'une présence", parent, size=(820, 620))

        group, layout = self.section("Dates et personnes")
        summary = QLabel("1 présence sera créée")
        summary.setProperty("muted", True)
        layout.addWidget(summary)
        table = self.readonly_table(["Personne", "Date", "Créer"], 1)
        table.setItem(0, 0, QTableWidgetItem("Personne sélectionnée"))
        table.setItem(0, 1, QTableWidgetItem(QDate.currentDate().toString("dd/MM/yyyy")))
        table.setItem(0, 2, QTableWidgetItem("Oui"))
        layout.addWidget(table, 1)

        middle = QHBoxLayout()
        details = QGroupBox("Horaires et légende")
        details_layout = QVBoxLayout(details)
        hours = QHBoxLayout()
        hours.addWidget(QLabel("Début"))
        hours.addWidget(self.time_edit())
        hours.addSpacing(12)
        hours.addWidget(QLabel("Fin"))
        hours.addWidget(self.time_edit())
        hours.addStretch(1)
        details_layout.addLayout(hours)
        details_layout.addWidget(QLabel("Légende"))
        legend = QTextEdit()
        legend.setPlaceholderText("Légende optionnelle")
        details_layout.addWidget(legend, 1)
        middle.addWidget(details, 3)

        category = QGroupBox("Catégorie")
        category_layout = QVBoxLayout(category)
        categories = QListWidget()
        categories.addItems(["Catégorie de présence", "Sous-catégorie"])
        category_layout.addWidget(categories)
        middle.addWidget(category, 2)
        self.root.addLayout(middle, 2)
        self.actions()


class TripPreviewDialog(LegacyPreviewDialog):
    def __init__(self, parent=None):
        super().__init__("Saisie d'un déplacement", parent, size=(820, 690))

        general = QGroupBox("Généralités")
        general_layout = QVBoxLayout(general)
        row = QHBoxLayout()
        row.addWidget(QLabel("Date"))
        row.addWidget(self.date_edit())
        row.addSpacing(18)
        row.addWidget(QLabel("Utilisateur"))
        user = QComboBox()
        user.addItem("Personne sélectionnée")
        row.addWidget(user, 1)
        general_layout.addLayout(row)
        general_layout.addWidget(QLabel("Objet"))
        obj = QTextEdit()
        obj.setPlaceholderText("Réunion, formation, rendez-vous…")
        obj.setMaximumHeight(90)
        general_layout.addWidget(obj)
        self.root.addWidget(general)

        trajet = QGroupBox("Trajet")
        grid = QGridLayout(trajet)
        grid.addWidget(QLabel("Ville de départ"), 0, 0)
        grid.addWidget(QLineEdit(), 0, 1)
        grid.addWidget(QLineEdit(), 0, 2)
        grid.addWidget(QPushButton("Rechercher"), 0, 3)
        grid.addWidget(QLabel("Ville d'arrivée"), 1, 0)
        grid.addWidget(QLineEdit(), 1, 1)
        grid.addWidget(QLineEdit(), 1, 2)
        grid.addWidget(QPushButton("Rechercher"), 1, 3)
        grid.addWidget(QLabel("Distance"), 2, 0)
        distance = QLineEdit("0")
        grid.addWidget(distance, 2, 1)
        grid.addWidget(QLabel("Km (aller simple)"), 2, 2)
        grid.addWidget(QLabel("Aller / retour"), 3, 0)
        grid.addWidget(QCheckBox(), 3, 1)
        grid.setColumnStretch(2, 1)
        self.root.addWidget(trajet)

        refund = QGroupBox("Remboursement")
        refund_grid = QGridLayout(refund)
        refund_grid.addWidget(QLabel("Tarif du km"), 0, 0)
        refund_grid.addWidget(QLineEdit("0.00"), 0, 1)
        refund_grid.addWidget(QLabel("€"), 0, 2)
        refund_grid.addWidget(QLabel("Montant"), 1, 0)
        amount = QLabel("0.00 €")
        font = amount.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        amount.setFont(font)
        refund_grid.addWidget(amount, 1, 1)
        refund_grid.addWidget(QLabel("Remboursement associé"), 2, 0)
        refund_grid.addWidget(QLabel("Aucun remboursement."), 2, 1, 1, 2)
        self.root.addWidget(refund)
        self.root.addStretch(1)
        self.actions()


class ReimbursementPreviewDialog(LegacyPreviewDialog):
    def __init__(self, parent=None):
        super().__init__("Saisie d'un remboursement", parent, size=(780, 580))

        general = QGroupBox("Caractéristiques")
        grid = QGridLayout(general)
        grid.addWidget(QLabel("Date"), 0, 0)
        grid.addWidget(self.date_edit(), 0, 1)
        grid.addWidget(QLabel("Montant"), 0, 2)
        grid.addWidget(QLineEdit(), 0, 3)
        grid.addWidget(QLabel("€"), 0, 4)
        grid.addWidget(QLabel("Utilisateur"), 1, 0)
        user = QComboBox()
        user.addItem("Personne sélectionnée")
        grid.addWidget(user, 1, 1, 1, 4)
        grid.setColumnStretch(3, 1)
        self.root.addWidget(general)

        attached = QGroupBox("Déplacements rattachés")
        attached_layout = QVBoxLayout(attached)
        info = QLabel("Cochez les déplacements couverts par ce remboursement")
        info.setProperty("muted", True)
        attached_layout.addWidget(info)
        table = self.readonly_table(["", "Date", "Objet", "Trajet", "Montant"], 3)
        for row in range(3):
            table.setItem(row, 0, QTableWidgetItem("□"))
        attached_layout.addWidget(table, 1)
        self.root.addWidget(attached, 1)
        self.actions()


class ApplicationPreviewDialog(LegacyPreviewDialog):
    def __init__(self, parent=None):
        super().__init__("Saisie d'une candidature", parent, size=(880, 760))

        scroll_host = QWidget()
        stack = QVBoxLayout(scroll_host)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setSpacing(8)

        depot = QGroupBox("Dépôt de candidature")
        depot_layout = QGridLayout(depot)
        depot_layout.addWidget(QLabel("Date"), 0, 0)
        depot_layout.addWidget(self.date_edit(), 1, 0)
        depot_layout.addWidget(QLabel("Canal de dépôt"), 0, 1)
        channel = QComboBox()
        channel.addItems(["Courrier", "E-mail", "Site internet", "Remise en main propre"])
        depot_layout.addWidget(channel, 1, 1)
        depot_layout.addWidget(QLabel("Remarques"), 2, 0, 1, 2)
        depot_layout.addWidget(QLineEdit(), 3, 0, 1, 2)
        stack.addWidget(depot)

        offer = QGroupBox("Offre d'emploi")
        offer_layout = QHBoxLayout(offer)
        offer_layout.addWidget(QLabel("Offre"))
        offer_choice = QComboBox()
        offer_choice.addItem("Candidature spontanée")
        offer_layout.addWidget(offer_choice, 1)
        manage = QPushButton("…")
        manage.setEnabled(False)
        offer_layout.addWidget(manage)
        stack.addWidget(offer)

        available = QGroupBox("Disponibilités")
        available_layout = QVBoxLayout(available)
        periods = self.readonly_table(["Période"], 2)
        periods.setItem(0, 0, QTableWidgetItem("Du … au …"))
        periods.setItem(1, 0, QTableWidgetItem("Du … au …"))
        available_layout.addWidget(periods)
        available_layout.addWidget(QLabel("Remarques"))
        available_layout.addWidget(QLineEdit())
        stack.addWidget(available)

        desired = QGroupBox("Poste souhaité")
        desired_grid = QGridLayout(desired)
        desired_grid.addWidget(QLabel("Fonction"), 0, 0)
        desired_grid.addWidget(QLineEdit(), 0, 1)
        desired_grid.addWidget(QPushButton("…"), 0, 2)
        desired_grid.addWidget(QLabel("Affectation"), 1, 0)
        desired_grid.addWidget(QLineEdit(), 1, 1)
        desired_grid.addWidget(QPushButton("…"), 1, 2)
        desired_grid.addWidget(QLabel("Remarques"), 2, 0)
        desired_grid.addWidget(QLineEdit(), 2, 1, 1, 2)
        stack.addWidget(desired)

        answer = QGroupBox("Réponse")
        answer_grid = QGridLayout(answer)
        answer_grid.addWidget(QLabel("Décision"), 0, 0)
        decision = QComboBox()
        decision.addItems(["Non renseignée", "À revoir", "Refusée", "Retenue"])
        answer_grid.addWidget(decision, 0, 1)
        answer_grid.addWidget(QLabel("Remarques"), 1, 0)
        answer_grid.addWidget(QLineEdit(), 1, 1)
        mandatory = QCheckBox("Réponse obligatoire")
        answer_grid.addWidget(mandatory, 2, 0, 1, 2)
        communicated = QCheckBox("Réponse communiquée au candidat")
        answer_grid.addWidget(communicated, 3, 0, 1, 2)
        answer_grid.addWidget(QLabel("Le"), 4, 0)
        answer_grid.addWidget(self.date_edit(), 4, 1)
        answer_grid.addWidget(QLabel("Par"), 5, 0)
        answer_type = QComboBox()
        answer_type.addItems(["Courrier", "E-mail", "Téléphone", "Autre"])
        answer_grid.addWidget(answer_type, 5, 1)
        stack.addWidget(answer)

        self.root.addWidget(scroll_host, 1)
        self.actions()


class InterviewPreviewDialog(LegacyPreviewDialog):
    def __init__(self, parent=None):
        super().__init__("Saisie d'un entretien", parent, size=(620, 520))

        group = QGroupBox("Entretien")
        layout = QVBoxLayout(group)
        timing = QHBoxLayout()
        date_block = QVBoxLayout()
        date_block.addWidget(QLabel("Date"))
        date_block.addWidget(self.date_edit())
        timing.addLayout(date_block, 2)
        hour_block = QVBoxLayout()
        hour_block.addWidget(QLabel("Heure"))
        hour_block.addWidget(self.time_edit())
        timing.addLayout(hour_block, 1)
        layout.addLayout(timing)
        layout.addWidget(QLabel("Avis"))
        rating = QComboBox()
        rating.addItems(["Avis inconnu", "Pas convaincant", "Mitigé", "Bien", "Très bien"])
        layout.addWidget(rating)
        layout.addWidget(QLabel("Commentaire"))
        comment = QTextEdit()
        comment.setMinimumHeight(150)
        layout.addWidget(comment, 1)
        self.root.addWidget(group, 1)
        self.actions()


class ScenarioPreviewDialog(LegacyPreviewDialog):
    def __init__(self, parent=None):
        super().__init__("Création d'un scénario", parent, size=(980, 720))

        top = QHBoxLayout()
        parameters = QGroupBox("Paramètres du scénario")
        form = QGridLayout(parameters)
        form.addWidget(QLabel("Nom"), 0, 0)
        form.addWidget(QLineEdit(), 0, 1)
        form.addWidget(QLabel("Description"), 1, 0)
        description = QTextEdit()
        description.setMaximumHeight(80)
        form.addWidget(description, 1, 1)
        form.addWidget(QLabel("Personne"), 2, 0)
        person = QComboBox()
        person.addItem("Personne sélectionnée")
        form.addWidget(person, 2, 1)
        form.addWidget(QLabel("Période du"), 3, 0)
        period = QHBoxLayout()
        period.addWidget(self.date_edit())
        period.addWidget(QLabel("au"))
        period.addWidget(self.date_edit())
        period.addWidget(QCheckBox("Inclure toutes les catégories utilisées"))
        form.addLayout(period, 3, 1)
        form.setColumnStretch(1, 1)
        top.addWidget(parameters, 3)

        legend = QGroupBox("Légende")
        legend_layout = QVBoxLayout(legend)
        legend_layout.addWidget(QLabel("Catégories et symboles du scénario"))
        legend_layout.addStretch(1)
        top.addWidget(legend, 1)
        self.root.addLayout(top)

        detail = QGroupBox("Détail du scénario")
        detail_layout = QVBoxLayout(detail)
        table = self.readonly_table(["Période", "Catégorie", "Temps"], 8)
        detail_layout.addWidget(table, 1)
        options = QHBoxLayout()
        options.addWidget(QLabel("Détail"))
        detail_choice = QComboBox()
        detail_choice.addItems(["Aucun", "Jour", "Mois", "Année"])
        options.addWidget(detail_choice)
        options.addSpacing(12)
        options.addWidget(QLabel("Mode minutes"))
        minute_mode = QComboBox()
        minute_mode.addItems(["Normal", "Décimal"])
        options.addWidget(minute_mode)
        options.addStretch(1)
        categories = QPushButton("Sélection des catégories")
        categories.setEnabled(False)
        options.addWidget(categories)
        detail_layout.addLayout(options)
        self.root.addWidget(detail, 1)
        self.actions(extra=("Excel", "Imprimer"))
