from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView, QWidget

from .tokens import TOKENS


class TwDataTable(QTableView):
    """Tableau dense commun. Les clés peuvent être exposées via UserRole."""

    selectionKeyChanged = Signal(object)
    activatedKey = Signal(object)

    def __init__(self, parent: QWidget | None = None, *, model=None) -> None:
        super().__init__(parent)
        self.setObjectName("twDataTable")
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(TOKENS.controls.table_row_dense)
        self.verticalHeader().setMinimumSectionSize(TOKENS.controls.table_row_dense)
        self.horizontalHeader().setMinimumHeight(TOKENS.controls.table_header)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.activated.connect(self._emit_activated)
        if model is not None:
            self.set_model(model)

    def set_model(self, model) -> None:
        self.setModel(model)
        selection_model = self.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._emit_selection)

    def selected_key(self):
        model = self.model()
        selection = self.selectionModel()
        if model is None or selection is None:
            return None
        rows = selection.selectedRows()
        if not rows:
            return None
        index = rows[0]
        key = index.data(Qt.ItemDataRole.UserRole)
        return key if key is not None else index.row()

    def select_key(self, key) -> bool:
        model = self.model()
        if model is None:
            return False
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            candidate = index.data(Qt.ItemDataRole.UserRole)
            if candidate == key:
                self.selectRow(row)
                self.scrollTo(index)
                return True
        return False

    def _key_for_index(self, index: QModelIndex):
        key = index.data(Qt.ItemDataRole.UserRole)
        return key if key is not None else index.row()

    def _emit_selection(self, *_args) -> None:
        self.selectionKeyChanged.emit(self.selected_key())

    def _emit_activated(self, index: QModelIndex) -> None:
        self.activatedKey.emit(self._key_for_index(index))
