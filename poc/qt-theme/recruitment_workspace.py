from __future__ import annotations

import sys
from collections.abc import Iterable, Sequence

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from recruitment_selection import (
    CandidateSubject,
    JobOfferSubject,
    PersonSubject,
    RecruitmentMode,
    RecruitmentUiState,
)
from ui.common.actions import ActionSpec, TwActionBar
from ui.common.choice_strip import ChoiceSpec, TwChoiceStrip
from ui.common.data_table import TwDataTable


_MODE_TITLES = {
    RecruitmentMode.CANDIDATES: "Candidats",
    RecruitmentMode.APPLICATIONS: "Candidatures",
    RecruitmentMode.INTERVIEWS: "Entretiens",
    RecruitmentMode.JOBS: "Offres d'emploi",
}

_MODE_COLUMNS = {
    RecruitmentMode.CANDIDATES: (
        "Civilité",
        "Nom",
        "Prénom",
        "Âge",
        "Qualifications",
        "Adresse",
        "CP",
        "Ville",
        "Téléphones",
        "Email",
    ),
    RecruitmentMode.APPLICATIONS: (
        "Dépôt",
        "Nom",
        "Offre d'emploi",
        "Disponibilités",
        "Fonction(s)",
        "Affectation(s)",
        "Décision",
        "Réponse",
    ),
    RecruitmentMode.INTERVIEWS: (
        "Date",
        "Heure",
        "Nom",
        "Avis",
        "Commentaire",
    ),
    RecruitmentMode.JOBS: (
        "Lancement",
        "Clôture",
        "Intitulé",
        "Candidatures",
        "Détail",
    ),
}


