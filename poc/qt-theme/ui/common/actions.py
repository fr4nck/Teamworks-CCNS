from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QBoxLayout, QHBoxLayout, QToolButton, QVBoxLayout, QWidget

from .tokens import TOKENS


@dataclass(frozen=True)
class ActionSpec:
    id: str
    label: str
    icon: str | None = None
    tooltip: str = ""
    role: str = "normal"
    enabled: bool = True
    visible: bool = True


class TwActionBar(QWidget):
    """Barre d'actions homogène sans connaissance des règles métier."""

    triggered = Signal(str)

    def __init__(
        self,
        actions: tuple[ActionSpec, ...] | list[ActionSpec],
        parent: QWidget | None = None,
        *,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        icon_loader: Callable[[str], QIcon] | None = None,
    ) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QToolButton] = {}
        self._icon_loader = icon_loader
        layout_cls = QHBoxLayout if orientation == Qt.Orientation.Horizontal else QVBoxLayout
        self._layout: QBoxLayout = layout_cls(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(TOKENS.spacing.sm)

        for spec in actions:
            button = QToolButton(self)
            button.setObjectName("twActionButton")
            button.setProperty("actionRole", spec.role)
            button.setText(spec.label)
            button.setToolTip(spec.tooltip or spec.label)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setIconSize(QSize(TOKENS.icons.sm, TOKENS.icons.sm))
            button.setMinimumHeight(TOKENS.controls.height_standard)
            if spec.icon and icon_loader is not None:
                button.setIcon(icon_loader(spec.icon))
            button.setEnabled(spec.enabled)
            button.setVisible(spec.visible)
            button.clicked.connect(lambda _checked=False, action_id=spec.id: self.triggered.emit(action_id))
            self._layout.addWidget(button)
            self._buttons[spec.id] = button

        self._layout.addStretch(1)

    def button(self, action_id: str) -> QToolButton:
        return self._buttons[action_id]

    def set_enabled(self, action_id: str, enabled: bool) -> None:
        self.button(action_id).setEnabled(enabled)

    def set_visible(self, action_id: str, visible: bool) -> None:
        self.button(action_id).setVisible(visible)
