from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qt_material import apply_stylesheet


@dataclass(frozen=True)
class Person:
    name: str
    role: str
    contract: str
    weekly_hours: str
    status: str
    email: str
    phone: str
    classification: str
    place: str
    birth_date: str
    employee_id: str
    medical: str
    mutual: str
    active: bool = True


PEOPLE = [
    Person("Gaëlle Desson", "Animatrice", "CDI", "35 h", "Dossier complet", "gaelle@example.org", "06 00 00 00 01", "Groupe 3", "La Guerche-de-Bretagne", "12/02/1990", "SAL-001", "À jour", "Affiliée"),
    Person("Thomas Loddé", "Éducateur sportif", "CDI intermittent", "24 h", "À contrôler", "thomas@example.org", "06 00 00 00 02", "Groupe 4", "Bais", "04/11/1988", "SAL-002", "Échéance proche", "Affilié"),
    Person("Léa Drouillé", "Animatrice", "CDD", "21 h", "Pièce manquante", "lea@example.org", "06 00 00 00 03", "Groupe 2", "Moutiers", "19/06/2002", "SAL-003", "À planifier", "Dispense"),
    Person("Valentin Guibourg", "Éducateur sportif", "CDI", "35 h", "Dossier complet", "valentin@example.org", "06 00 00 00 04", "Groupe 4", "Moutiers", "28/01/1995", "SAL-004", "À jour", "Affilié"),
    Person("Andréa Sévegrand", "Éducatrice sportive", "CDI", "35 h", "Dossier complet", "andrea@example.org", "06 00 00 00 05", "Groupe 4", "Bais", "07/09/1985", "SAL-005", "À jour", "Affiliée"),
    Person("Émilien Bioteau", "Éducateur sportif", "CDI", "35 h", "Dossier complet", "emilien@example.org", "06 00 00 00 06", "Groupe 4", "La Guerche-de-Bretagne", "22/03/1995", "SAL-006", "À jour", "Affilié"),
    Person("Ian Pennors", "Animateur", "CDD", "28 h", "À contrôler", "ian@example.org", "06 00 00 00 07", "Groupe 2", "La Guerche-de-Bretagne", "11/12/1998", "SAL-007", "À planifier", "Dispense"),
    Person("Nicolas Serrand", "Animateur", "CDI", "35 h", "Dossier complet", "nicolas@example.org", "06 00 00 00 08", "Groupe 3", "Bais", "13/05/1985", "SAL-008", "À jour", "Affilié"),
]


CONTRACT_ROWS = [
    ("CDI", "01/09/2024", "—", "Groupe 4", "35 h", "Actif", True),
    ("Avenant", "01/09/2025", "31/08/2026", "Groupe 4", "24 h", "Terminé", False),
    ("Avenant", "01/09/2026", "31/08/2027", "Groupe 4", "24 h", "À vérifier", True),
    ("CDD remplacement", "04/11/2025", "20/12/2025", "Groupe 3", "21 h", "Terminé", False),
    ("CDD accroissement", "06/01/2026", "31/03/2026", "Groupe 2", "18 h", "Terminé", False),
    ("CDI intermittent", "01/09/2023", "—", "Groupe 4", "304 h/an", "Actif", True),
    ("Avenant temps partiel", "01/01/2026", "30/06/2026", "Groupe 3", "28 h", "Terminé", False),
    ("CDD saisonnier", "06/07/2026", "31/07/2026", "Groupe 2", "35 h", "Terminé", False),
    ("CDD saisonnier", "03/08/2026", "28/08/2026", "Groupe 2", "35 h", "Terminé", False),
    ("Avenant fonction", "01/09/2026", "31/08/2027", "Groupe 4", "35 h", "Brouillon", True),
    ("CDD", "08/09/2026", "31/12/2026", "Groupe 1", "30 h", "À signer", True),
    ("Avenant", "01/09/2022", "31/08/2023", "Groupe 3", "24 h", "Archivé", False),
]


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, detail: str, emphasis: str = "normal"):
        super().__init__()
        self.setObjectName("metricCard")
        self.setProperty("emphasis", emphasis)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(3)
        label = QLabel(title)
        label.setProperty("muted", True)
        value_label = QLabel(value)
        font = value_label.font()
        font.setPointSize(17)
        font.setBold(True)
        value_label.setFont(font)
        detail_label = QLabel(detail)
        detail_label.setProperty("muted", True)
        layout.addWidget(label)
        layout.addWidget(value_label)
        layout.addWidget(detail_label)


