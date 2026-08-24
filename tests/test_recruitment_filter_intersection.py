from __future__ import annotations

import ast
import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
TARGET = TEAMWORKS / "Ol" / "OL_candidatures_core.py"


def _load_filter_method():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TARGET))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ListView":
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == "GetListeFiltres":
                    module = ast.Module(body=[member], type_ignores=[])
                    ast.fix_missing_locations(module)
                    namespace = {
                        "DICT_DISPONIBILITES": {},
                        "DICT_CAND_FONCTIONS": {},
                        "DICT_CAND_AFFECTATIONS": {},
                    }
                    exec(compile(module, str(TARGET), "exec"), namespace)
                    return namespace, namespace["GetListeFiltres"]
    raise AssertionError("ListView.GetListeFiltres introuvable")


def test_recruitment_filter_intersection_is_explicit_and_deterministic() -> None:
    source = TARGET.read_text(encoding="utf-8")

    assert 'exec("listeID=%s" % texteFonction)' not in source
    assert "set.intersection(*(set(liste) for liste in listeListes))" in source


def test_recruitment_filter_intersects_real_filter_dimensions() -> None:
    namespace, get_filters = _load_filter_method()
    namespace["DICT_DISPONIBILITES"] = {
        10: [(1, datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))],
        20: [(2, datetime.date(2026, 8, 1), datetime.date(2026, 8, 31))],
        30: [(3, datetime.date(2026, 7, 15), datetime.date(2026, 8, 15))],
    }
    namespace["DICT_CAND_FONCTIONS"] = {
        10: [1, 2],
        20: [2],
        30: [1, 3],
    }
    namespace["DICT_CAND_AFFECTATIONS"] = {
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

    candidate_ids, sql = get_filters(object(), filters)
    assert candidate_ids == [30]
    assert sql == "IDdecision=1"

    no_intersection, no_sql = get_filters(
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


def test_recruitment_list_source_compiles() -> None:
    source = TARGET.read_text(encoding="utf-8")
    compile(source, str(TARGET), "exec")
