from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DB = ROOT / "teamworks" / "Static" / "Exemples" / "Exemple_TDATA.dat"


def test_historical_example_person_3_qualifications_and_received_pieces():
    assert EXAMPLE_DB.is_file()
    with sqlite3.connect(EXAMPLE_DB) as db:
        qualifications = db.execute(
            "SELECT types_diplomes.nom_diplome "
            "FROM diplomes JOIN types_diplomes "
            "ON diplomes.IDtype_diplome=types_diplomes.IDtype_diplome "
            "WHERE diplomes.IDpersonne=? ORDER BY types_diplomes.nom_diplome",
            (3,),
        ).fetchall()
        received_pieces = db.execute(
            "SELECT types_pieces.nom_piece, pieces.date_debut, pieces.date_fin "
            "FROM pieces JOIN types_pieces "
            "ON pieces.IDtype_piece=types_pieces.IDtype_piece "
            "WHERE pieces.IDpersonne=? ORDER BY pieces.date_debut",
            (3,),
        ).fetchall()

    assert qualifications == [("A.F.P.S.",), ("B.A.F.A",)]
    assert received_pieces == [
        ("Diplôme B.A.F.A.", "2006-01-20", "2999-01-01"),
        ("Certificat médical de non-contagion", "2009-01-01", "2009-04-01"),
        ("Bulletin n°3 du casier judiciaire", "2009-05-15", "2010-05-15"),
    ]


def test_historical_piece_indefinite_date_is_not_contract_label_semantics():
    """wx Qualifications formate 2999-01-01 comme une date, pas comme `Indétermin.`."""
    assert "01/01/2999" != "Indétermin."