class SectionTitle(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        font = self.font()
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font)


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Tableau de bord")
        font = title.font()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)
        subtitle = QLabel("POC Qt isolé — stress-test d'une interface RH dense, sans donnée de production")
        subtitle.setProperty("muted", True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(MetricCard("Salariés", "21", "18 dossiers complets"))
        cards.addWidget(MetricCard("Contrats actifs", "17", "2 contrôles à effectuer", "warning"))
        cards.addWidget(MetricCard("Alertes CCNS", "3", "1 contrôle prioritaire", "danger"))
        cards.addWidget(MetricCard("Absences", "2", "Période en cours"))
        layout.addLayout(cards)

        body = QSplitter(Qt.Horizontal)
        body.setChildrenCollapsible(False)

        alerts = QFrame()
        alerts.setObjectName("panel")
        alert_layout = QVBoxLayout(alerts)
        alert_layout.addWidget(SectionTitle("Points à traiter"))
        for text in (
            "Contrat à vérifier : dépassement potentiel de durée hebdomadaire",
            "Dossier salarié incomplet : justificatif de dispense mutuelle",
            "Visite médicale arrivant à échéance dans moins de 30 jours",
            "Avenant en brouillon non encore signé",
        ):
            row = QFrame()
            row.setObjectName("alertRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 7, 10, 7)
            badge = QLabel("!")
            badge.setObjectName("roundBadge")
            badge.setFixedSize(24, 24)
            badge.setAlignment(Qt.AlignCenter)
            row_layout.addWidget(badge)
            row_layout.addWidget(QLabel(text), 1)
            alert_layout.addWidget(row)
        alert_layout.addStretch(1)

        quick = QFrame()
        quick.setObjectName("panel")
        quick_layout = QVBoxLayout(quick)
        quick_layout.addWidget(SectionTitle("Accès rapides"))
        for label in ("Créer un contrat", "Contrôler les temps", "Générer un document RH", "Préparer les variables de paie", "Exporter les alertes"):
            button = QPushButton(label)
            button.setMinimumHeight(34)
            quick_layout.addWidget(button)
        quick_layout.addStretch(1)

        body.addWidget(alerts)
        body.addWidget(quick)
        body.setSizes([760, 400])
        layout.addWidget(body, 1)


class GeneralTab(QWidget):
    def __init__(self):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(4, 8, 12, 8)

        identity = QFrame()
        identity.setObjectName("panel")
        form = QFormLayout(identity)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.employee_id = QLineEdit()
        self.name = QLineEdit()
        self.birth_date = QLineEdit()
        self.role = QLineEdit()
        self.classification = QComboBox()
        self.classification.addItems([f"Groupe {i}" for i in range(1, 9)])
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.place = QComboBox()
        self.place.addItems(["La Guerche-de-Bretagne", "Bais", "Moutiers", "Visseiche", "Autre"])
        form.addRow("Identifiant", self.employee_id)
        form.addRow("Nom / prénom", self.name)
        form.addRow("Date de naissance", self.birth_date)
        form.addRow("Emploi", self.role)
        form.addRow("Classification", self.classification)
        form.addRow("E-mail", self.email)
        form.addRow("Téléphone", self.phone)
        form.addRow("Site principal", self.place)
        root.addWidget(SectionTitle("Identité et emploi"))
        root.addWidget(identity)

        compliance = QFrame()
        compliance.setObjectName("panel")
        compliance_form = QFormLayout(compliance)
        self.medical = QComboBox()
        self.medical.addItems(["À jour", "Échéance proche", "À planifier", "Non renseigné"])
        self.mutual = QComboBox()
        self.mutual.addItems(["Affilié", "Affiliée", "Dispense", "À vérifier"])
        self.minor = QCheckBox("Salarié mineur")
        self.night = QCheckBox("Travail de nuit possible")
        self.driver = QCheckBox("Déplacements professionnels")
        self.prof_card = QCheckBox("Carte professionnelle requise")
        compliance_form.addRow("Médecine du travail", self.medical)
        compliance_form.addRow("Mutuelle", self.mutual)
        compliance_form.addRow("", self.minor)
        compliance_form.addRow("", self.night)
        compliance_form.addRow("", self.driver)
        compliance_form.addRow("", self.prof_card)
        root.addWidget(SectionTitle("Conformité"))
        root.addWidget(compliance)
        root.addStretch(1)
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_person(self, person: Person):
        self.employee_id.setText(person.employee_id)
        self.name.setText(person.name)
        self.birth_date.setText(person.birth_date)
        self.role.setText(person.role)
        idx = self.classification.findText(person.classification)
        self.classification.setCurrentIndex(max(idx, 0))
        self.email.setText(person.email)
        self.phone.setText(person.phone)
        idx = self.place.findText(person.place)
        self.place.setCurrentIndex(max(idx, 0))
        idx = self.medical.findText(person.medical)
        self.medical.setCurrentIndex(max(idx, 0))
        idx = self.mutual.findText(person.mutual)
        self.mutual.setCurrentIndex(max(idx, 0))
        self.prof_card.setChecked("sport" in person.role.casefold())


class ContractDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau contrat — POC")
        self.resize(560, 430)
        root = QVBoxLayout(self)
        intro = QLabel("Exemple de dialogue métier dense. Aucune donnée n'est enregistrée.")
        intro.setProperty("muted", True)
        intro.setWordWrap(True)
        root.addWidget(intro)

        form_box = QFrame()
        form_box.setObjectName("panel")
        form = QFormLayout(form_box)
        contract_type = QComboBox()
        contract_type.addItems(["CDI", "CDD", "CDI intermittent", "CDD saisonnier", "Avenant"])
        classification = QComboBox()
        classification.addItems([f"Groupe {i}" for i in range(1, 9)])
        weekly = QSpinBox()
        weekly.setRange(1, 48)
        weekly.setValue(35)
        start = QLineEdit(date.today().strftime("%d/%m/%Y"))
        end = QLineEdit()
        end.setPlaceholderText("laisser vide si indéterminé")
        reason = QTextEdit()
        reason.setMaximumHeight(90)
        form.addRow("Type", contract_type)
        form.addRow("Classification", classification)
        form.addRow("Durée hebdomadaire", weekly)
        form.addRow("Date de début", start)
        form.addRow("Date de fin", end)
        form.addRow("Motif / notes", reason)
        root.addWidget(form_box)

        checks = QFrame()
        checks.setObjectName("panel")
        checks_layout = QVBoxLayout(checks)
        checks_layout.addWidget(QCheckBox("Contrôle CCNS effectué"))
        checks_layout.addWidget(QCheckBox("Planning annuel annexé"))
        checks_layout.addWidget(QCheckBox("Documents obligatoires présents"))
        root.addWidget(checks)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)


class ContractsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(8)

        toolbar = QFrame()
        toolbar.setObjectName("commandBar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        new_button = QPushButton("Nouveau contrat")
        new_button.clicked.connect(self._open_contract_dialog)
        toolbar_layout.addWidget(new_button)
        toolbar_layout.addWidget(QPushButton("Créer un avenant"))
        toolbar_layout.addWidget(QPushButton("Dupliquer"))
        toolbar_layout.addWidget(QPushButton("Contrôler CCNS"))
        toolbar_layout.addWidget(QPushButton("Générer le document"))
        toolbar_layout.addStretch(1)
        self.only_active = QCheckBox("Actifs uniquement")
        self.only_active.stateChanged.connect(self._apply_filter)
        toolbar_layout.addWidget(self.only_active)
        layout.addWidget(toolbar)

        self.table = QTableWidget(len(CONTRACT_ROWS), 8)
        self.table.setHorizontalHeaderLabels(["✓", "Type", "Début", "Fin", "Classification", "Durée", "État", "Contrôle"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 34)

        for row_index, row in enumerate(CONTRACT_ROWS):
            contract_type, start, end, group, duration, state, active = row
            checkbox = QCheckBox()
            checkbox.setChecked(row_index in (0, 2, 9))
            checkbox.setProperty("rowSelector", True)
            holder = QWidget()
            h = QHBoxLayout(holder)
            h.setContentsMargins(0, 0, 0, 0)
            h.setAlignment(Qt.AlignCenter)
            h.addWidget(checkbox)
            self.table.setCellWidget(row_index, 0, holder)
            for column_index, value in enumerate((contract_type, start, end, group, duration, state), start=1):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
            control = "Conforme" if state in ("Actif", "Terminé", "Archivé") else "À revoir"
            control_item = QTableWidgetItem(control)
            if control == "À revoir":
                control_item.setData(Qt.UserRole, "warning")
            self.table.setItem(row_index, 7, control_item)
            self.table.setRowHeight(row_index, 30)
            self.table.item(row_index, 1).setData(Qt.UserRole, active)

        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.selection_label = QLabel("3 lignes cochées")
        self.selection_label.setProperty("muted", True)
        footer.addWidget(self.selection_label)
        footer.addStretch(1)
        footer.addWidget(QPushButton("Archiver la sélection"))
        footer.addWidget(QPushButton("Exporter"))
        layout.addLayout(footer)

    def _apply_filter(self):
        active_only = self.only_active.isChecked()
        for row in range(self.table.rowCount()):
            active = bool(self.table.item(row, 1).data(Qt.UserRole))
            self.table.setRowHidden(row, active_only and not active)

    def _open_contract_dialog(self):
        dialog = ContractDialog(self)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "POC", "Simulation uniquement : aucune donnée n'a été enregistrée.")


class TimeTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 0)

        toolbar = QFrame()
        toolbar.setObjectName("commandBar")
        bar = QHBoxLayout(toolbar)
        bar.setContentsMargins(8, 6, 8, 6)
        period = QComboBox()
        period.addItems(["Septembre 2026", "Octobre 2026", "Novembre 2026", "Année 2026-2027"])
        bar.addWidget(QLabel("Période"))
        bar.addWidget(period)
        bar.addSpacing(12)
        bar.addWidget(QCheckBox("Afficher les anomalies"))
        bar.addStretch(1)
        bar.addWidget(QPushButton("Recalculer"))
        bar.addWidget(QPushButton("Exporter"))
        root.addWidget(toolbar)

        table = QTableWidget(18, 8)
        table.setHorizontalHeaderLabels(["Semaine", "Prévu", "Réalisé", "Écart", "Repos", "Pause", "Amplitude", "État"])
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r in range(18):
            week = 36 + r
            planned = 35 if r % 4 else 42
            actual = planned + ((r % 3) - 1) * 2
            delta = actual - planned
            state = "OK" if actual <= 44 else "À contrôler"
            values = (f"S{week}", f"{planned} h", f"{actual} h", f"{delta:+d} h", "35 h", "20 min", "10 h 30", state)
            for c, value in enumerate(values):
                table.setItem(r, c, QTableWidgetItem(value))
            table.setRowHeight(r, 29)
        root.addWidget(table)


class DocumentsTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.addWidget(SectionTitle("Documents RH"))
        intro = QLabel("Stress-test de listes d'actions, états et cases à cocher. Aucun fichier réel n'est utilisé.")
        intro.setProperty("muted", True)
        root.addWidget(intro)

        rows = [
            ("Contrat de travail", "Généré", True),
            ("Avenant", "À générer", False),
            ("Dispense mutuelle", "Justificatif reçu", True),
            ("Attestation d'emploi", "Disponible", True),
            ("Certificat de travail", "Non applicable", False),
            ("Autorisation mineur", "Non applicable", False),
            ("Fiche visite médicale", "À renouveler", True),
        ]
        table = QTableWidget(len(rows), 4)
        table.setHorizontalHeaderLabels(["Inclure", "Document", "État", "Action"])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        for r, (doc, state, checked) in enumerate(rows):
            check = QCheckBox()
            check.setChecked(checked)
            holder = QWidget()
            h = QHBoxLayout(holder)
            h.setContentsMargins(0, 0, 0, 0)
            h.setAlignment(Qt.AlignCenter)
            h.addWidget(check)
            table.setCellWidget(r, 0, holder)
            table.setItem(r, 1, QTableWidgetItem(doc))
            table.setItem(r, 2, QTableWidgetItem(state))
            button = QPushButton("Ouvrir" if state not in ("À générer", "Non applicable") else "Générer")
            table.setCellWidget(r, 3, button)
            table.setRowHeight(r, 34)
        root.addWidget(table)


class PlaceholderTab(QWidget):
    def __init__(self, title: str, text: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 14, 8, 8)
        layout.addWidget(SectionTitle(title))
        description = QLabel(text)
        description.setWordWrap(True)
        layout.addWidget(description)
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.addWidget(QCheckBox("Exemple d'option métier"))
        panel_layout.addWidget(QCheckBox("Deuxième option avec libellé plus long"))
        panel_layout.addWidget(QLineEdit("Champ de saisie dense"))
        panel_layout.addWidget(QComboBox())
        layout.addWidget(panel)
        layout.addStretch(1)


class PeoplePage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Individus")
        title_font = title.font()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        subtitle = QLabel("Dossier salarié — test de densité, tableaux, formulaires, checkboxes et dialogues")
        subtitle.setProperty("muted", True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)
        header.addWidget(QPushButton("Ajouter"))
        header.addWidget(QPushButton("Imprimer"))
        header.addWidget(QPushButton("Exporter"))
        root.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = QFrame()
        left.setObjectName("sidePanel")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un salarié…")
        self.search.textChanged.connect(self._filter)
        left_layout.addWidget(self.search)
        filters = QHBoxLayout()
        self.active_only = QCheckBox("Actifs")
        self.active_only.setChecked(True)
        self.active_only.stateChanged.connect(self._filter_now)
        filters.addWidget(self.active_only)
        filters.addStretch(1)
        left_layout.addLayout(filters)
        self.list = QListWidget()
        self.list.setSpacing(1)
        for person in PEOPLE:
            item = QListWidgetItem(f"{person.name}\n{person.role} · {person.contract}")
            item.setData(Qt.UserRole, person)
            item.setSizeHint(QSize(260, 50))
            self.list.addItem(item)
        self.list.currentItemChanged.connect(self._select)
        left_layout.addWidget(self.list)
        left_layout.addWidget(QLabel(f"{len(PEOPLE)} salariés affichés"))

        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(14, 10, 14, 10)
        right_layout.setSpacing(8)

        person_header = QFrame()
        person_header.setObjectName("personHeader")
        header_layout = QHBoxLayout(person_header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        person_header_text = QVBoxLayout()
        self.person_name = QLabel("Sélectionnez un salarié")
        person_font = self.person_name.font()
        person_font.setPointSize(18)
        person_font.setBold(True)
        self.person_name.setFont(person_font)
        self.person_meta = QLabel("")
        self.person_meta.setProperty("muted", True)
        person_header_text.addWidget(self.person_name)
        person_header_text.addWidget(self.person_meta)
        header_layout.addLayout(person_header_text)
        header_layout.addStretch(1)
        self.status = QLabel("")
        self.status.setObjectName("statusBadge")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setMinimumWidth(150)
        header_layout.addWidget(self.status)
        right_layout.addWidget(person_header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.general = GeneralTab()
        self.tabs.addTab(self.general, "Généralités")
        self.tabs.addTab(PlaceholderTab("Qualifications", "Diplômes, cartes professionnelles, habilitations et classifications métier."), "Qualifications")
        self.tabs.addTab(ContractsTab(), "Contrats")
        self.tabs.addTab(TimeTab(), "Présences / temps")
        self.tabs.addTab(PlaceholderTab("Scénarios", "Organisation annuelle, affectations et scénarios horaires."), "Scénarios")
        self.tabs.addTab(PlaceholderTab("Frais", "Frais kilométriques, remboursements et pièces justificatives."), "Frais")
        self.tabs.addTab(DocumentsTab(), "Documents RH")
        self.tabs.addTab(PlaceholderTab("Recrutement", "Candidatures, entretiens, pièces et parcours d'intégration."), "Recrutement")
        right_layout.addWidget(self.tabs, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([310, 1050])
        root.addWidget(splitter, 1)
        self.list.setCurrentRow(0)

    def _filter_now(self):
        self._filter(self.search.text())

    def _filter(self, text: str):
        needle = text.casefold().strip()
        active_only = self.active_only.isChecked()
        visible = 0
        for index in range(self.list.count()):
            item = self.list.item(index)
            person = item.data(Qt.UserRole)
            hidden = needle not in item.text().casefold() or (active_only and not person.active)
            item.setHidden(hidden)
            visible += 0 if hidden else 1

    def _select(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None):
        if current is None:
            return
        person = current.data(Qt.UserRole)
        self.person_name.setText(person.name)
        self.person_meta.setText(f"{person.role} · {person.classification} · {person.contract} · {person.weekly_hours} · {person.place}")
        self.status.setText(person.status)
        self.status.setProperty("status", "warning" if person.status != "Dossier complet" else "ok")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.general.set_person(person)


class SimplePage(QWidget):
    def __init__(self, title: str, text: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        label = QLabel(title)
        font = label.font()
        font.setPointSize(20)
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label)
        description = QLabel(text)
        description.setWordWrap(True)
        description.setProperty("muted", True)
        layout.addWidget(description)
        table = QTableWidget(14, 5)
        table.setHorizontalHeaderLabels(["Élément", "Type", "État", "Échéance", "Action"])
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r in range(14):
            for c, value in enumerate((f"Ligne {r + 1}", "Donnée", "OK" if r % 4 else "À traiter", "Sept. 2026", "Ouvrir")):
                table.setItem(r, c, QTableWidgetItem(value))
            table.setRowHeight(r, 30)
        layout.addWidget(table)


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Préférences d'affichage — POC")
        self.resize(500, 330)
        root = QVBoxLayout(self)
        form_box = QFrame()
        form_box.setObjectName("panel")
        form = QFormLayout(form_box)
        density = QComboBox()
        density.addItems(["Compacte", "Normale", "Confortable"])
        density.setCurrentText("Compacte")
        form.addRow("Densité", density)
        form.addRow("Taille de texte", QComboBox())
        form.addRow("", QCheckBox("Respecter le thème système au démarrage"))
        form.addRow("", QCheckBox("Animations réduites"))
        form.addRow("", QCheckBox("Focus clavier renforcé"))
        root.addWidget(form_box)
        root.addWidget(QLabel("Ce dialogue sert à vérifier le rendu des contrôles courants. Les options ne sont pas persistées."))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.setWindowTitle("Teamworks — POC Qt isolé")
        self.resize(1500, 920)
        self.setMinimumSize(1100, 720)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        nav = QFrame()
        nav.setObjectName("navigation")
        nav.setFixedWidth(225)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(6)

        brand = QLabel("TEAMWORKS")
        brand_font = brand.font()
        brand_font.setPointSize(15)
        brand_font.setBold(True)
        brand.setFont(brand_font)
        nav_layout.addWidget(brand)
        edition = QLabel("CCNS · POC Qt")
        edition.setProperty("muted", True)
        nav_layout.addWidget(edition)
        nav_layout.addSpacing(14)

        self.pages = QStackedWidget()
        pages = [
            ("Accueil", HomePage()),
            ("Individus", PeoplePage()),
            ("Présences", SimplePage("Présences", "Vue globale de décompte des présences, absences et temps de travail.")),
            ("Planning", SimplePage("Planning", "Affectations, périodes, volumes et contrôle de cohérence.")),
            ("Recrutement", SimplePage("Recrutement", "Candidats, candidatures, entretiens et suivi des recrutements.")),
            ("Documents RH", SimplePage("Documents RH", "Catalogue documentaire, génération, suivi et statut des pièces.")),
        ]
        self.nav_buttons: list[QPushButton] = []
        for index, (label, page) in enumerate(pages):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setMinimumHeight(36)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.clicked.connect(lambda _checked=False, i=index: self.pages.setCurrentIndex(i))
            nav_layout.addWidget(button)
            self.nav_buttons.append(button)
            self.pages.addWidget(page)
            if index == 1:
                button.setChecked(True)
                self.pages.setCurrentIndex(1)

        nav_layout.addStretch(1)
        prefs = QPushButton("Préférences…")
        prefs.clicked.connect(self._settings)
        nav_layout.addWidget(prefs)
        nav_layout.addSpacing(4)
        nav_layout.addWidget(QLabel("Thème"))
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Clair", "Sombre"])
        self.theme_selector.currentIndexChanged.connect(self._change_theme)
        nav_layout.addWidget(self.theme_selector)

        root.addWidget(nav)
        root.addWidget(self.pages, 1)

        self.statusBar().showMessage("POC isolé — aucune donnée Teamworks de production n'est chargée")

    def _settings(self):
        SettingsDialog(self).exec()

    def _change_theme(self, index: int):
        apply_teamworks_theme(self.app, dark=index == 1)


def apply_teamworks_theme(app: QApplication, dark: bool):
    theme = "dark_blue.xml" if dark else "light_blue.xml"
    extras = {"density_scale": "-1", "font_family": "Segoe UI"}
    apply_stylesheet(app, theme=theme, extra=extras)

    app.setStyleSheet(
        app.styleSheet()
        + """
        QFrame#navigation {
            border-right: 1px solid rgba(127, 127, 127, 0.28);
        }
        QFrame#panel, QFrame#metricCard, QFrame#personHeader, QFrame#sidePanel {
            border: 1px solid rgba(127, 127, 127, 0.25);
            border-radius: 7px;
        }
        QFrame#commandBar {
            border: 1px solid rgba(127, 127, 127, 0.22);
            border-radius: 6px;
        }
        QFrame#alertRow {
            border-bottom: 1px solid rgba(127, 127, 127, 0.18);
        }
        QLabel[muted="true"] {
            color: rgba(127, 127, 127, 0.95);
        }
        QLabel#statusBadge {
            padding: 6px 10px;
            border: 1px solid rgba(127, 127, 127, 0.35);
            border-radius: 8px;
            font-weight: 600;
        }
        QLabel#statusBadge[status="warning"] {
            border-color: rgba(215, 145, 0, 0.75);
        }
        QLabel#statusBadge[status="ok"] {
            border-color: rgba(50, 150, 90, 0.70);
        }
        QLabel#roundBadge {
            border: 1px solid rgba(215, 145, 0, 0.75);
            border-radius: 12px;
            font-weight: 700;
        }
        QPushButton#navButton {
            text-align: left;
            padding-left: 12px;
        }
        QTableWidget {
            gridline-color: rgba(127, 127, 127, 0.20);
        }
        QTableWidget::item {
            padding-left: 5px;
            padding-right: 5px;
        }
        QTabBar::tab {
            min-width: 96px;
        }
        """
    )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Teamworks Qt POC")
    app.setOrganizationName("Pêle-Mêle Sports et Loisirs")
    apply_teamworks_theme(app, dark=False)
    window = MainWindow(app)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
