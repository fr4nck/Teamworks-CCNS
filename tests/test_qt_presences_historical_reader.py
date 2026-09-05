from __future__ import annotations

import sqlite3
from pathlib import Path

from infrastructure.persistence.individual_activity_reader import IndividualActivityReader


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DB = ROOT / "teamworks" / "Static" / "Exemples" / "Exemple_TDATA.dat"


class _FakeDb:
    def __init__(self):
        self.last_query = ""
        self.queries: list[str] = []
        self.closed = False

    def ExecuterReq(self, query):
        self.last_query = query
        self.queries.append(query)

    def ResultatReq(self):
        if "FROM presences" in self.last_query:
            return [
                (1, "2009-07-01", "08:00", "18:00", 1, ""),
                (3, "2009-07-02", "18:30", "19:30", 5, "Réunion de fonctionnement"),
            ]
        if "FROM cat_presences" in self.last_query:
            return [(1, "Animation", "(213, 244, 138)"), (5, "Réunion", "(196, 225, 255)")]
        if "FROM periodes_vacances" in self.last_query:
            return [(5, "Eté", "2009", "2009-07-02", "2009-09-01")]
        raise AssertionError(self.last_query)

    def Close(self):
        self.closed = True


def test_presence_reader_preserves_historical_queries_and_ordering():
    fake = _FakeDb()
    reader = IndividualActivityReader(db_factory=lambda: fake)

    presences = reader.lire_presences_personne(3)
    categories = reader.lire_categories_presences()
    vacations = reader.lire_periodes_vacances()

    assert [(row.IDpresence, row.date, row.heure_debut, row.heure_fin) for row in presences] == [
        (1, "2009-07-01", "08:00", "18:00"),
        (3, "2009-07-02", "18:30", "19:30"),
    ]
    assert [(row.IDcategorie, row.nom_categorie) for row in categories] == [
        (1, "Animation"),
        (5, "Réunion"),
    ]
    assert [(row.nom, row.annee, row.date_debut, row.date_fin) for row in vacations] == [
        ("Eté", "2009", "2009-07-02", "2009-09-01"),
    ]
    assert "ORDER BY date, heure_debut" in fake.queries[0]

    reader.close()
    assert fake.closed is True


def test_historical_example_person_3_presence_contract():
    assert EXAMPLE_DB.is_file()
    with sqlite3.connect(EXAMPLE_DB) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM presences WHERE IDpersonne=?",
            (3,),
        ).fetchone()[0]
        first_rows = db.execute(
            "SELECT presences.IDpresence, presences.date, presences.heure_debut, "
            "presences.heure_fin, cat_presences.nom_categorie, presences.intitule "
            "FROM presences JOIN cat_presences "
            "ON presences.IDcategorie=cat_presences.IDcategorie "
            "WHERE presences.IDpersonne=? ORDER BY presences.date, presences.heure_debut LIMIT 3",
            (3,),
        ).fetchall()
        summer = db.execute(
            "SELECT nom, annee, date_debut, date_fin FROM periodes_vacances "
            "WHERE date_debut<=? AND date_fin>=?",
            ("2009-07-02", "2009-07-02"),
        ).fetchall()
        overnight = db.execute(
            "SELECT COUNT(*) FROM presences WHERE IDpersonne=? AND heure_fin<heure_debut",
            (3,),
        ).fetchone()[0]

    assert count == 1026
    assert first_rows == [
        (1, "2009-07-01", "08:00", "18:00", "Animation", ""),
        (2, "2009-07-02", "07:30", "17:00", "Animation", ""),
        (3, "2009-07-02", "18:30", "19:30", "Réunion", "Réunion de fonctionnement"),
    ]
    assert summer == [("Eté", "2009", "2009-07-02", "2009-09-01")]
    assert overnight == 0
