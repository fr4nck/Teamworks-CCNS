from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class LegacyContractWizardDialog(QDialog):
    """Transposition Qt de DLG_Creation_contrat, strictement sans persistance.

    Le dialogue reprend la séquence des six pages wx historiques. Les contrôles
    sont manipulables pour juger la géométrie, mais aucun bouton ne déclenche de
    sauvegarde ou d'appel métier.
    """

    PAGE_TITLES = (
        "Bienvenue",
        "Modèle",
        "Caractéristiques",
        "Informations complémentaires",
        "Saisie complémentaire",
        "Terminé",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Création d'un contrat")
        self.resize(900, 760)
        self.setMinimumSize(720, 600)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        top = QHBoxLayout()
        self.step_label = QLabel()
        step_font = self.step_label.font()
        step_font.setBold(True)
        self.step_label.setFont(step_font)
        top.addWidget(self.step_label)
        top.addStretch(1)
        readonly = QLabel("Aperçu Qt · aucune écriture en base")
        readonly.setProperty("muted", True)
        top.addWidget(readonly)
        root.addLayout(top)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._page_welcome())
        self.pages.addWidget(self._page_model())
        self.pages.addWidget(self._page_characteristics())
        self.pages.addWidget(self._page_custom_fields())
        self.pages.addWidget(self._page_custom_values())
        self.pages.addWidget(self._page_finish())
        root.addWidget(self.pages, 1)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setProperty("separator", True)
        root.addWidget(separator)

        actions = QHBoxLayout()
        help_button = QPushButton("Aide")
        help_button.setEnabled(False)
        actions.addWidget(help_button)
        actions.addStretch(1)

        self.back_button = QPushButton("Retour")
        self.back_button.clicked.connect(self._previous_page)
        actions.addWidget(self.back_button)

        self.next_button = QPushButton("Suite")
        self.next_button.clicked.connect(self._next_page)
        actions.addWidget(self.next_button)

        cancel_button = QPushButton("Fermer")
        cancel_button.clicked.connect(self.reject)
        actions.addWidget(cancel_button)
        root.addLayout(actions)

        self.pages.currentChanged.connect(self._sync_navigation)
        self._sync_navigation(0)

    @staticmethod
    def _date_edit() -> QDateEdit:
        edit = QDateEdit(QDate.currentDate())
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd/MM/yyyy")
        return edit

    @staticmethod
    def _scroll_page(content: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    @staticmethod
    def _page_heading(title: str, intro: str) -> tuple[QWidget, QVBoxLayout]:
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)
        heading = QLabel(title)
        font = heading.font()
        font.setBold(True)
        font.setPointSize(max(font.pointSize(), 11))
        heading.setFont(font)
        root.addWidget(heading)
        text = QLabel(intro)
        text.setWordWrap(True)
        text.setProperty("muted", True)
        root.addWidget(text)
        return content, root

    def _page_welcome(self) -> QWidget:
        content, root = self._page_heading(
            "Bienvenue dans l'assistant de création de contrat",
            "Cet assistant reprend le parcours historique Teamworks : modèle, "
            "caractéristiques du contrat, compléments puis validation finale.",
        )

        banner = QGroupBox("Contrat")
        banner_layout = QVBoxLayout(banner)
        title = QLabel("Création ou modification d'un contrat")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addStretch(1)
        banner_layout.addWidget(title)
        text = QLabel(
            "Le contrat permet de définir la période d'emploi et ses caractéristiques. "
            "L'impression du contrat et de la DUE intervient ensuite depuis la fiche individuelle."
        )
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(text)
        banner_layout.addStretch(1)
        root.addWidget(banner, 1)
        return content

    def _page_model(self) -> QWidget:
        content, root = self._page_heading(
            "1. Importation d'un modèle de contrat",
            "Souhaitez-vous utiliser un modèle de contrat pour faciliter votre saisie ?",
        )

        no_model = QRadioButton("Non")
        yes_model = QRadioButton("Oui")
        no_model.setChecked(True)
        root.addWidget(no_model)
        root.addWidget(yes_model)

        group = QGroupBox("Choix du modèle")
        layout = QHBoxLayout(group)
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Nom", "Description"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEnabled(False)
        layout.addWidget(table, 1)
        manage = QPushButton("…")
        manage.setEnabled(False)
        layout.addWidget(manage, 0, Qt.AlignmentFlag.AlignTop)
        root.addWidget(group, 1)

        def update_model_state() -> None:
            enabled = yes_model.isChecked()
            table.setEnabled(enabled)
            manage.setEnabled(False)

        no_model.toggled.connect(update_model_state)
        yes_model.toggled.connect(update_model_state)
        return content

    def _page_characteristics(self) -> QWidget:
        content, root = self._page_heading(
            "2. Caractéristiques générales du contrat",
            "Sélectionnez le régime applicable au contrat.",
        )

        characteristics = QGroupBox("Régime et caractéristiques")
        grid = QGridLayout(characteristics)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        operation = QComboBox()
        operation.addItems(("Nouveau contrat", "Renouvellement d'un CDD", "Passage CDD → CDI"))
        previous = QComboBox()
        previous.addItem("CDD précédent…")
        previous.setEnabled(False)

        convention = QComboBox()
        convention.addItems((
            "CCNS — Sport (IDCC 2511)",
            "ÉCLAT",
            "Centres sociaux",
            "Autre / hors moteur conventionnel",
        ))
        contract_type = QComboBox()
        contract_type.addItems(("CDI", "CDD", "CEE", "Autre"))
        ccns_group = QComboBox()
        ccns_group.addItems(("Groupe 1", "Groupe 2", "Groupe 3", "Groupe 4", "Groupe 5", "Groupe 6", "Groupe 7", "Groupe 8"))
        cee_qualification = QComboBox()
        cee_qualification.addItems((
            "BAFA titulaire",
            "BAFA stagiaire",
            "Non diplômé",
            "Qualification équivalente",
            "BAFD titulaire",
            "BAFD stagiaire",
        ))
        legacy_class = QComboBox()
        legacy_class.addItem("Classification historique…")
        legacy_point = QComboBox()
        legacy_point.addItem("Valeur du point historique…")

        rows = (
            ("Nature de l'opération", operation),
            ("Contrat précédent", previous),
            ("Convention applicable", convention),
            ("Type de contrat", contract_type),
            ("Groupe CCNS", ccns_group),
            ("Qualification / statut CEE", cee_qualification),
            ("Classification historique", legacy_class),
            ("Valeur du point historique", legacy_point),
        )
        for row, (label, control) in enumerate(rows):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(control, row, 1)
            if row in (3, 6, 7):
                configure = QPushButton("…")
                configure.setEnabled(False)
                grid.addWidget(configure, row, 2)
        grid.setColumnStretch(1, 1)
        root.addWidget(characteristics)

        ccns = QGroupBox("Contrôle CCNS / SMIC")
        ccns_grid = QGridLayout(ccns)
        weekly = QDoubleSpinBox()
        weekly.setRange(0.0, 80.0)
        weekly.setDecimals(2)
        weekly.setSingleStep(0.25)
        weekly.setValue(35.0)
        salary = QLineEdit()
        salary.setPlaceholderText("Rémunération brute mensuelle")
        ccns_grid.addWidget(QLabel("Durée hebdomadaire"), 0, 0)
        ccns_grid.addWidget(weekly, 0, 1)
        ccns_grid.addWidget(QLabel("h / semaine"), 0, 2)
        ccns_grid.addWidget(QLabel("Rémunération brute"), 1, 0)
        ccns_grid.addWidget(salary, 1, 1)
        ccns_grid.addWidget(QLabel("€ brut / mois"), 1, 2)
        preview = QLabel("Contrôle réglementaire : aperçu uniquement dans ce dialogue de transposition.")
        preview.setProperty("muted", True)
        preview.setWordWrap(True)
        ccns_grid.addWidget(preview, 2, 0, 1, 3)
        ccns_grid.setColumnStretch(1, 1)
        root.addWidget(ccns)

        cee = QGroupBox("Barème CEE")
        cee_layout = QHBoxLayout(cee)
        cee_text = QLabel("Le forfait journalier applicable sera fourni par le moteur CEE.")
        cee_text.setWordWrap(True)
        cee_text.setProperty("muted", True)
        cee_layout.addWidget(cee_text, 1)
        cee_button = QPushButton("Barèmes CEE…")
        cee_button.setEnabled(False)
        cee_layout.addWidget(cee_button)
        root.addWidget(cee)

        dates = QGroupBox("Dates du contrat")
        dates_grid = QGridLayout(dates)
        dates_grid.addWidget(QLabel("À partir du"), 0, 0)
        dates_grid.addWidget(self._date_edit(), 0, 1)
        dates_grid.addWidget(QLabel("Jusqu'au"), 0, 2)
        dates_grid.addWidget(self._date_edit(), 0, 3)
        rupture = QCheckBox("Rupture anticipée du contrat au")
        rupture_date = self._date_edit()
        rupture_date.setEnabled(False)
        rupture.toggled.connect(rupture_date.setEnabled)
        dates_grid.addWidget(rupture, 1, 0, 1, 2)
        dates_grid.addWidget(rupture_date, 1, 2, 1, 2)
        root.addWidget(dates)

        trial = QGroupBox("Période d'essai")
        trial_layout = QVBoxLayout(trial)
        trial_row = QHBoxLayout()
        trial_check = QCheckBox("Prévoir une période d'essai")
        trial_row.addWidget(trial_check)
        trial_row.addWidget(QLabel("Durée"))
        trial_value = QSpinBox()
        trial_value.setRange(0, 365)
        trial_value.setEnabled(False)
        trial_row.addWidget(trial_value)
        trial_unit = QComboBox()
        trial_unit.addItems(("jour(s) calendaires", "mois calendaires"))
        trial_unit.setEnabled(False)
        trial_row.addWidget(trial_unit)
        trial_row.addStretch(1)
        trial_layout.addLayout(trial_row)
        hint = QLabel("La proposition automatique du moteur métier sera affichée ici.")
        hint.setWordWrap(True)
        hint.setProperty("muted", True)
        trial_layout.addWidget(hint)
        trial_check.toggled.connect(trial_value.setEnabled)
        trial_check.toggled.connect(trial_unit.setEnabled)
        root.addWidget(trial)
        root.addStretch(1)

        def refresh_operation() -> None:
            previous.setEnabled(operation.currentIndex() in (1, 2))

        def refresh_regime() -> None:
            is_ccns = convention.currentIndex() == 0
            is_cee = contract_type.currentText() == "CEE"
            ccns.setVisible(is_ccns and not is_cee)
            cee.setVisible(is_cee)
            ccns_group.setEnabled(is_ccns and not is_cee)
            cee_qualification.setEnabled(is_cee)

        operation.currentIndexChanged.connect(refresh_operation)
        convention.currentIndexChanged.connect(refresh_regime)
        contract_type.currentIndexChanged.connect(refresh_regime)
        refresh_operation()
        refresh_regime()
        return self._scroll_page(content)

    def _page_custom_fields(self) -> QWidget:
        content, root = self._page_heading(
            "3. Informations complémentaires (optionnel)",
            "Cochez uniquement les informations supplémentaires nécessaires à ce contrat. "
            "Les données déjà gérées par le contrat sont renseignées automatiquement.",
        )

        group = QGroupBox("Champs")
        layout = QHBoxLayout(group)
        fields = QListWidget()
        for label in (
            "Lieu de travail",
            "Fonction détaillée",
            "Observations contractuelles",
            "Référence interne",
        ):
            fields.addItem(f"□  {label}")
        layout.addWidget(fields, 1)
        manage = QPushButton("…")
        manage.setEnabled(False)
        layout.addWidget(manage, 0, Qt.AlignmentFlag.AlignTop)
        root.addWidget(group, 1)
        return content

    def _page_custom_values(self) -> QWidget:
        content, root = self._page_heading(
            "4. Saisie des informations complémentaires",
            "Renseignez les informations complémentaires sélectionnées.",
        )

        fields = QGroupBox("Exemple de champs sélectionnés")
        form = QFormLayout(fields)
        place = QLineEdit()
        place.setPlaceholderText("Ex. : gymnase municipal")
        function = QLineEdit()
        function.setPlaceholderText("Ex. : éducateur sportif")
        notes = QTextEdit()
        notes.setMaximumHeight(120)
        form.addRow("Lieu de travail", place)
        form.addRow("Fonction détaillée", function)
        form.addRow("Observations", notes)
        root.addWidget(fields)
        info = QLabel(
            "Dans l'application finale, cette page sera construite uniquement à partir des champs "
            "personnalisés réellement sélectionnés à l'étape précédente."
        )
        info.setProperty("muted", True)
        info.setWordWrap(True)
        root.addWidget(info)
        root.addStretch(1)
        return content

    def _page_finish(self) -> QWidget:
        content, root = self._page_heading(
            "Fin de l'assistant de création de contrat",
            "Vous avez saisi toutes les données du contrat. Dans l'application de production, "
            "la validation finale déclenchera les contrôles métier avant toute écriture.",
        )
        group = QGroupBox("Validation finale")
        layout = QVBoxLayout(group)
        message = QLabel(
            "Aucune donnée ne sera enregistrée depuis ce POC. Le bouton de validation reste "
            "volontairement désactivé tant que la chaîne d'écriture Qt n'est pas raccordée et testée."
        )
        message.setWordWrap(True)
        layout.addWidget(message)
        root.addWidget(group)
        root.addStretch(1)
        return content

    def _previous_page(self) -> None:
        index = self.pages.currentIndex()
        if index > 0:
            self.pages.setCurrentIndex(index - 1)

    def _next_page(self) -> None:
        index = self.pages.currentIndex()
        if index < self.pages.count() - 1:
            self.pages.setCurrentIndex(index + 1)

    def _sync_navigation(self, index: int) -> None:
        self.step_label.setText(f"Étape {index + 1}/{self.pages.count()} · {self.PAGE_TITLES[index]}")
        self.back_button.setEnabled(index > 0)
        if index == self.pages.count() - 1:
            self.next_button.setText("Valider")
            self.next_button.setEnabled(False)
        else:
            self.next_button.setText("Suite")
            self.next_button.setEnabled(True)
