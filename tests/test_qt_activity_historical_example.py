from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
QT_POC = ROOT / "poc" / "qt-theme"
if str(QT_POC) not in sys.path:
    sys.path.insert(0, str(QT_POC))

from production_read_adapter import TeamworksProductionReadAdapter, _scenario_description, _scenario_period


EXAMPLE_DB = ROOT / "teamworks" / "Static" / "Exemples" / "Exemple_TDATA.dat"


def test_qt_scenarios_match_historical_example_person_3():
    assert EXAMPLE_DB.is_file()
    with sqlite3.connect(EXAMPLE_DB) as db:
        row = db.execute(
            "SELECT nom, description, date_debut, date_fin "
            "FROM scenarios WHERE IDpersonne=? ORDER BY date_debut DESC",
            (3,),
        ).fetchone()

    assert row is not None
    nom, description, date_debut, date_fin = row
    assert nom == "Année 2009"
    assert _scenario_period(date_debut, date_fin) == "Du 01/01/2009 au 31/12/2009"
    assert _scenario_description(description) == "Aucune description"


def test_qt_frais_match_historical_example_person_3():
    assert EXAMPLE_DB.is_file()
    with sqlite3.connect(EXAMPLE_DB) as db:
        trips = db.execute(
            "SELECT IDdeplacement, date, objet, ville_depart, ville_arrivee, distance, "
            "aller_retour, tarif_km, IDremboursement "
            "FROM deplacements WHERE IDpersonne=? ORDER BY date",
            (3,),
        ).fetchall()
        reimbursement = db.execute(
            "SELECT IDremboursement, date, montant, listeIDdeplacement "
            "FROM remboursements WHERE IDpersonne=? ORDER BY date",
            (3,),
        ).fetchone()

    assert len(trips) == 4
    views = [
        TeamworksProductionReadAdapter._trip_to_view(
            SimpleNamespace(
                IDdeplacement=row[0],
                date=row[1],
                objet=row[2],
                ville_depart=row[3],
                ville_arrivee=row[4],
                distance=row[5],
                aller_retour=row[6],
                tarif_km=row[7],
                IDremboursement=row[8],
            )
        )
        for row in trips
    ]

    assert [(view.number, view.date, view.purpose) for view in views] == [
        ("1", "12/06/2009", "Réunion"),
        ("2", "15/06/2009", "Formation"),
        ("4", "24/06/2009", "Formation"),
        ("3", "05/07/2009", "Repérages de terrain"),
    ]
    assert views[0].route == "QUIMPER <--> BREST"
    assert views[0].amount == "30.00 €"
    assert views[0].reimbursement == "N°1"
    assert views[-1].route == "QUIMPER -> LANDERNEAU"
    assert views[-1].amount == "16.60 €"
    assert views[-1].reimbursement == ""

    assert reimbursement == (1, "2009-06-19", 64.0, "1-2")
