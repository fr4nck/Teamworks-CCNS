from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from legacy_sheets import (
    ApplicationPreviewDialog,
    InterviewPreviewDialog,
    PiecePreviewDialog,
    PresencePreviewDialog,
)
from scenario_expense_dialogs import (
    ReimbursementPreviewDialog,
    ScenarioPreviewDialog,
    TripPreviewDialog,
)
from ui.common import (
    ActionSpec,
    TOKENS,
    TwActionBar,
    TwDataTable,
    TwDialogShell,
    TwFormSection,
)


IconLoader = Callable[[str], QIcon]


def _empty_model(headers: tuple[str, ...], parent: QWidget) -> QStandardItemModel:
    model = QStandardItemModel(0, len(headers), parent)
    model.setHorizontalHeaderLabels(list(headers))
    return model


def _table(model, *, hide_header: bool = False) -> TwDataTable:
    table = TwDataTable(model=model)
    table.horizontalHeader().setVisible(not hide_header)
    return table


def _open_preview(dialog_cls, owner: QWidget) -> None:
    dialog_cls(owner.window()).exec()


class QualificationsSelectionPreviewDialog(TwDialogShell):
    """Aperçu du `MultiChoiceDialog` historique, sans données ni écriture."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "Sélection des qualifications",
            parent,
            profile="standard",
            primary_label="Valider",
            cancel_label="Fermer",
        )
        body = QWidget(self)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS.spacing.sm)

        message = QLabel(
            "Sélectionnez les qualifications que possède la personne dans la liste proposée :"
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        choices = QListWidget()
        choices.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        layout.addWidget(choices, 1)

        note = QLabel("Aucune qualification métier n'est chargée dans cet aperçu Qt.")
        note.setProperty("muted", True)
        note.setWordWrap(True)
        layout.addWidget(note)

        self.set_content(body)
        self.help_button.setEnabled(False)
        self.set_primary_enabled(False)


class QuestionnairePage(QWidget):
    """Questionnaire historique : questions à gauche, réponses à droite."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
        )

        section = TwFormSection("Questionnaire")
        self.model = _empty_model(("Question", "Réponse"), self)
        self.table = _table(self.model)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        section.add_widget(self.table, 1)
        root.addWidget(section, 1)


class QualificationsPage(QWidget):
    """Transposition de ``CTRL_Page_qualifications`` sans persistance."""

    def __init__(self, icon_loader: IconLoader, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icon_loader = icon_loader

        root = QVBoxLayout(self)
        root.setContentsMargins(
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
        )
        root.setSpacing(TOKENS.spacing.md)

        top = QHBoxLayout()
        top.setSpacing(TOKENS.spacing.md)

        required = TwFormSection("Pièces à fournir")
        self.required_model = _empty_model(("Pièce à fournir",), self)
        self.required_table = _table(self.required_model, hide_header=True)
        required.add_widget(self.required_table, 1)
        top.addWidget(required, 1)

        qualifications = TwFormSection("Qualifications")
        self.qualifications_model = _empty_model(("Qualification",), self)
        self.qualifications_table = _table(self.qualifications_model, hide_header=True)
        qualifications.add_widget(self.qualifications_table, 1)
        self.qualifications_actions = TwActionBar(
            [
                ActionSpec(
                    "edit_qualifications",
                    "Modifier les qualifications",
                    "Modifier.png",
                    "Ouvrir l'aperçu de sélection des qualifications",
                    enabled=True,
                )
            ],
            icon_loader=icon_loader,
        )
        self.qualifications_actions.triggered.connect(self._on_qualifications_action)
        qualifications.add_widget(self.qualifications_actions)
        top.addWidget(qualifications, 1)
        root.addLayout(top, 1)

        received = TwFormSection("Pièces reçues")
        self.received_model = _empty_model(
            ("Type de pièce", "Obtention", "Expiration", "Observations"), self
        )
        self.received_table = _table(self.received_model)
        received.add_widget(self.received_table, 1)
        self.received_actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter une pièce", "Ajouter.png", "Saisir une nouvelle pièce"),
                ActionSpec(
                    "edit",
                    "Modifier",
                    "Modifier.png",
                    "Modifier la pièce sélectionnée",
                    enabled=False,
                ),
                ActionSpec(
                    "delete",
                    "Supprimer",
                    "Supprimer.png",
                    "Supprimer la pièce sélectionnée",
                    role="destructive",
                    enabled=False,
                ),
            ],
            icon_loader=icon_loader,
        )
        self.received_actions.triggered.connect(self._on_received_action)
        received.add_widget(self.received_actions)
        root.addWidget(received, 1)

    def _on_qualifications_action(self, action_id: str) -> None:
        if action_id == "edit_qualifications":
            QualificationsSelectionPreviewDialog(self.window()).exec()

    def _on_received_action(self, action_id: str) -> None:
        if action_id == "add":
            _open_preview(PiecePreviewDialog, self)


