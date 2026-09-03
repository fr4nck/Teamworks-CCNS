from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .tokens import TOKENS, apply_typography
from .validation import ValidationLevel, set_validation_state


class TwFormSection(QFrame):
    """Section nommée de formulaire avec géométrie commune.

    ``compact=True`` conserve exactement le même langage visuel tout en réduisant
    les marges/espacements pour les fiches historiques très denses. La densité
    reste donc centralisée dans le composant commun plutôt que décidée écran par
    écran.
    """

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        description: str | None = None,
        compact: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("twFormSection")
        self.setProperty("twDensity", "compact" if compact else "standard")
        margin = TOKENS.spacing.sm if compact else TOKENS.spacing.md
        spacing = TOKENS.spacing.xs if compact else TOKENS.spacing.sm

        root = QVBoxLayout(self)
        root.setContentsMargins(margin, margin, margin, margin)
        root.setSpacing(spacing)

        title_label = QLabel(title)
        title_label.setObjectName("twSectionTitle")
        apply_typography(title_label, TOKENS.typography.section)
        root.addWidget(title_label)

        if description:
            description_label = QLabel(description)
            description_label.setWordWrap(True)
            description_label.setProperty("muted", True)
            apply_typography(description_label, TOKENS.typography.secondary)
            root.addWidget(description_label)

        self.body = QWidget(self)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(spacing)
        root.addWidget(self.body)

    def add_row(self, row: QWidget) -> None:
        self.body_layout.addWidget(row)

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        self.body_layout.addWidget(widget, stretch)

    def add_layout(self, layout) -> None:
        self.body_layout.addLayout(layout)


class TwFieldRow(QWidget):
    """Ligne label + éditeur + suffixe/action + message de validation."""

    def __init__(
        self,
        label: str,
        editor: QWidget,
        parent: QWidget | None = None,
        *,
        suffix: str | None = None,
        action: QWidget | None = None,
        help_text: str | None = None,
        compact: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setProperty("twDensity", "compact" if compact else "standard")
        self.editor = editor
        self.editor.setProperty("twDensity", "compact" if compact else "standard")
        if action is not None:
            action.setProperty("twDensity", "compact" if compact else "standard")

        self._validation = QLabel("")
        self._validation.setObjectName("twValidationMessage")
        self._validation.setWordWrap(True)
        self._validation.setVisible(False)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(TOKENS.spacing.xs)

        line = QHBoxLayout()
        line.setSpacing(TOKENS.spacing.xs if compact else TOKENS.spacing.sm)
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(122 if compact else 130)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        apply_typography(label_widget, TOKENS.typography.label)
        line.addWidget(label_widget)

        if hasattr(editor, "setMinimumHeight"):
            editor.setMinimumHeight(
                TOKENS.controls.height_compact if compact else TOKENS.controls.height_standard
            )
        line.addWidget(editor, 1)

        if suffix:
            suffix_widget = QLabel(suffix)
            suffix_widget.setProperty("muted", True)
            line.addWidget(suffix_widget)
        if action is not None:
            line.addWidget(action)
        root.addLayout(line)

        if help_text:
            help_label = QLabel(help_text)
            help_label.setProperty("muted", True)
            help_label.setWordWrap(True)
            apply_typography(help_label, TOKENS.typography.secondary)
            root.addWidget(help_label)

        root.addWidget(self._validation)

    def set_validation(self, state: ValidationLevel | str, message: str = "") -> None:
        level = ValidationLevel(state)
        set_validation_state(self.editor, level, message)
        self._validation.setProperty("validationState", level.value)
        self._validation.setText(message)
        self._validation.setVisible(bool(message) and level is not ValidationLevel.NEUTRAL)
        style = self._validation.style()
        style.unpolish(self._validation)
        style.polish(self._validation)
        self._validation.update()

    def clear_validation(self) -> None:
        self.set_validation(ValidationLevel.NEUTRAL, "")
