from __future__ import annotations

import datetime as dt
from typing import Iterable

from data_adapter import PresenceView
from infrastructure.persistence.teamworks_contract_conversions import as_date


EMPTY = "—"
_DAYS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche")
_MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


def project_presences(records, categories, vacations) -> tuple[PresenceView, ...]:
    """Projette les présences sans dépendance wxPython ni SQL.

    Les conventions reproduites sont celles de ``CTRL_Page_presences`` :
    catégorie complétée par l'intitulé, vacances applicables, horaires ``8h00-18h00``,
    durée ``10h00`` et date complète uniquement sur la première ligne d'un même jour.
    """

    category_map = {
        int(item.IDcategorie): (str(item.nom_categorie or "").strip() or EMPTY, str(item.couleur or "").strip())
        for item in categories
    }
    vacation_items = tuple(vacations)
    views: list[PresenceView] = []
    previous_date = None

    for record in records:
        raw_date = as_date(record.date)
        category_id = int(record.IDcategorie)
        category, color = category_map.get(category_id, (EMPTY, ""))
        title = str(record.intitule or "").strip()
        label = category if not title else f"{category} ({title})"

        display_date = ""
        if raw_date is not None and raw_date != previous_date:
            display_date = _format_long_date(raw_date)

        views.append(
            PresenceView(
                key=int(record.IDpresence),
                category_id=category_id,
                category=category,
                category_color=color,
                date=display_date,
                vacation=_vacation_label(raw_date, vacation_items),
                schedule=_format_schedule(record.heure_debut, record.heure_fin),
                duration=_format_duration(record.heure_debut, record.heure_fin),
                label=label,
            )
        )
        previous_date = raw_date

    return tuple(views)


def _format_long_date(value: dt.date) -> str:
    return f"{_DAYS[value.weekday()]} {value.day} {_MONTHS[value.month - 1]} {value.year}"


def _format_time(value) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        return EMPTY
    hour, minute = parsed
    return f"{hour}h{minute:02d}"


def _format_schedule(start, end) -> str:
    start_text = _format_time(start)
    end_text = _format_time(end)
    if EMPTY in (start_text, end_text):
        return EMPTY
    return f"{start_text}-{end_text}"


def _format_duration(start, end) -> str:
    start_time = _parse_time(start)
    end_time = _parse_time(end)
    if start_time is None or end_time is None:
        return EMPTY
    start_minutes = start_time[0] * 60 + start_time[1]
    end_minutes = end_time[0] * 60 + end_time[1]
    # Le wx historique utilise timedelta.seconds : une différence négative est ramenée modulo 24 h.
    total = (end_minutes - start_minutes) % (24 * 60)
    return f"{total // 60}h{total % 60:02d}"


def _parse_time(value) -> tuple[int, int] | None:
    if value is None:
        return None
    text = str(value).strip()
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text[:2])
    except (TypeError, ValueError):
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute


def _vacation_label(date_value: dt.date | None, vacations: Iterable[object]) -> str:
    if date_value is None:
        return ""
    label = ""
    for period in vacations:
        start = as_date(period.date_debut)
        end = as_date(period.date_fin)
        if start is None or end is None or not (start <= date_value <= end):
            continue
        name = str(period.nom or "").strip()
        year = str(period.annee or "").strip()
        label = " ".join(part for part in (name, year) if part)
    return label
