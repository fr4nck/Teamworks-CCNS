from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .tokens import TOKENS, apply_typography


_PROFILE_SIZES = {
    "compact": (480, 320),
    "standard": (640, 480),
    "wide": (820, 620),
}


class TwDialogShell(QDialog):
    """Squelette commun des dialogues secondaires Teamworks."""

    validateRequested = Signal()
    cancelRequested = Signal()
    helpRequested = Signal()

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        profile: str = "standard",
        show_help: bool = True,
        primary_label: str = "Valider",
        cancel_label: str = "Annuler",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        width, height = _PROFILE_SIZES.get(profile, _PROFILE_SIZES["standard"])
        self.resize(width, height)
        self.setMinimumSize(min(width, 420), min(height, 280))

        root = QVBoxLayout(self)
        root.setContentsMargins(*(TOKENS.spacing.lg,) * 4)
        root.setSpacing(TOKENS.spacing.lg)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("twDialogTitle")
        apply_typography(self.title_label, TOKENS.typography.dialog_title)
        root.addWidget(self.title_label)

        self.content_frame = QFrame()
        self.content_frame.setObjectName("twDialogContent")
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(TOKENS.spacing.lg)
        root.addWidget(self.content_frame, 1)

        footer = QHBoxLayout()
        footer.setSpacing(TOKENS.spacing.sm)
        self.help_button = QPushButton("Aide")
        self.help_button.setObjectName("twSecondaryButton")
        self.help_button.setVisible(show_help)
        self.help_button.clicked.connect(self.helpRequested)
        footer.addWidget(self.help_button)
        footer.addStretch(1)

        self.primary_button = QPushButton(primary_label)
        self.primary_button.setObjectName("twPrimaryButton")
        self.primary_button.clicked.connect(self.validateRequested)
        footer.addWidget(self.primary_button)

        self.cancel_button = QPushButton(cancel_label)
        self.cancel_button.setObjectName("twSecondaryButton")
        self.cancel_button.clicked.connect(self._cancel)
        footer.addWidget(self.cancel_button)
        root.addLayout(footer)

    def set_content(self, widget: QWidget) -> None:
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            old = item.widget()
            if old is not None:
                old.setParent(None)
        self.content_layout.addWidget(widget, 1)

    def set_primary_label(self, text: str) -> None:
        self.primary_button.setText(text)

    def set_primary_enabled(self, enabled: bool) -> None:
        self.primary_button.setEnabled(enabled)

    def set_cancel_label(self, text: str) -> None:
        self.cancel_button.setText(text)

    def _cancel(self) -> None:
        self.cancelRequested.emit()
        self.reject()
