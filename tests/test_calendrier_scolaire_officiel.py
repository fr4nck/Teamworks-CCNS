import datetime
import json
from urllib.parse import parse_qs, urlparse

import pytest

from teamworks.Utils import UTILS_Calendrier_scolaire_officiel as calendrier


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_mapping_zones_metropole():
    assert calendrier.normaliser_zone("A") == "A"
    assert calendrier.normaliser_zone("Zone B") == "B"
    assert calendrier.libelle_zone("C") == "Zone C"
    assert 'zones%3D%22Zone+A%22' in calendrier.construire_url_api("A")


def test_api_pagine_dedoublonne_et_filtre_enseignants(monkeypatch):
    pages = {
        0: {
            "total_count": 3,
            "results": [
                {
                    "description": "Vacances de la Toussaint",
                    "population": "-",
                    "start_date": "2026-10-16T22:00:00+00:00",
                    "end_date": "2026-11-01T23:00:00+00:00",
                    "location": "Lyon",
                    "zones": "Zone A",
                    "annee_scolaire": "2026-2027",
                },
                {
                    "description": "Vacances de la Toussaint",
                    "population": "-",
                    "start_date": "2026-10-16T22:00:00+00:00",
                    "end_date": "2026-11-01T23:00:00+00:00",
                    "location": "Grenoble",
                    "zones": "Zone A",
                    "annee_scolaire": "2026-2027",
                },
            ],
        },
        2: {
            "total_count": 3,
            "results": [
                {
                    "description": "Pré-rentrée des enseignants",
                    "population": "Enseignants",
                    "start_date": "2026-08-30T22:00:00+00:00",
                    "end_date": "2026-08-31T22:00:00+00:00",
                    "location": "Lyon",
                    "zones": "Zone A",
                    "annee_scolaire": "2026-2027",
                },
            ],
        },
    }

    def fake_request(url, timeout):
        query = parse_qs(urlparse(url).query)
        offset = int(query.get("offset", ["0"])[0])
        return _Response(pages[offset])

    monkeypatch.setattr(calendrier, "_requete", fake_request)
    vacances = calendrier.charger_depuis_api("A")

    assert len(vacances) == 1
    vacance = vacances[0]
    assert vacance.nom == "Toussaint"
    assert vacance.date_debut == datetime.date(2026, 10, 17)
    assert vacance.date_fin == datetime.date(2026, 11, 1)
    assert vacance.annee_scolaire == "2026-2027"


def test_fallback_ical_officiel(monkeypatch):
    attendu = calendrier.VacanceOfficielle(
        nom="Noël",
        date_debut=datetime.date(2026, 12, 19),
        date_fin=datetime.date(2027, 1, 3),
        annee_scolaire="2026-2027",
        zone="Zone A",
    )

    def api_ko(zone, timeout=calendrier.DEFAULT_TIMEOUT):
        raise OSError("api indisponible")

    monkeypatch.setattr(calendrier, "charger_depuis_api", api_ko)
    monkeypatch.setattr(
        calendrier,
        "charger_depuis_ical",
        lambda zone, timeout=calendrier.DEFAULT_TIMEOUT: [attendu],
    )

    resultat = calendrier.charger_vacances("A")
    assert resultat.source == "ical"
    assert resultat.vacances == (attendu,)
    assert "api indisponible" in resultat.avertissement


def test_source_ne_contient_plus_ancien_endpoint():
    source = open(
        "teamworks/Utils/UTILS_Calendrier_scolaire_officiel.py",
        encoding="utf-8",
    ).read()
    dialog = open(
        "teamworks/Dlg/DLG_Importation_vacances.py",
        encoding="utf-8",
    ).read()
    assert "media.education.gouv.fr" not in source
    assert "media.education.gouv.fr" not in dialog
    assert "NOUVELLES Zones par département" not in dialog
    assert "GetParent().SetLabelPeriodes" not in dialog
    assert "owner=self" in dialog
    assert "wx.CallAfter" in dialog
    assert "daemon=True" in dialog
