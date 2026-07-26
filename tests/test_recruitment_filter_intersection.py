from __future__ import annotations

import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
TARGET = TEAMWORKS / "Ol" / "OL_candidatures.py"


def test_recruitment_filter_intersection_is_explicit_and_deterministic() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")

    assert 'exec("listeID=%s" % texteFonction)' not in source
    assert "set.intersection(*(set(liste) for liste in listeListes))" in source


def test_recruitment_filter_intersects_real_filter_dimensions() -> None:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(TEAMWORKS))
    try:
        from Ol import OL_candidatures as candidatures

        candidatures.DICT_DISPONIBILITES = {
            10: [(1, datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))],
            20: [(2, datetime.date(2026, 8, 1), datetime.date(2026, 8, 31))],
            30: [(3, datetime.date(2026, 7, 15), datetime.date(2026, 8, 15))],
        }
        candidatures.DICT_CAND_FONCTIONS = {
            10: [1, 2],
            20: [2],
            30: [1, 3],
        }
        candidatures.DICT_CAND_AFFECTATIONS = {
            10: [100],
            20: [100, 200],
            30: [200],
        }

        filters = [
            {
                "nomControle": "candidature_dispo",
                "valeur": (datetime.date(2026, 7, 20), datetime.date(2026, 8, 5)),
            },
            {
                "nomControle": "candidature_fonctions",
                "valeur": [(1, "Animation")],
            },
            {
                "nomControle": "candidature_affectations",
                "valeur": [(200, "Bais")],
            },
            {
                "nomControle": "decision",
                "sql": "IDdecision=1",
                "valeur": 1,
            },
        ]

        candidate_ids, sql = candidatures.ListView.GetListeFiltres(object(), filters)
        assert candidate_ids == [30]
        assert sql == "IDdecision=1"

        no_intersection, no_sql = candidatures.ListView.GetListeFiltres(
            object(),
            [
                filters[1],
                {
                    "nomControle": "candidature_affectations",
                    "valeur": [(100, "La Guerche")],
                },
            ],
        )
        assert no_intersection == [10]
        assert no_sql == ""
    finally:
        sys.path.remove(str(TEAMWORKS))
        sys.path.remove(str(ROOT))


def test_recruitment_list_source_compiles() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")
    compile(source, str(TARGET), "exec")
