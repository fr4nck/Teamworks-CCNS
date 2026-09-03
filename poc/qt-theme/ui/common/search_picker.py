from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QVBoxLayout, QWidget

from .actions import ActionSpec, TwActionBar
from .data_table import TwDataTable
from .tokens import TOKENS


@dataclass(frozen=True)
class SearchModeSpec:
    id: str
    label: str


class TwSearchPicker(QWidget):
    """Patron commun rechercher -> résultats -> choisir."""

    searchRequested = Signal(str, object)
    showAllRequested = Signal()
    selectionAccepted = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        model=None,
        modes: tuple[SearchModeSpec, ...] | list[SearchModeSpec] = (),
        icon_loader=None,
        placeholder: str = "Rechercher…",
    ) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(TOKENS.spacing.sm)

        row = QHBoxLayout()
        row.setSpacing(TOKENS.spacing.sm)
        self.search = QLineEdit()
        self.search.setPlaceholderText(placeholder)
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(TOKENS.controls.height_search)
        self.search.returnPressed.connect(self._request_search)
        row.addWidget(self.search, 1)

        self.mode = QComboBox()
        for spec in modes:
            self.mode.addItem(spec.label, spec.id)
        self.mode.setVisible(bool(modes))
        self.mode.setMinimumHeight(TOKENS.controls.height_standard)
        row.addWidget(self.mode)

        self.actions = TwActionBar(
            [
                ActionSpec("search", "Rechercher", "Rechercher.png"),
                ActionSpec("show_all", "Afficher tout", "Actualiser.png"),
            ],
            icon_loader=icon_loader,
        )
        self.actions.triggered.connect(self._on_action)
        row.addWidget(self.actions)
        root.addLayout(row)

        self.table = TwDataTable(model=model)
        self.table.activatedKey.connect(self.selectionAccepted)
        root.addWidget(self.table, 1)

    def set_results_model(self, model) -> None:
        self.table.set_model(model)

    def query(self) -> str:
        return self.search.text().strip()

    def search_mode(self):
        return self.mode.currentData() if self.mode.isVisible() else None

    def selected_key(self):
        return self.table.selected_key()

    def _request_search(self) -> None:
        self.searchRequested.emit(self.query(), self.search_mode())

    def _on_action(self, action_id: str) -> None:
        if action_id == "search":
            self._request_search()
        elif action_id == "show_all":
            self.showAllRequested.emit()
