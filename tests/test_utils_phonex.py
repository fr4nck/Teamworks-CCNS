import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "teamworks" / "Utils" / "UTILS_Phonex.py"

spec = importlib.util.spec_from_file_location("UTILS_Phonex_under_test", MODULE_PATH)
UTILS_Phonex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(UTILS_Phonex)


def test_phonex_accepts_compound_and_accented_city_names():
    expected = UTILS_Phonex.phonex("SAINT MALO")

    assert UTILS_Phonex.phonex("Saint-Malo") == expected
    assert UTILS_Phonex.phonex("Saint'Malo") == expected
    assert UTILS_Phonex.phonex("Sàint Mâlo") == expected


def test_phonex_tolerates_empty_and_non_text_values():
    assert UTILS_Phonex.phonex(None) == 0.0
    assert UTILS_Phonex.phonex("") == 0.0
    assert UTILS_Phonex.phonex(" - ' ") == 0.0
    assert UTILS_Phonex.phonex(12345) == 0.0


def test_phonex_can_be_used_as_a_sqlite_function_on_compound_names():
    connection = sqlite3.connect(":memory:")
    connection.create_function("phonex", 1, UTILS_Phonex.phonex)
    connection.execute("CREATE TABLE villes (ville TEXT)")
    connection.executemany(
        "INSERT INTO villes (ville) VALUES (?)",
        [
            ("AIX EN PROVENCE",),
            ("AEROPORT D'ORLY",),
            ("L'HAŸ LES ROSES",),
            (None,),
        ],
    )

    resultats = connection.execute(
        "SELECT ville FROM villes WHERE phonex(ville)=phonex(?)",
        ("Aix-en-Provence",),
    ).fetchall()

    assert resultats == [("AIX EN PROVENCE",)]