class PresencesPage(QWidget):
    """Transposition de ``CTRL_Page_presences`` sans lecture/écriture métier."""

    HEADERS = ("Date", "Vacances", "Horaires", "Durée", "Intitulé")

    def __init__(self, icon_loader: IconLoader, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
        )

        section = TwFormSection("Présences")
        self.actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter", "Ajouter.png", "Saisir une nouvelle présence"),
                ActionSpec("edit", "Modifier", "Modifier.png", "Modifier la présence sélectionnée", enabled=False),
                ActionSpec(
                    "delete",
                    "Supprimer",
                    "Supprimer.png",
                    "Supprimer la présence sélectionnée",
                    role="destructive",
                    enabled=False,
                ),
                ActionSpec("print", "Imprimer", "Imprimante.png", "Imprimer une feuille d'heures", enabled=False),
                ActionSpec("stats", "Statistiques", "Diagramme.png", "Afficher les statistiques de présences", enabled=False),
                ActionSpec("model", "Appliquer un modèle", "Modele.png", "Appliquer un modèle de présences", enabled=False),
            ],
            icon_loader=icon_loader,
        )
        self.actions.triggered.connect(self._on_action)
        section.add_widget(self.actions)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Rechercher une date, des vacances, un mois, une année ou un intitulé…"
        )
        self.search.setClearButtonEnabled(True)
        section.add_widget(self.search)

        self.summary = QLabel("")
        self.summary.setProperty("muted", True)
        section.add_widget(self.summary)

        self.source_model = _empty_model(self.HEADERS, self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)
        self.table = _table(self.proxy_model)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        section.add_widget(self.table, 1)

        self.search.textChanged.connect(self._filter)
        root.addWidget(section, 1)

    def _on_action(self, action_id: str) -> None:
        if action_id == "add":
            _open_preview(PresencePreviewDialog, self)

    def _filter(self, text: str) -> None:
        self.proxy_model.setFilterFixedString(text)
        if text:
            self.summary.setText(
                f"{self.proxy_model.rowCount()} présences trouvées pour « {text} »"
            )
        else:
            self.summary.setText("")


class ScenariosPage(QWidget):
    """Page Scénarios individuelle fidèle à ``CTRL_Page_scenarios``."""

    HEADERS = ("Nom du scénario", "Période", "Description")

    def __init__(self, icon_loader: IconLoader, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
        )

        section = TwFormSection("Scénarios")
        self.model = _empty_model(self.HEADERS, self)
        self.table = _table(self.model)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(1, 190)
        section.add_widget(self.table, 1)

        self.actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter", "Ajouter.png", "Ouvrir l'aperçu de création d'un scénario"),
                ActionSpec("edit", "Modifier", "Modifier.png", "Modifier le scénario sélectionné", enabled=False),
                ActionSpec(
                    "delete",
                    "Supprimer",
                    "Supprimer.png",
                    "Supprimer le scénario sélectionné",
                    role="destructive",
                    enabled=False,
                ),
                ActionSpec("duplicate", "Dupliquer", "Dupliquer.png", "Dupliquer le scénario sélectionné", enabled=False),
            ],
            icon_loader=icon_loader,
        )
        self.actions.triggered.connect(self._on_action)
        # Le source wx place les quatre actions sous la liste.
        section.add_widget(self.actions)
        root.addWidget(section, 1)

    def _on_action(self, action_id: str) -> None:
        if action_id == "add":
            _open_preview(ScenarioPreviewDialog, self)


