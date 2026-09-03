from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon, QStandardItemModel
from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QLabel, QLineEdit, QVBoxLayout, QWidget

from legacy_sheets import (
    ApplicationPreviewDialog,
    InterviewPreviewDialog,
    PiecePreviewDialog,
    PresencePreviewDialog,
)
from ui.common import ActionSpec, TOKENS, TwActionBar, TwDataTable, TwFormSection


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


class QuestionnairePage(QWidget):
    """Questionnaire historique : questions à gauche, réponses à droite."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm)

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
    """Transposition de ``CTRL_Page_qualifications`` sans persistance.

    La structure suit le source courant : Pièces à fournir et Qualifications en
    deux colonnes, puis Pièces reçues en dessous. Les actions sont placées sous
    les listes comme dans wx ; seule l'ouverture des aperçus locaux est active.
    """

    def __init__(self, icon_loader: IconLoader, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icon_loader = icon_loader

        root = QVBoxLayout(self)
        root.setContentsMargins(TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm)
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
                    "Modifier la liste des qualifications",
                    enabled=False,
                )
            ],
            icon_loader=icon_loader,
        )
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
                ActionSpec("edit", "Modifier", "Modifier.png", "Modifier la pièce sélectionnée", enabled=False),
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

    def _on_received_action(self, action_id: str) -> None:
        if action_id == "add":
            _open_preview(PiecePreviewDialog, self)


class PresencesPage(QWidget):
    """Transposition de ``CTRL_Page_presences`` sans lecture/écriture métier.

    Le source place la barre d'actions avant la recherche, le résumé puis la
    liste. Cette géométrie est conservée ; la recherche filtre seulement le
    modèle Qt local lorsqu'il contient des lignes.
    """

    HEADERS = ("Date", "Vacances", "Horaires", "Durée", "Intitulé")

    def __init__(self, icon_loader: IconLoader, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm)

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


class RecruitmentPage(QWidget):
    """Page Recrutement de la fiche individuelle (`CTRL_Page_candidatures`)."""

    def __init__(self, icon_loader: IconLoader, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm)
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
        applications = self._build_section(
            "Candidatures",
            self.applications_model,
            "application",
            icon_loader,
        )
        root.addWidget(applications, 1)

        self.interviews_model = _empty_model(("Date", "Heure", "Avis", "Commentaire"), self)
        interviews = self._build_section(
            "Entretiens",
            self.interviews_model,
            "interview",
            icon_loader,
        )
        root.addWidget(interviews, 1)

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
        actions.triggered.connect(lambda action_id, kind=prefix: self._on_action(kind, action_id))
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
