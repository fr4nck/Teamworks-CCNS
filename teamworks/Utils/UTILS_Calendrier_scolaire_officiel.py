#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calendrier scolaire officiel du ministère de l'Éducation nationale.

Ce module constitue la frontière réseau de l'import de vacances Teamworks-CCNS.
Il ne dépend pas de wx et ne manipule aucun contrôle graphique.

Source principale : API Explore v2.1 du jeu fr-en-calendrier-scolaire.
Source de secours : ressources iCal officielles publiées avec le même jeu de
données sur data.gouv.fr / Opendatasoft.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import json
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import icalendar


DATASET = "fr-en-calendrier-scolaire"
API_BASE = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
    + DATASET
    + "/records"
)
API_PAGE_SIZE = 100
DEFAULT_TIMEOUT = 8
PARIS_TZ = ZoneInfo("Europe/Paris")

ZONE_LABELS = {
    "A": "Zone A",
    "B": "Zone B",
    "C": "Zone C",
}

ICAL_URLS = {
    "A": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Zone-A.ics",
    "B": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Zone-B.ics",
    "C": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Zone-C.ics",
    "CORSE": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Corse.ics",
    "GUADELOUPE": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Guadeloupe.ics",
    "GUYANE": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Guyane.ics",
    "MARTINIQUE": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Martinique.ics",
    "MAYOTTE": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Mayotte.ics",
    "REUNION": "https://fr.ftp.opendatasoft.com/openscol/fr-en-calendrier-scolaire/Reunion.ics",
}


class ErreurCalendrierScolaire(RuntimeError):
    """L'API et sa source officielle de secours sont indisponibles."""


@dataclass(frozen=True)
class VacanceOfficielle:
    nom: str
    date_debut: datetime.date
    date_fin: datetime.date
    annee_scolaire: str
    zone: str
    academie: str = ""
    population: str = ""

    @property
    def annee(self):
        # Compatibilité avec la table historique periodes_vacances.
        return self.date_debut.year


@dataclass(frozen=True)
class ResultatCalendrier:
    vacances: tuple
    source: str
    avertissement: str = ""


def normaliser_zone(zone):
    texte = str(zone or "").strip().upper()
    if texte.startswith("ZONE "):
        texte = texte[5:].strip()
    if texte in ZONE_LABELS:
        return texte
    if texte in ICAL_URLS:
        return texte
    raise ValueError("Zone scolaire non prise en charge : %r" % (zone,))


def libelle_zone(zone):
    code = normaliser_zone(zone)
    return ZONE_LABELS.get(code, code.title())


def _texte_normalise(value):
    texte = unicodedata.normalize("NFKD", str(value or ""))
    texte = "".join(car for car in texte if not unicodedata.combining(car))
    return " ".join(texte.casefold().replace("’", "'").split())


def _nom_teamworks(description):
    """Conserve les libellés historiques attendus par periodes_vacances."""
    brut = " ".join(str(description or "").split())
    normalise = _texte_normalise(brut)
    correspondances = (
        ("vacances d'hiver", "Février"),
        ("vacances de printemps", "Pâques"),
        ("vacances de la toussaint", "Toussaint"),
        ("vacances de noel", "Noël"),
        ("vacances d'ete", "Eté"),
        ("pont de l'ascension", "Pont de l'Ascension"),
    )
    for fragment, libelle in correspondances:
        if fragment in normalise:
            return libelle
    return brut


def _description_importable(description):
    normalise = _texte_normalise(description)
    return "vacances" in normalise or "pont de l'ascension" in normalise


def _population_importable(population):
    normalise = _texte_normalise(population)
    if not normalise or normalise == "-":
        return True
    if "enseignant" in normalise and "eleve" not in normalise:
        return False
    return True


def _date_locale(value):
    if isinstance(value, datetime.datetime):
        dt = value
    elif isinstance(value, datetime.date):
        return value
    else:
        texte = str(value or "").strip()
        if not texte:
            raise ValueError("date vide")
        if texte.endswith("Z"):
            texte = texte[:-1] + "+00:00"
        dt = datetime.datetime.fromisoformat(texte)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=PARIS_TZ)
    return dt.astimezone(PARIS_TZ).date()


def _vacance_depuis_champs(
    *,
    description,
    population,
    start_date,
    end_date,
    location,
    zone,
    annee_scolaire,
):
    if not _description_importable(description):
        return None
    if not _population_importable(population):
        return None
    debut = _date_locale(start_date)
    # L'API et iCal expriment la reprise via une borne de fin exclusive.
    fin = _date_locale(end_date) - datetime.timedelta(days=1)
    if fin < debut:
        return None
    return VacanceOfficielle(
        nom=_nom_teamworks(description),
        date_debut=debut,
        date_fin=fin,
        annee_scolaire=str(annee_scolaire or ""),
        zone=str(zone or ""),
        academie=str(location or ""),
        population=str(population or ""),
    )


