from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class SpacingTokens:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True)
class ControlTokens:
    height_compact: int = 28
    height_standard: int = 32
    height_toolbar: int = 36
    height_search: int = 38
    table_row_dense: int = 26
    table_header: int = 32


@dataclass(frozen=True)
class RadiusTokens:
    field: int = 4
    button: int = 4
    panel: int = 8
    dialog_section: int = 8
    round: int = 999


@dataclass(frozen=True)
class IconTokens:
    xs: int = 12
    sm: int = 16
    md: int = 20
    lg: int = 24
    avatar: int = 48


@dataclass(frozen=True)
class TypographyToken:
    family: str
    point_size: float
    weight: QFont.Weight


@dataclass(frozen=True)
class TypographyTokens:
    body: TypographyToken
    label: TypographyToken
    secondary: TypographyToken
    section: TypographyToken
    dialog_title: TypographyToken
    page_title: TypographyToken


@dataclass(frozen=True)
class UiTokens:
    spacing: SpacingTokens
    controls: ControlTokens
    radius: RadiusTokens
    icons: IconTokens
    typography: TypographyTokens


_DEFAULT_FONT = "Segoe UI Variable"

TOKENS = UiTokens(
    spacing=SpacingTokens(),
    controls=ControlTokens(),
    radius=RadiusTokens(),
    icons=IconTokens(),
    typography=TypographyTokens(
        body=TypographyToken(_DEFAULT_FONT, 10.0, QFont.Weight.Normal),
        label=TypographyToken(_DEFAULT_FONT, 9.5, QFont.Weight.Normal),
        secondary=TypographyToken(_DEFAULT_FONT, 9.0, QFont.Weight.Normal),
        section=TypographyToken(_DEFAULT_FONT, 10.5, QFont.Weight.DemiBold),
        dialog_title=TypographyToken(_DEFAULT_FONT, 14.0, QFont.Weight.DemiBold),
        page_title=TypographyToken(_DEFAULT_FONT, 17.0, QFont.Weight.DemiBold),
    ),
)

CONTENT_MARGIN = TOKENS.spacing.lg
DIALOG_MARGIN = TOKENS.spacing.lg
FIELD_GAP = TOKENS.spacing.sm
SECTION_GAP = TOKENS.spacing.lg
TOOLBAR_GAP = TOKENS.spacing.sm


def apply_typography(widget: QWidget, token: TypographyToken) -> None:
    """Applique un rôle typographique sans laisser chaque fiche fixer ses pixels."""
    font = widget.font()
    font.setFamilies([token.family, "Segoe UI"])
    font.setPointSizeF(token.point_size)
    font.setWeight(token.weight)
    widget.setFont(font)
