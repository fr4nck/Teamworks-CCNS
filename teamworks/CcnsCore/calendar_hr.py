#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Petites projections RH destinées au calendrier Teamworks.

Ce module ne dépend ni de wxPython ni de la base de données. Il transforme des
lignes issues du registre du personnel en événements calendaires simples afin
que l'interface reste une couche d'affichage.
"""

import datetime


def _as_date(value):
    """Convertit une date Teamworks en ``datetime.date`` si possible."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _birthday_date(birth_date, year):
    """Projette une date de naissance sur l'année affichée.

    Pour une naissance le 29 février, Teamworks affiche l'événement le
    28 février les années non bissextiles. Il s'agit uniquement d'un choix
    d'affichage de l'agenda, sans portée juridique.
    """
    try:
        return datetime.date(year, birth_date.month, birth_date.day)
    except ValueError:
        if birth_date.month == 2 and birth_date.day == 29:
            return datetime.date(year, 2, 28)
        return None


def build_birthdays_index(rows, year):
    """Construit ``{date: [personnes...]}`` à partir du registre du personnel.

    ``rows`` contient des tuples ``(IDpersonne, nom, prenom, date_naiss)``.
    Les lignes sans date exploitable sont ignorées. Les personnes partageant
    le même anniversaire sont conservées et triées de façon déterministe.
    """
    result = {}
    for row in rows:
        if len(row) < 4:
            continue
        person_id, last_name, first_name, raw_birth_date = row[:4]
        birth_date = _as_date(raw_birth_date)
        if birth_date is None:
            continue

        event_date = _birthday_date(birth_date, int(year))
        if event_date is None:
            continue

        person = {
            "IDpersonne": person_id,
            "nom": (last_name or "").strip(),
            "prenom": (first_name or "").strip(),
            "date_naiss": birth_date,
        }
        result.setdefault(event_date, []).append(person)

    for people in result.values():
        people.sort(key=lambda item: (item["prenom"].casefold(), item["nom"].casefold(), item["IDpersonne"] or 0))
    return result


def format_birthday_names(people):
    """Retourne une liste compacte de noms pour l'infobulle/statut calendrier."""
    labels = []
    for person in people:
        first_name = (person.get("prenom") or "").strip()
        last_name = (person.get("nom") or "").strip()
        if first_name and last_name:
            labels.append("%s %s" % (first_name, last_name))
        else:
            labels.append(first_name or last_name or "Salarié")
    return ", ".join(labels)
