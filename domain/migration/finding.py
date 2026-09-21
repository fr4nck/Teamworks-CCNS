"""Anomalie d'inventaire ou de réconciliation, avec code stable et gravité.

Toute anomalie détectée par l'inventaire doit être représentée par une
instance de Finding : aucune anomalie ne doit disparaître silencieusement
d'un rapport.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.migration.severity import Severity


@dataclass(frozen=True, slots=True)
class Finding:
    code: str
    severity: Severity
    table: str
    row_id: str
    message: str
    column: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code obligatoire")
        if not self.table.strip():
            raise ValueError("table obligatoire")
        if not self.message.strip():
            raise ValueError("message obligatoire")
