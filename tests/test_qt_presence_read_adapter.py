from __future__ import annotations

from types import SimpleNamespace

import sys
from pathlib import Path


QT_POC = Path(__file__).resolve().parents[1] / "poc" / "qt-theme"
if str(QT_POC) not in sys.path:
    sys.path.insert(0, str(QT_POC))

from presence_read_adapter import PresenceReadAdapter


class _ActivityReader:
    def __init__(self):
        self.person_ids = []

    def lire_presences_personne(self, person_id):
        self.person_ids.append(person_id)
        return [
            SimpleNamespace(
                IDpresence=1,
                date="2009-07-01",
                heure_debut="08:00",
                heure_fin="18:00",
                IDcategorie=1,
                intitule="",
            ),
            SimpleNamespace(
                IDpresence=2,
                date="2009-07-02",
                heure_debut="07:30",
                heure_fin="17:00",
                IDcategorie=1,
                intitule="",
            ),
            SimpleNamespace(
                IDpresence=3,
                date="2009-07-02",
                heure_debut="18:30",
                heure_fin="19:30",
                IDcategorie=5,
                intitule="Réunion de fonctionnement",
            ),
        ]

    def lire_categories_presences(self):
        return [
            SimpleNamespace(IDcategorie=1, nom_categorie="Animation", couleur="(213, 244, 138)"),
            SimpleNamespace(IDcategorie=5, nom_categorie="Réunion", couleur="(196, 225, 255)"),
        ]

    def lire_periodes_vacances(self):
        return [
            SimpleNamespace(
                IDperiode=5,
                nom="Eté",
                annee="2009",
                date_debut="2009-07-02",
                date_fin="2009-09-01",
            )
        ]


def test_presence_read_adapter_composes_reader_and_historical_projection():
    reader = _ActivityReader()
    adapter = PresenceReadAdapter(reader)

    views = adapter.list_presences("3")

    assert reader.person_ids == [3]
    assert len(views) == 3
    assert views[0].category == "Animation"
    assert views[0].date == "Mercredi 1 juillet 2009"
    assert views[0].schedule == "8h00-18h00"
    assert views[0].duration == "10h00"
    assert views[1].vacation == "Eté 2009"
    assert views[2].date == ""
    assert views[2].label == "Réunion (Réunion de fonctionnement)"
    assert views[2].duration == "1h00"


def test_presence_read_adapter_rejects_non_historical_ids():
    adapter = PresenceReadAdapter(_ActivityReader())

    for value in (None, True, 0, -1, "", "abc"):
        try:
            adapter.list_presences(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"ID invalide accepté: {value!r}")
