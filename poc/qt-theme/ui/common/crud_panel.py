from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .actions import ActionSpec, TwActionBar
from .data_table import TwDataTable
from .tokens import TOKENS, apply_typography


class TwCrudPanel(QFrame):
    """Patron commun des référentiels administrables."""

    addRequested = Signal()
    editRequested = Signal(object)
    deleteRequested = Signal(object)

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        model=None,
        description: str | None = None,
        icon_loader=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("twCrudPanel")
        root = QVBoxLayout(self)
        root.setContentsMargins(TOKENS.spacing.lg, TOKENS.spacing.lg, TOKENS.spacing.lg, TOKENS.spacing.lg)
        root.setSpacing(TOKENS.spacing.sm)

        title_label = QLabel(title)
        apply_typography(title_label, TOKENS.typography.section)
        root.addWidget(title_label)
        if description:
            description_label = QLabel(description)
            description_label.setWordWrap(True)
            description_label.setProperty("muted", True)
            root.addWidget(description_label)

        self.actions = TwActionBar(
            [
                ActionSpec("add", "Ajouter", "Ajouter.png"),
                ActionSpec("edit", "Modifier", "Modifier.png", enabled=False),
                ActionSpec("delete", "Supprimer", "Supprimer.png", role="destructive", enabled=False),
            ],
            icon_loader=icon_loader,
        )
        self.actions.triggered.connect(self._on_action)
        root.addWidget(self.actions)

        self.table = TwDataTable(model=model)
        self.table.selectionKeyChanged.connect(self._on_selection)
        self.table.activatedKey.connect(self.editRequested)
        root.addWidget(self.table, 1)

    def set_model(self, model) -> None:
        self.table.set_model(model)
        self._on_selection(None)

    def selected_key(self):
        return self.table.selected_key()

    def set_action_enabled(self, action_id: str, enabled: bool) -> None:
        self.actions.set_enabled(action_id, enabled)

    def _on_selection(self, key) -> None:
        has_selection = key is not None
        self.actions.set_enabled("edit", has_selection)
        self.actions.set_enabled("delete", has_selection)

    def _on_action(self, action_id: str) -> None:
        if action_id == "add":
            self.addRequested.emit()
            return
        key = self.selected_key()
        if key is None:
            return
        if action_id == "edit":
            self.editRequested.emit(key)
        elif action_id == "delete":
            self.deleteRequested.emit(key)
