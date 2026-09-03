from __future__ import annotations

from enum import StrEnum

from PySide6.QtWidgets import QWidget


class ValidationLevel(StrEnum):
    NEUTRAL = "neutral"
    SUCCESS = "success"
    VALID = "valid"  # compatibilité des premiers composants du POC
    WARNING = "warning"
    ERROR = "error"


def _repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def set_validation_state(
    widget: QWidget,
    state: ValidationLevel | str = ValidationLevel.NEUTRAL,
    message: str = "",
) -> None:
    """Déclare un état sémantique ; le thème reste seul responsable du rendu."""
    level = ValidationLevel(state)
    widget.setProperty("validationState", level.value)
    widget.setProperty("validationMessage", message)
    _repolish(widget)