def _dedoublonner(vacances):
    resultat = {}
    for vacance in vacances:
        cle = (
            _texte_normalise(vacance.nom),
            vacance.date_debut,
            vacance.date_fin,
        )
        if cle not in resultat:
            resultat[cle] = vacance
    return sorted(
        resultat.values(),
        key=lambda item: (item.date_debut, item.date_fin, item.nom),
    )


def _requete(url, timeout):
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Teamworks-CCNS/0.9.2",
        },
    )
    return urlopen(request, timeout=timeout)


def construire_url_api(zone, offset=0, limit=API_PAGE_SIZE):
    code = normaliser_zone(zone)
    if code not in ZONE_LABELS:
        raise ValueError("L'API par zone n'est configurée que pour A/B/C")
    params = {
        "limit": int(limit),
        "offset": int(offset),
        "where": 'zones="%s" AND end_date >= now()' % ZONE_LABELS[code],
        "order_by": "start_date",
    }
    return API_BASE + "?" + urlencode(params)


def charger_depuis_api(zone, timeout=DEFAULT_TIMEOUT):
    code = normaliser_zone(zone)
    vacances = []
    offset = 0
    total = None

    while total is None or offset < total:
        url = construire_url_api(code, offset=offset)
        with _requete(url, timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))

        results = payload.get("results")
        if not isinstance(results, list):
            raise ValueError("Réponse API sans liste results")
        if total is None:
            total = int(payload.get("total_count", len(results)))

        for item in results:
            if not isinstance(item, dict):
                continue
            vacance = _vacance_depuis_champs(
                description=item.get("description"),
                population=item.get("population"),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
                location=item.get("location"),
                zone=item.get("zones"),
                annee_scolaire=item.get("annee_scolaire"),
            )
            if vacance is not None:
                vacances.append(vacance)

        if not results:
            break
        offset += len(results)

    return _dedoublonner(vacances)


def _valeur_ical(component, nom):
    if nom not in component:
        return None
    try:
        return component.decoded(nom)
    except Exception:
        return component.get(nom)


def charger_depuis_ical(zone, timeout=DEFAULT_TIMEOUT):
    code = normaliser_zone(zone)
    url = ICAL_URLS.get(code)
    if not url:
        raise ValueError("Aucune ressource iCal officielle pour %s" % code)

    request = Request(url, headers={"User-Agent": "Teamworks-CCNS/0.9.2"})
    with urlopen(request, timeout=timeout) as response:
        calendrier = icalendar.Calendar.from_ical(response.read())

    vacances = []
    for component in calendrier.walk():
        if getattr(component, "name", "") != "VEVENT":
            continue
        description = str(component.get("SUMMARY") or component.get("DESCRIPTION") or "")
        population = "-"
        if not _description_importable(description):
            continue
        debut = _valeur_ical(component, "DTSTART")
        fin = _valeur_ical(component, "DTEND")
        if debut is None or fin is None:
            continue
        try:
            vacance = _vacance_depuis_champs(
                description=description,
                population=population,
                start_date=debut,
                end_date=fin,
                location="",
                zone=libelle_zone(code),
                annee_scolaire="",
            )
        except (TypeError, ValueError):
            continue
        if vacance is not None:
            vacances.append(vacance)
    return _dedoublonner(vacances)


def charger_vacances(zone, timeout=DEFAULT_TIMEOUT):
    """Charge les vacances de la zone, API d'abord puis iCal officiel."""
    code = normaliser_zone(zone)
    erreur_api = None
    try:
        vacances = charger_depuis_api(code, timeout=timeout)
        if vacances:
            return ResultatCalendrier(tuple(vacances), "api")
        erreur_api = RuntimeError("L'API officielle n'a retourné aucune période")
    except Exception as err:
        erreur_api = err

    try:
        vacances = charger_depuis_ical(code, timeout=timeout)
        if vacances:
            return ResultatCalendrier(
                tuple(vacances),
                "ical",
                "API officielle indisponible : %s" % erreur_api,
            )
        raise RuntimeError("Le calendrier iCal officiel est vide")
    except Exception as err_ical:
        raise ErreurCalendrierScolaire(
            "Calendrier scolaire officiel indisponible (API : %s ; iCal : %s)"
            % (erreur_api, err_ical)
        ) from err_ical