class RecruitmentSummaryPanel(QFrame):
    """Résumé typé de la sélection, sans lecture métier ni persistance."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(6)

        title = QLabel("Détail de la sélection")
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        root.addWidget(title)

        self.tabs = QTabWidget(self)
        self.identity_page = self._placeholder("Identité candidat / personne · lecture non raccordée")
        self.applications_page = self._placeholder("Candidatures liées · lecture non raccordée")
        self.interviews_page = self._placeholder("Entretiens liés · lecture non raccordée")
        root.addWidget(self.tabs, 1)
        self.clear()

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("muted", True)
        label.setWordWrap(True)
        layout.addWidget(label, 1)
        return page

    def _remove_all_tabs(self) -> None:
        while self.tabs.count():
            self.tabs.removeTab(0)

    def clear(self) -> None:
        self._remove_all_tabs()
        self.setVisible(False)

    def set_subject(self, subject) -> None:
        self._remove_all_tabs()
        if isinstance(subject, (CandidateSubject, PersonSubject)):
            self.tabs.addTab(self.identity_page, "Identité")
            self.tabs.addTab(self.applications_page, "Candidatures")
            self.tabs.addTab(self.interviews_page, "Entretiens")
        elif isinstance(subject, JobOfferSubject):
            self.tabs.addTab(self.applications_page, "Candidatures")
        else:
            self.clear()
            return
        self.setVisible(True)


class RecruitmentWorkspace(QMainWindow):
    """Transposition Qt, lecture seule, de l'espace global Recrutement wxPython."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = RecruitmentUiState()
        self.setWindowTitle("Teamworks Qt — Recrutement")
        self.resize(1440, 900)
        self.setMinimumSize(1040, 680)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        heading = QLabel("Recrutement")
        font = heading.font()
        font.setPointSize(16)
        font.setBold(True)
        heading.setFont(font)
        root.addWidget(heading)

        subtitle = QLabel("Transposition Qt de l’espace global historique Teamworks · lecture seule")
        subtitle.setProperty("muted", True)
        root.addWidget(subtitle)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)
        left = self._build_tracking_column()
        right = self._build_main_content()
        left.setMinimumWidth(230)
        right.setMinimumWidth(620)
        self.splitter.addWidget(left)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 8)
        self.splitter.setSizes([330, 1090])
        root.addWidget(self.splitter, 1)

        self.setCentralWidget(central)
        self._apply_mode(self.state.mode)
        self.statusBar().showMessage("Lecture seule · données Recrutement non raccordées dans ce POC")

    def _build_tracking_column(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("panel")
        root = QVBoxLayout(frame)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        interviews_group = QGroupBox("Prochains entretiens", frame)
        interviews_layout = QVBoxLayout(interviews_group)
        self.upcoming_interviews = QListWidget(interviews_group)
        self.upcoming_interviews.setEnabled(False)
        interviews_layout.addWidget(self.upcoming_interviews, 1)
        interviews_note = QLabel("Lecture non raccordée dans le POC")
        interviews_note.setProperty("muted", True)
        interviews_layout.addWidget(interviews_note)
        root.addWidget(interviews_group, 1)

        pending_group = QGroupBox("À traiter", frame)
        pending_layout = QVBoxLayout(pending_group)
        description = QLabel("Entretiens sans avis et candidatures en attente de réponse.")
        description.setWordWrap(True)
        description.setProperty("muted", True)
        pending_layout.addWidget(description)
        self.pending_items = QListWidget(pending_group)
        self.pending_items.setEnabled(False)
        pending_layout.addWidget(self.pending_items, 1)
        pending_note = QLabel("Lecture non raccordée dans le POC")
        pending_note.setProperty("muted", True)
        pending_layout.addWidget(pending_note)
        root.addWidget(pending_group, 2)
        return frame

    def _build_main_content(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("panel")
        root = QVBoxLayout(frame)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(8)

        self.list_title = QLabel("Candidats")
        title_font = self.list_title.font()
        title_font.setPointSize(13)
        title_font.setBold(True)
        self.list_title.setFont(title_font)
        root.addWidget(self.list_title)

        self.mode_strip = TwChoiceStrip(
            [
                ChoiceSpec(RecruitmentMode.CANDIDATES.value, "Candidats"),
                ChoiceSpec(RecruitmentMode.APPLICATIONS.value, "Candidatures"),
                ChoiceSpec(RecruitmentMode.INTERVIEWS.value, "Entretiens"),
                ChoiceSpec(RecruitmentMode.JOBS.value, "Offres d'emploi"),
            ],
            frame,
        )
        self.mode_strip.valueChanged.connect(self._on_mode_changed)
        root.addWidget(self.mode_strip)

        self.tables_stack = QStackedWidget(frame)
        self.models: dict[RecruitmentMode, QStandardItemModel] = {}
        self.tables: dict[RecruitmentMode, TwDataTable] = {}
        self.proxies: dict[RecruitmentMode, QSortFilterProxyModel] = {}

        for mode in RecruitmentMode:
            model = QStandardItemModel(0, len(_MODE_COLUMNS[mode]), self)
            model.setHorizontalHeaderLabels(list(_MODE_COLUMNS[mode]))
            table_model = model
            if mode is RecruitmentMode.CANDIDATES:
                proxy = QSortFilterProxyModel(self)
                proxy.setSourceModel(model)
                proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                proxy.setFilterKeyColumn(-1)
                self.proxies[mode] = proxy
                table_model = proxy
            table = TwDataTable(frame, model=table_model)
            table.selectionKeyChanged.connect(
                lambda key, current_mode=mode: self._on_selection_changed(current_mode, key)
            )
            self.models[mode] = model
            self.tables[mode] = table
            self.tables_stack.addWidget(table)
        root.addWidget(self.tables_stack, 3)

        self.search_frame = QFrame(frame)
        self.search_frame.setObjectName("commandBar")
        search_layout = QHBoxLayout(self.search_frame)
        search_layout.setContentsMargins(6, 4, 6, 4)
        self.search = QLineEdit(self.search_frame)
        self.search.setPlaceholderText("Rechercher un candidat")
        self.search.setClearButtonEnabled(True)
        self.search.setToolTip(
            "Saisissez un nom, un prénom, une ville ou un autre élément de la fiche candidat."
        )
        self.search.textChanged.connect(self._on_candidate_search)
        search_layout.addWidget(self.search, 1)
        root.addWidget(self.search_frame)

        self.actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter", enabled=False),
                ActionSpec("edit", "Modifier", enabled=False),
                ActionSpec("delete", "Supprimer", enabled=False),
                ActionSpec("filters", "Filtres", enabled=False),
                ActionSpec("show_all", "Tout afficher", enabled=True),
                ActionSpec("columns", "Colonnes", enabled=False),
                ActionSpec("mail", "Courrier", enabled=False),
                ActionSpec("print", "Imprimer", enabled=False),
                ActionSpec("export_text", "Export texte", enabled=False),
                ActionSpec("export_excel", "Export Excel", enabled=False),
                ActionSpec("help", "Aide", enabled=False),
            ],
            frame,
        )
        self.actions.triggered.connect(self._on_action)
        root.addWidget(self.actions)

        self.summary = RecruitmentSummaryPanel(frame)
        root.addWidget(self.summary, 2)
        return frame

    def _on_mode_changed(self, value: object) -> None:
        try:
            mode = RecruitmentMode(str(value))
        except ValueError:
            return
        self.state.change_mode(mode)
        self._apply_mode(mode)

    def _apply_mode(self, mode: RecruitmentMode) -> None:
        self.mode_strip.set_value(mode.value)
        self.list_title.setText(_MODE_TITLES[mode])
        self.tables_stack.setCurrentWidget(self.tables[mode])
        self.search_frame.setVisible(mode is RecruitmentMode.CANDIDATES)
        self.actions.set_visible(
            "mail",
            mode in (RecruitmentMode.CANDIDATES, RecruitmentMode.APPLICATIONS),
        )
        for table in self.tables.values():
            table.clearSelection()
        self.actions.set_enabled("edit", False)
        self.actions.set_enabled("delete", False)
        self.summary.clear()
        self.statusBar().showMessage(
            f"Lecture seule · {_MODE_TITLES[mode]} · données non raccordées dans ce POC"
        )

    def _on_candidate_search(self, text: str) -> None:
        proxy = self.proxies.get(RecruitmentMode.CANDIDATES)
        if proxy is not None:
            proxy.setFilterFixedString(text)

    def _on_action(self, action_id: str) -> None:
        if action_id == "show_all":
            if self.state.mode is RecruitmentMode.CANDIDATES:
                self.search.clear()
            self.tables[self.state.mode].clearSelection()

    def _on_selection_changed(self, mode: RecruitmentMode, key: object) -> None:
        if mode is not self.state.mode or key is None or not hasattr(key, "mode"):
            self._clear_selection()
            return
        try:
            self.state.set_selection(key)
        except (TypeError, ValueError):
            self._clear_selection()
            return
        self.actions.set_enabled("edit", True)
        self.actions.set_enabled("delete", True)
        self.summary.set_subject(key.subject)

    def _clear_selection(self) -> None:
        self.state.clear_selection()
        self.actions.set_enabled("edit", False)
        self.actions.set_enabled("delete", False)
        self.summary.clear()

    def set_rows(
        self,
        mode: RecruitmentMode,
        rows: Iterable[tuple[object, Sequence[object]]],
    ) -> None:
        """Point d'injection futur : aucune lecture SQL n'est autorisée dans le widget."""

        model = self.models[mode]
        model.removeRows(0, model.rowCount())
        expected = len(_MODE_COLUMNS[mode])
        for selection, values in rows:
            if not hasattr(selection, "mode") or selection.mode is not mode:
                raise ValueError("selection incompatible avec le mode Recrutement")
            cells = [QStandardItem("" if value is None else str(value)) for value in values[:expected]]
            while len(cells) < expected:
                cells.append(QStandardItem(""))
            if cells:
                cells[0].setData(selection, Qt.ItemDataRole.UserRole)
            model.appendRow(cells)


def main() -> int:
    app = QApplication.instance()
    owns_app = app is None
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("Teamworks Qt POC")
        app.setOrganizationName("Pêle-Mêle Sports et Loisirs")

    from theme_engine import ThemeEngine

    theme_engine = ThemeEngine(app)
    theme_engine.apply(dark=False)
    window = RecruitmentWorkspace()
    window.show()
    window.raise_()
    window.activateWindow()

    if owns_app:
        return int(app.exec())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
