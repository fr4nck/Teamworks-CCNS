from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
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


PEOPLE = [
    Person(
        "Gaëlle Desson",
        "Animatrice",
        "CDI",
        "35 h",
        "Dossier complet",
        "gaelle@example.org",
        "06 00 00 00 01",
        "Groupe 3",
        "La Guerche-de-Bretagne",
    ),
    Person(
        "Thomas Loddé",
        "Éducateur sportif",
        "CDI intermittent",
        "24 h",
        "À contrôler",
        "thomas@example.org",
        "06 00 00 00 02",
        "Groupe 4",
        "Bais",
    ),
    Person(
        "Léa Drouillé",
        "Animatrice",
        "CDD",
        "21 h",
        "Pièce manquante",
        "lea@example.org",
        "06 00 00 00 03",
        "Groupe 2",
        "Moutiers",
    ),
    Person(
        "Valentin Guibourg",
        "Éducateur sportif",
        "CDI",
        "35 h",
        "Dossier complet",
        "valentin@example.org",
        "06 00 00 00 04",
        "Groupe 4",
        "Moutiers",
    ),
    Person(
        "Andréa Sévegrand",
        "Éducatrice sportive",
        "CDI",
        "35 h",
        "Dossier complet",
        "andrea@example.org",
        "06 00 00 00 05",
        "Groupe 4",
        "Bais",
    ),
]


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, detail: str):
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
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


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Tableau de bord")
        font = title.font()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)
        subtitle = QLabel("Prototype Qt isolé — aucune donnée réelle n'est chargée")
        subtitle.setProperty("muted", True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        cards = QHBoxLayout()
        cards.addWidget(MetricCard("Salariés", "21", "18 dossiers complets"))
        cards.addWidget(MetricCard("Contrats actifs", "17", "2 contrôles à effectuer"))
        cards.addWidget(MetricCard("Alertes CCNS", "3", "1 contrôle prioritaire"))
        cards.addWidget(MetricCard("Absences", "2", "Période en cours"))
        layout.addLayout(cards)

        alert = QFrame()
        alert.setObjectName("warningCard")
        alert_layout = QVBoxLayout(alert)
        alert_title = QLabel("Points à traiter")
        alert_title.setStyleSheet("font-weight: 600;")
        alert_layout.addWidget(alert_title)
        alert_layout.addWidget(QLabel("• 1 contrat nécessite un contrôle de durée du travail"))
        alert_layout.addWidget(QLabel("• 1 dossier salarié comporte une pièce manquante"))
        alert_layout.addWidget(QLabel("• 1 échéance de visite médicale approche"))
        layout.addWidget(alert)
        layout.addStretch(1)


class GeneralTab(QWidget):
    def __init__(self):
        super().__init__()
        self.form = QFormLayout(self)
        self.name = QLineEdit()
        self.role = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.place = QLineEdit()
        self.form.addRow("Nom", self.name)
        self.form.addRow("Emploi", self.role)
        self.form.addRow("E-mail", self.email)
        self.form.addRow("Téléphone", self.phone)
        self.form.addRow("Site principal", self.place)

    def set_person(self, person: Person):
        self.name.setText(person.name)
        self.role.setText(person.role)
        self.email.setText(person.email)
        self.phone.setText(person.phone)
        self.place.setText(person.place)


class ContractsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QPushButton("Nouveau contrat"))
        toolbar.addWidget(QPushButton("Créer un avenant"))
        toolbar.addWidget(QPushButton("Contrôler CCNS"))
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.table = QTableWidget(3, 6)
        self.table.setHorizontalHeaderLabels(
            ["Type", "Début", "Fin", "Classification", "Durée", "État"]
        )
        rows = [
            ("CDI", "01/09/2024", "—", "Groupe 4", "35 h", "Actif"),
            ("Avenant", "01/09/2025", "31/08/2026", "Groupe 4", "24 h", "Terminé"),
            ("Avenant", "01/09/2026", "31/08/2027", "Groupe 4", "24 h", "À vérifier"),
        ]
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)


class PlaceholderTab(QWidget):
    def __init__(self, title: str, text: str):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel(title)
        font = label.font()
        font.setPointSize(15)
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label)
        description = QLabel(text)
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addStretch(1)