class ExpensesPage(QWidget):
    """Page Frais individuelle fidèle à ``CTRL_Page_frais``.

    Les deux blocs occupent chacun la moitié de la page et conservent les barres
    d'actions au-dessus des listes. Les calculs et rattachements restent hors UI.
    """

    TRIP_HEADERS = (
        "N°",
        "Date",
        "Objet",
        "Trajet",
        "Distance",
        "Tarif",
        "Montant",
        "Remboursement",
    )
    REIMBURSEMENT_HEADERS = ("N°", "Date", "Montant", "Déplacements rattachés")

    def __init__(self, icon_loader: IconLoader, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
        )
        root.setSpacing(TOKENS.spacing.md)

        self.trip_model = _empty_model(self.TRIP_HEADERS, self)
        root.addWidget(self._build_trips(icon_loader), 1)
        self.reimbursement_model = _empty_model(self.REIMBURSEMENT_HEADERS, self)
        root.addWidget(self._build_reimbursements(icon_loader), 1)

    def _build_trips(self, icon_loader: IconLoader) -> TwFormSection:
        section = TwFormSection("Déplacements")
        self.trip_actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter", "Ajouter.png", "Ouvrir l'aperçu de saisie d'un déplacement"),
                ActionSpec("edit", "Modifier", "Modifier.png", "Modifier le déplacement sélectionné", enabled=False),
                ActionSpec(
                    "delete",
                    "Supprimer",
                    "Supprimer.png",
                    "Supprimer le déplacement sélectionné",
                    role="destructive",
                    enabled=False,
                ),
                ActionSpec("print", "Imprimer", "Imprimante.png", "Imprimer une fiche de frais de déplacement", enabled=False),
            ],
            icon_loader=icon_loader,
        )
        self.trip_actions.triggered.connect(self._on_trip_action)
        section.add_widget(self.trip_actions)

        self.trip_table = _table(self.trip_model)
        header = self.trip_table.horizontalHeader()
        for column in range(len(self.TRIP_HEADERS)):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        section.add_widget(self.trip_table, 1)
        return section

    def _build_reimbursements(self, icon_loader: IconLoader) -> TwFormSection:
        section = TwFormSection("Remboursements")
        self.reimbursement_actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter", "Ajouter.png", "Ouvrir l'aperçu de saisie d'un remboursement"),
                ActionSpec("edit", "Modifier", "Modifier.png", "Modifier le remboursement sélectionné", enabled=False),
                ActionSpec(
                    "delete",
                    "Supprimer",
                    "Supprimer.png",
                    "Supprimer le remboursement sélectionné",
                    role="destructive",
                    enabled=False,
                ),
            ],
            icon_loader=icon_loader,
        )
        self.reimbursement_actions.triggered.connect(self._on_reimbursement_action)
        section.add_widget(self.reimbursement_actions)

        self.reimbursement_table = _table(self.reimbursement_model)
        header = self.reimbursement_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        section.add_widget(self.reimbursement_table, 1)
        return section

    def _on_trip_action(self, action_id: str) -> None:
        if action_id == "add":
            _open_preview(TripPreviewDialog, self)

    def _on_reimbursement_action(self, action_id: str) -> None:
        if action_id == "add":
            _open_preview(ReimbursementPreviewDialog, self)


class RecruitmentPage(QWidget):
    """Page Recrutement de la fiche individuelle (`CTRL_Page_candidatures`)."""

    def __init__(self, icon_loader: IconLoader, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
            TOKENS.spacing.sm,
        )
        root.setSpacing(TOKENS.spacing.md)

        self.applications_model = _empty_model(
            (
                "Dépôt",
                "Offre d'emploi",
                "Disponibilités",
                "Fonction(s)",
                "Affectation(s)",
                "Décision",
                "Réponse",
            ),
            self,
        )
        root.addWidget(
            self._build_section("Candidatures", self.applications_model, "application", icon_loader),
            1,
        )

        self.interviews_model = _empty_model(("Date", "Heure", "Avis", "Commentaire"), self)
        root.addWidget(
            self._build_section("Entretiens", self.interviews_model, "interview", icon_loader),
            1,
        )

    def _build_section(
        self,
        title: str,
        model: QStandardItemModel,
        prefix: str,
        icon_loader: IconLoader,
    ) -> TwFormSection:
        section = TwFormSection(title)
        actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter", "Ajouter.png", f"Saisir un nouvel élément {title.lower()}"),
                ActionSpec("edit", "Modifier", "Modifier.png", "Modifier l'élément sélectionné", enabled=False),
                ActionSpec(
                    "delete",
                    "Supprimer",
                    "Supprimer.png",
                    "Supprimer l'élément sélectionné",
                    role="destructive",
                    enabled=False,
                ),
            ],
            icon_loader=icon_loader,
        )
        actions.triggered.connect(
            lambda action_id, kind=prefix: self._on_action(kind, action_id)
        )
        section.add_widget(actions)

        table = _table(model)
        table.setMinimumHeight(
            TOKENS.controls.table_header + TOKENS.controls.table_row_dense * 4
        )
        section.add_widget(table, 1)
        return section

    def _on_action(self, kind: str, action_id: str) -> None:
        if action_id != "add":
            return
        dialog_cls = ApplicationPreviewDialog if kind == "application" else InterviewPreviewDialog
        _open_preview(dialog_cls, self)
