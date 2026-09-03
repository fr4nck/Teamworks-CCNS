from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QToolButton, QWidget

from .tokens import TOKENS


@dataclass(frozen=True)
class ChoiceSpec:
    id: str
    label: str
    icon: str | None = None


class TwChoiceStrip(QWidget):
    """Choix exclusifs compacts, sans logique métier."""

    valueChanged = Signal(object)

    def __init__(
        self,
        choices: tuple[ChoiceSpec, ...] | list[ChoiceSpec],
        parent: QWidget | None = None,
        *,
        icon_loader=None,
    ) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QToolButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS.spacing.xs)

        for index, spec in enumerate(choices):
            button = QToolButton(self)
            button.setObjectName("twChoiceButton")
            button.setText(spec.label)
            button.setCheckable(True)
            button.setMinimumHeight(TOKENS.controls.height_standard)
            button.setIconSize(QSize(TOKENS.icons.sm, TOKENS.icons.sm))
            if spec.icon and icon_loader is not None:
                button.setIcon(icon_loader(spec.icon))
            button.clicked.connect(lambda _checked=False, key=spec.id: self.valueChanged.emit(key))
            self._group.addButton(button, index)
            self._buttons[spec.id] = button
            layout.addWidget(button)
        layout.addStretch(1)

    def value(self):
        for key, button in self._buttons.items():
            if button.isChecked():
                return key
        return None

    def set_value(self, key) -> bool:
        button = self._buttons.get(key)
        if button is None:
            return False
        button.setChecked(True)
        return True
