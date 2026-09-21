"""Révision déterministe d'une présence sans colonne de version en base."""

from __future__ import annotations

import hashlib
from datetime import date, datetime


def _date_text(value) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if type(value) is date:
        return value.isoformat()
    return str(value or "").strip()[:10]


def _time_text(value) -> str:
    return str(value or "").strip()[:5]


def build_presence_revision(
    *,
    presence_id: int,
    presence_date,
    start_time,
    end_time,
    category_id: int,
    title,
) -> str:
    """Empreinte stable utilisée comme jeton de concurrence optimiste."""

    canonical = "\x1f".join(
        (
            str(int(presence_id)),
            _date_text(presence_date),
            _time_text(start_time),
            _time_text(end_time),
            str(int(category_id)),
            str(title or "").strip(),
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
