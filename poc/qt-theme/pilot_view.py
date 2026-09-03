from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QSize, QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from contract_editor import ContractComplianceDialog
from data_adapter import TeamworksReadAdapter
from models import ContractsTableModel, PeopleTableModel


_REPO_ROOT = Path(__file__).resolve().parents[2]
_LEGACY_ICONS = _REPO_ROOT / "teamworks" / "Static" / "Images" / "16x16"


def _initials(name: str) -> str:
    parts = [part for part in (name or "").replace("-", " ").split() if part]
    return "".join(part[0].upper() for part in parts[:2]) or "—"


def _contract_count_text(count: int) -> str:
    if count == 0:
        return "Aucun contrat enregistré"
    if count == 1:
        return "1 contrat enregistré"
    return f"{count} contrats enregistrés"


def _legacy_icon(name: str) -> QIcon:
    path = _LEGACY_ICONS / name
    return QIcon(str(path)) if path.exists() else QIcon()


class ReadValue(QLabel):
    def __init__(self, text: str = "—"):
        super().__init__(text or "—")
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setWordWrap(True)
        self.setProperty("readValue", True)


class PeopleContractsPilot(QMainWindow):
    def __init__(self, adapter: TeamworksReadAdapter, parent=None):
        super().__init__(parent)
        self.adapter = adapter
        self.setWindowTitle("Teamworks Qt — Individus / Contrats")
        self.resize(1380, 860)
        self.setMinimumSize(900, 620)

        people_load_started = time.perf_counter()
        initial_people = adapter.list_people()
        self.initial_people_load_seconds = time.perf_counter() - people_load_started

        self.people_model = PeopleTableModel(initial_people, self)
        self.people_proxy = QSortFilterProxyModel(self)
        self.people_proxy.setSourceModel(self.people_model)
        self.people_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.people_proxy.setFilterKeyColumn(-1)
        self.people_proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.contracts_model = ContractsTableModel(parent=self)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        heading = QLabel("Individus / Contrats")
        font = heading.font()
        font.setPointSize(16)
        font.setBold(True)
        heading.setFont(font)
        root.addWidget(heading)

        subheading = QLabel("Transposition Qt de l’organisation historique Teamworks · lecture seule")
        subheading.setProperty("muted", True)
        root.addWidget(subheading)

        people_panel = self._build_people_panel()
        detail_panel = self._build_detail_panel()
        people_panel.setMinimumWidth(390)
        detail_panel.setMinimumWidth(460)
        people_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        detail_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(people_panel)
        self.splitter.addWidget(detail_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.setSizes([500, 820])
        root.addWidget(self.splitter, 1)

        self.setCentralWidget(central)
        self._show_empty_detail()

    def _people_count_text(self) -> str:
        total = self.people_model.rowCount()
        visible = self.people_proxy.rowCount()
        if visible != total:
            return f"{visible} / {total} personnes"
        return f"{total} personne" if total == 1 else f"{total} personnes"

    def _on_search_changed(self, text: str) -> None:
        self.people_proxy.setFilterFixedString(text)
        self.people_count.setText(self._people_count_text())

    def _clear_people_filter(self) -> None:
        self.search.clear()
        self.people_table.setFocus()

    def _legacy_tool_button(
        self,
        icon_name: str,
        tooltip: str,
        *,
        enabled: bool = False,
        fallback: str = "·",
    ) -> QToolButton:
        button = QToolButton()
        button.setObjectName("legacyToolButton")
        button.setToolTip(tooltip)
        button.setIcon(_legacy_icon(icon_name))
        button.setIconSize(QSize(16, 16))
        button.setFixedSize(30, 30)
        if button.icon().isNull():
            button.setText(fallback)
        button.setEnabled(enabled)
        return button

    def _build_people_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        label = QLabel("Liste des individus")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        title_row.addWidget(label)
        title_row.addStretch(1)
        self.people_count = QLabel(self._people_count_text())
        self.people_count.setProperty("muted", True)
        title_row.addWidget(self.people_count)
        layout.addLayout(title_row)

        list_row = QHBoxLayout()
        list_row.setSpacing(6)

        list_column = QVBoxLayout()
        list_column.setSpacing(5)

        self.people_table = QTableView()
        self.people_table.setModel(self.people_proxy)
        self.people_table.setSortingEnabled(True)
        self.people_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.people_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.people_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.people_table.setAlternatingRowColors(True)
        self.people_table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.people_table.setWordWrap(False)
        self.people_table.verticalHeader().setVisible(False)
        self.people_table.verticalHeader().setDefaultSectionSize(24)
        self.people_table.verticalHeader().setMinimumSectionSize(22)
        header = self.people_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 82)
        header.resizeSection(2, 112)
        header.resizeSection(3, 104)
        header.resizeSection(4, 84)
        header.resizeSection(5, 64)
        header.resizeSection(6, 86)
        header.resizeSection(7, 100)
        self.people_table.selectionModel().selectionChanged.connect(self._on_person_selection)
        list_column.addWidget(self.people_table, 1)

        search_bar = QFrame()
        search_bar.setObjectName("commandBar")
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(6, 4, 6, 4)
        search_layout.setSpacing(6)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Nom, prénom, ville, statut…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search, 1)
        list_column.addWidget(search_bar)
        list_row.addLayout(list_column, 1)

        tools = QVBoxLayout()
        tools.setSpacing(5)
        add_button = self._legacy_tool_button("Ajouter.png", "Créer une nouvelle fiche individuelle", fallback="+")
        edit_button = self._legacy_tool_button("Modifier.png", "Modifier la fiche sélectionnée", fallback="M")
        delete_button = self._legacy_tool_button("Supprimer.png", "Supprimer la fiche sélectionnée", fallback="−")
        tools.addWidget(add_button)
        tools.addWidget(edit_button)
        tools.addWidget(delete_button)
        tools.addSpacing(10)

        period_button = self._legacy_tool_button("Calendrier3jours.png", "Rechercher les personnes présentes sur une période", fallback="P")
        show_all_button = self._legacy_tool_button("Actualiser.png", "Réafficher toute la liste", enabled=True, fallback="R")
        show_all_button.clicked.connect(self._clear_people_filter)
        options_button = self._legacy_tool_button("Mecanisme.png", "Options de la liste", fallback="O")
        tools.addWidget(period_button)
        tools.addWidget(show_all_button)
        tools.addWidget(options_button)
        tools.addSpacing(10)

        mail_button = self._legacy_tool_button("Mail.png", "Courrier ou publipostage", fallback="@")
        print_button = self._legacy_tool_button("Imprimante.png", "Imprimer la liste", fallback="I")
        export_button = self._legacy_tool_button("Excel.png", "Exporter la liste", fallback="X")
        help_button = self._legacy_tool_button("Aide.png", "Aide", fallback="?")
        tools.addWidget(mail_button)
        tools.addWidget(print_button)
        tools.addWidget(export_button)
        tools.addSpacing(10)
        tools.addWidget(help_button)
        tools.addStretch(1)
        list_row.addLayout(tools)

        layout.addLayout(list_row, 1)
        return frame

    def _build_detail_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.detail_stack = QStackedWidget()
        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_message = QLabel("Sélectionnez une personne pour afficher sa fiche individuelle")
        empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_message, 1)

        detail_page = QWidget()
        detail_layout = QVBoxLayout(detail_page)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(6)

        person_summary = QFrame()
        person_summary.setObjectName("personSummary")
        summary_layout = QHBoxLayout(person_summary)
        summary_layout.setContentsMargins(10, 8, 10, 8)
        summary_layout.setSpacing(12)

        summary_text = QWidget()
        summary_text_layout = QVBoxLayout(summary_text)
        summary_text_layout.setContentsMargins(0, 0, 0, 0)
        summary_text_layout.setSpacing(2)

        self.detail_id = QLabel("ID personne : —")
        self.detail_id.setProperty("muted", True)
        summary_text_layout.addWidget(self.detail_id)

        header_separator = QFrame()
        header_separator.setFrameShape(QFrame.Shape.HLine)
        header_separator.setProperty("separator", True)
        summary_text_layout.addWidget(header_separator)

        self.detail_title = QLabel("Fiche individuelle")
        self.detail_title.setObjectName("personSummaryName")
        title_font = self.detail_title.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.detail_title.setFont(title_font)
        summary_text_layout.addWidget(self.detail_title)

        self.detail_context = QLabel("Fonction / site : —")
        self.detail_context.setProperty("muted", True)
        self.detail_context.setWordWrap(True)
        summary_text_layout.addWidget(self.detail_context)

        self.detail_birth = QLabel("Naissance : —")
        self.detail_birth.setProperty("muted", True)
        summary_text_layout.addWidget(self.detail_birth)

        self.detail_contracts = QLabel("Aucun contrat enregistré")
        self.detail_contracts.setProperty("muted", True)
        summary_text_layout.addWidget(self.detail_contracts)
        summary_text_layout.addStretch(1)
        summary_layout.addWidget(summary_text, 1)

        self.person_avatar = QLabel("—")
        self.person_avatar.setObjectName("personAvatar")
        self.person_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.person_avatar.setFixedSize(96, 96)
        summary_layout.addWidget(self.person_avatar, 0, Qt.AlignmentFlag.AlignTop)
        detail_layout.addWidget(person_summary)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        self.tabs.addTab(self._build_general_tab(), _legacy_icon("Identite.png"), "Généralités")
        self.tabs.addTab(self._build_placeholder_tab("Questionnaire"), _legacy_icon("Document2.png"), "Questionnaire")
        self.tabs.addTab(self._build_placeholder_tab("Qualifications"), _legacy_icon("BlocNotes.png"), "Qualifications")
        self.tabs.addTab(self._build_contracts_tab(), _legacy_icon("Document.png"), "Contrats")
        self.tabs.addTab(self._build_placeholder_tab("Présences"), _legacy_icon("Presences.png"), "Présences")
        self.tabs.addTab(self._build_placeholder_tab("Scénarios"), _legacy_icon("Scenario.png"), "Scénarios")
        self.tabs.addTab(self._build_placeholder_tab("Frais"), _legacy_icon("Calculatrice.png"), "Frais")
        self.tabs.addTab(self._build_placeholder_tab("Recrutement"), _legacy_icon("Candidature.png"), "Recrutement")
        detail_layout.addWidget(self.tabs, 1)

        footer = QHBoxLayout()
        footer_help = QPushButton("Aide")
        footer_help.setEnabled(False)
        footer.addWidget(footer_help)
        footer.addStretch(1)
        footer_close = QPushButton("Fermer")
        footer_close.clicked.connect(self.close)
        footer.addWidget(footer_close)
        detail_layout.addLayout(footer)

        self.detail_stack.addWidget(empty_page)
        self.detail_stack.addWidget(detail_page)
        layout.addWidget(self.detail_stack, 1)
        return frame

    def _build_placeholder_tab(self, label: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        message = QLabel(f"{label} · transposition à venir")
        message.setProperty("muted", True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message, 1)
        return page

    def _build_general_tab(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(8)

        self.value_id = ReadValue()
        self.value_name = ReadValue()
        self.value_birth_date = ReadValue()
        self.value_role = ReadValue()
        self.value_classification = ReadValue()
        self.value_contract = ReadValue()
        self.value_hours = ReadValue()
        self.value_status = ReadValue()
        self.value_site = ReadValue()
        self.value_medical = ReadValue()
        self.value_mutual = ReadValue()

        content_layout.addWidget(self._build_compact_section("Identité", (
            ("Matricule", self.value_id, "Nom", self.value_name),
            ("Naissance", self.value_birth_date, "Site", self.value_site),
        )))
        content_layout.addWidget(self._build_compact_section("Situation professionnelle", (
            ("Fonction", self.value_role, "Classification", self.value_classification),
            ("Contrat", self.value_contract, "Temps", self.value_hours),
            ("Statut", self.value_status, "", ReadValue("")),
        )))
        content_layout.addWidget(self._build_compact_section("Suivi RH", (
            ("Suivi médical", self.value_medical, "Mutuelle", self.value_mutual),
        ), with_separator=False))
        content_layout.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll, 1)
        return page

    def _build_compact_section(self, title, rows, *, with_separator=True) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        heading = QLabel(title)
        font = heading.font()
        font.setBold(True)
        heading.setFont(font)
        layout.addWidget(heading)
        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        for row, (la, va, lb, vb) in enumerate(rows):
            grid.addWidget(QLabel(la), row, 0)
            grid.addWidget(va, row, 1)
            grid.addWidget(QLabel(lb), row, 2)
            grid.addWidget(vb, row, 3)
        layout.addWidget(host)
        if with_separator:
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setLineWidth(1)
            separator.setProperty("separator", True)
            layout.addWidget(separator)
        return section

    def _build_contracts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        command_bar = QFrame()
        command_bar.setObjectName("commandBar")
        command_layout = QHBoxLayout(command_bar)
        command_layout.setContentsMargins(8, 6, 8, 6)
        simulate_button = QPushButton("Simuler un contrat")
        simulate_button.clicked.connect(self._open_contract_compliance_dialog)
        command_layout.addWidget(simulate_button)
        command_layout.addStretch(1)
        readonly = QLabel("POC · aucune écriture")
        readonly.setProperty("muted", True)
        command_layout.addWidget(readonly)
        layout.addWidget(command_bar)

        self.contracts_stack = QStackedWidget()
        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_message = QLabel("Aucun contrat enregistré pour cette personne")
        empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_message, 1)
        self.contracts_table = QTableView()
        self.contracts_table.setModel(self.contracts_model)
        self.contracts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.contracts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.contracts_table.setAlternatingRowColors(True)
        self.contracts_table.verticalHeader().setVisible(False)
        header = self.contracts_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.contracts_stack.addWidget(empty_page)
        self.contracts_stack.addWidget(self.contracts_table)
        self.contracts_stack.setCurrentIndex(0)
        layout.addWidget(self.contracts_stack, 1)
        return widget

    def _open_contract_compliance_dialog(self) -> None:
        dialog = ContractComplianceDialog(self)
        dialog.exec()

    def _show_empty_detail(self) -> None:
        self.detail_stack.setCurrentIndex(0)
        self.contracts_model.replace([])
        self.contracts_stack.setCurrentIndex(0)
        self.statusBar().showMessage("Lecture seule · aucune sélection")

    def _on_person_selection(self, *_args) -> None:
        rows = self.people_table.selectionModel().selectedRows()
        if not rows:
            self._show_empty_detail()
            return
        self._show_person_from_proxy_row(rows[0].row())

    def _show_person_from_proxy_row(self, proxy_row: int) -> None:
        source_index = self.people_proxy.mapToSource(self.people_proxy.index(proxy_row, 0))
        person = self.people_model.person_at(source_index.row())
        if person is None:
            self._show_empty_detail()
            return
        for widget, value in (
            (self.value_id, person.id),
            (self.value_name, person.name),
            (self.value_birth_date, person.birth_date),
            (self.value_role, person.role),
            (self.value_classification, person.classification),
            (self.value_contract, person.contract),
            (self.value_hours, person.weekly_hours),
            (self.value_status, person.status),
            (self.value_site, person.site),
            (self.value_medical, person.medical),
            (self.value_mutual, person.mutual),
        ):
            widget.setText(value or "—")

        contract_key = person.id_historique if person.id_historique is not None else person.id
        self.contracts_model.replace(self.adapter.list_contracts(contract_key))
        contract_count = self.contracts_model.rowCount()
        self.contracts_stack.setCurrentIndex(1 if contract_count else 0)

        historical_id = person.id_historique if person.id_historique is not None else person.id
        self.detail_id.setText(f"ID personne : {historical_id}")
        self.detail_title.setText(person.name or "—")
        context_parts = [value for value in (person.role, person.site) if value and value != "—"]
        self.detail_context.setText(" · ".join(context_parts) if context_parts else "Fonction / site : —")
        self.detail_birth.setText(f"Naissance : {person.birth_date or '—'}")
        self.detail_contracts.setText(_contract_count_text(contract_count))
        self.person_avatar.setText(_initials(person.name))
        self.detail_stack.setCurrentIndex(1)
        self.statusBar().showMessage(f"Lecture seule · {person.name} · {contract_count} contrat(s)")
