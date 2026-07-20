"""Jour de semaine ISO utilisé par le domaine planning."""

from __future__ import annotations

from enum import IntEnum


class Weekday(IntEnum):
    """Jour de semaine avec numérotation ISO, du lundi (1) au dimanche (7)."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

    @classmethod
    def from_iso_weekday(cls, value: int) -> "Weekday":
        """Retourne le jour correspondant à un numéro ISO de semaine."""

        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Le numéro ISO du jour de semaine doit être un entier strict.")
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError("Le numéro ISO du jour de semaine doit être compris entre 1 et 7.") from exc
