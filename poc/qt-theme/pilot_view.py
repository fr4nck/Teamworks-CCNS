from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QFrame,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from data_adapter import TeamworksReadAdapter
from models import ContractsTableModel, PeopleTableModel


class ReadValue(QLabel):
    """Valeur de consultation légère, volontairement non éditable."""

    def __init__(self, text: str = "—"):
        super().__init__(text or "—")
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setWordWrap(True)
        self.setProperty("readValue", True)


class PeopleContractsPilot(QMainWindow):
    """Écran témoin Individus/Contrats, strictement lecture seule."""

    def __init__(self, adapter: TeamworksReadAdapter, parent=None):
        super().__init__(parent)
        self.adapter = adapter
        self.setWindowTitle("Teamworks Qt — Individus / Contrats")
        self.resize(1380, 860)
        self.setMinimumSize(900, 620)

        self.people_model = PeopleTableModel(adapter.list_people(), self)
        self.people_proxy = QSortFilterProxyModel(self)
        self.people_proxy.setSourceModel(self.people_model)
        self.people_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.people_proxy.setFilterKeyColumn(-1)
        self.people_proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.contracts_model = ContractsTableModel(parent=self)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        heading = QLabel("Individus / Contrats")
        font = heading.font()
        font.setPointSize(18)
        font.setBold(True)
        heading.setFont(font)
        root.addWidget(heading)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un salarié, un site, un statut…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.people_proxy.setFilterFixedString)
        root.addWidget(self.search)

        people_panel = self._build_people_panel()
        detail_panel = self._build_detail_panel()
        people_panel.setMinimumWidth(380)
        detail_panel.setMinimumWidth(440)
        people_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        detail_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(people_panel)
        self.splitter.addWidget(detail_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.setSizes([480, 800])
        root.addWidget(self.splitter, 1)

        self.setCentralWidget(central)
        self._select_first_row()

    def _build_people_panel(self) -> QWidget:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel("Salariés")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label)

        self.people_table = QTableView()
        self.people_table.setModel(self.people_proxy)
        self.people_table.setSortingEnabled(True)
        self.people_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.people_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.people_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.people_table.setAlternatingRowColors(True)
        self.people_table.verticalHeader().setVisible(False)
        header = self.people_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 95)
        header.resizeSection(2, 130)
        header.resizeSection(3, 120)
        header.resizeSection(4, 95)
        header.resizeSection(5, 75)
        header.resizeSection(6, 95)
        header.resizeSection(7, 130)
        self.people_table.selectionModel().selectionChanged.connect(self._on_person_selection)
        layout.addWidget(self.people_table, 1)
        return frame

    def _build_detail_panel(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tabs.addTab(self._build_general_tab(), "Généralités")
        tabs.addTab(self._build_contracts_tab(), "Contrats")
        return tabs

    def _build_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(12)

        self.value_id = ReadValue()
        self.value_name = ReadValue()
        self.value_role = ReadValue()
        self.value_classification = ReadValue()
        self.value_contract = ReadValue()
        self.value_hours = ReadValue()
        self.value_status = ReadValue()
        self.value_site = ReadValue()
        self.value_medical = ReadValue()
        self.value_mutual = ReadValue()

        layout.addRow("Matricule", self.value_id)
        layout.addRow("Nom", self.value_name)
        layout.addRow("Fonction", self.value_role)
        layout.addRow("Classification", self.value_classification)
        layout.addRow("Contrat", self.value_contract)
        layout.addRow("Temps", self.value_hours)
        layout.addRow("Statut", self.value_status)
        layout.addRow("Site", self.value_site)
        layout.addRow("Suivi médical", self.value_medical)
        layout.addRow("Mutuelle", self.value_mutual)
        return widget

    def _build_contracts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        self.contracts_table = QTableView()
        self.contracts_table.setModel(self.contracts_model)
        self.contracts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.contracts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.contracts_table.setAlternatingRowColors(True)
        self.contracts_table.verticalHeader().setVisible(False)
        header = self.contracts_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 100)
        header.resizeSection(1, 95)
        header.resizeSection(2, 95)
        header.resizeSection(4, 90)
        header.resizeSection(5, 110)
        layout.addWidget(self.contracts_table)
        return widget

    def _select_first_row(self) -> None:
        if self.people_proxy.rowCount() > 0:
            self.people_table.selectRow(0)
            self._show_person_from_proxy_row(0)

    def _on_person_selection(self, *_args) -> None:
        indexes = self.people_table.selectionModel().selectedRows()
        if indexes:
            self._show_person_from_proxy_row(indexes[0].row())

    def _show_person_from_proxy_row(self, proxy_row: int) -> None:
        proxy_index = self.people_proxy.index(proxy_row, 0)
        source_index = self.people_proxy.mapToSource(proxy_index)
        person = self.people_model.person_at(source_index.row())
        if person is None:
            return

        values = (
            (self.value_id, person.id),
            (self.value_name, person.name),
            (self.value_role, person.role),
            (self.value_classification, person.classification),
            (self.value_contract, person.contract),
            (self.value_hours, person.weekly_hours),
            (self.value_status, person.status),
            (self.value_site, person.site),
            (self.value_medical, person.medical),
            (self.value_mutual, person.mutual),
        )
        for widget, value in values:
            widget.setText(value or "—")

        self.contracts_model.replace(self.adapter.list_contracts(person.id))
        self.statusBar().showMessage(
            f"Lecture seule · {person.name} · {self.contracts_model.rowCount()} contrat(s)"
        )