class PeoplePage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Individus")
        title_font = title.font()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        subtitle = QLabel("Liste des salariés et accès à la fiche individuelle")
        subtitle.setProperty("muted", True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)
        header.addWidget(QPushButton("Ajouter"))
        header.addWidget(QPushButton("Exporter"))
        root.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un salarié…")
        self.search.textChanged.connect(self._filter)
        left_layout.addWidget(self.search)
        self.list = QListWidget()
        for person in PEOPLE:
            item = QListWidgetItem(f"{person.name}\n{person.role} · {person.contract}")
            item.setData(Qt.UserRole, person)
            self.list.addItem(item)
        self.list.currentItemChanged.connect(self._select)
        left_layout.addWidget(self.list)

        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(14, 10, 14, 10)

        self.person_name = QLabel("Sélectionnez un salarié")
        person_font = self.person_name.font()
        person_font.setPointSize(18)
        person_font.setBold(True)
        self.person_name.setFont(person_font)
        self.person_meta = QLabel("")
        self.person_meta.setProperty("muted", True)
        self.status = QLabel("")
        self.status.setObjectName("statusBadge")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setMinimumWidth(140)

        person_header = QHBoxLayout()
        person_header_text = QVBoxLayout()
        person_header_text.addWidget(self.person_name)
        person_header_text.addWidget(self.person_meta)
        person_header.addLayout(person_header_text)
        person_header.addStretch(1)
        person_header.addWidget(self.status)
        right_layout.addLayout(person_header)

        self.tabs = QTabWidget()
        self.general = GeneralTab()
        self.tabs.addTab(self.general, "Généralités")
        self.tabs.addTab(
            PlaceholderTab(
                "Qualifications",
                "Diplômes, cartes professionnelles, habilitations et classifications métier.",
            ),
            "Qualifications",
        )
        self.tabs.addTab(ContractsTab(), "Contrats")
        self.tabs.addTab(
            PlaceholderTab(
                "Présences",
                "Décompte et historique des temps de présence, absences et compteurs individuels.",
            ),
            "Présences",
        )
        self.tabs.addTab(
            PlaceholderTab(
                "Frais",
                "Frais kilométriques, remboursements et pièces justificatives associées.",
            ),
            "Frais",
        )
        right_layout.addWidget(self.tabs)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([330, 950])
        root.addWidget(splitter)

        self.list.setCurrentRow(0)

    def _filter(self, text: str):
        needle = text.casefold().strip()
        for index in range(self.list.count()):
            item = self.list.item(index)
            item.setHidden(needle not in item.text().casefold())

    def _select(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None):
        if current is None:
            return
        person = current.data(Qt.UserRole)
        self.person_name.setText(person.name)
        self.person_meta.setText(
            f"{person.role} · {person.classification} · {person.contract} · {person.weekly_hours}"
        )
        self.status.setText(person.status)
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
        layout.addWidget(description)
        layout.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.dark = False
        self.setWindowTitle("Teamworks — POC Qt isolé")
        self.resize(1380, 860)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        nav = QFrame()
        nav.setObjectName("navigation")
        nav.setFixedWidth(220)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        brand = QLabel("TEAMWORKS")
        brand_font = brand.font()
        brand_font.setPointSize(15)
        brand_font.setBold(True)
        brand.setFont(brand_font)
        nav_layout.addWidget(brand)
        nav_layout.addSpacing(14)

        self.pages = QStackedWidget()
        pages = [
            ("Accueil", HomePage()),
            ("Individus", PeoplePage()),
            ("Présences", SimplePage("Présences", "Vue de décompte des présences et du temps de travail.")),
            ("Recrutement", SimplePage("Recrutement", "Candidats, candidatures, entretiens et suivi des recrutements.")),
        ]

        for index, (label, page) in enumerate(pages):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.clicked.connect(lambda _checked=False, i=index: self.pages.setCurrentIndex(i))
            nav_layout.addWidget(button)
            self.pages.addWidget(page)
            if index == 1:
                button.setChecked(True)
                self.pages.setCurrentIndex(1)

        nav_layout.addStretch(1)
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Thème"))
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Clair", "Sombre"])
        self.theme_selector.currentIndexChanged.connect(self._change_theme)
        theme_row.addWidget(self.theme_selector)
        nav_layout.addLayout(theme_row)

        root.addWidget(nav)
        root.addWidget(self.pages, 1)

    def _change_theme(self, index: int):
        self.dark = index == 1
        apply_teamworks_theme(self.app, self.dark)


def apply_teamworks_theme(app: QApplication, dark: bool):
    theme = "dark_blue.xml" if dark else "light_blue.xml"
    extras = {
        "density_scale": "0",
        "font_family": "Segoe UI",
    }
    apply_stylesheet(app, theme=theme, extra=extras)

    # Petites surcharges propres au POC : le moteur de thème reste global,
    # ces règles testent seulement les rôles de surfaces Teamworks.
    app.setStyleSheet(
        app.styleSheet()
        + """
        QFrame#navigation {
            border-right: 1px solid rgba(127, 127, 127, 0.25);
        }
        QFrame#metricCard, QFrame#warningCard {
            border: 1px solid rgba(127, 127, 127, 0.25);
            border-radius: 8px;
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
        QTableWidget {
            gridline-color: rgba(127, 127, 127, 0.22);
        }
        """
    )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Teamworks Qt POC")
    apply_teamworks_theme(app, dark=False)
    window = MainWindow(app)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
