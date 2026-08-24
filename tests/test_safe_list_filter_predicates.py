from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "teamworks"))
from Utils import UTILS_Filtres_listes


def predicate(type_donnee, choix, criteres, code="valeur", get_inscrits=None):
    return UTILS_Filtres_listes.ConstruirePredicat(
        {"typeDonnee": type_donnee, "choix": choix, "criteres": criteres, "code": code},
        get_inscrits=get_inscrits,
    )


def test_text_filters_handle_apostrophes_without_code_generation():
    eq = predicate("texte", "EGAL", "L'Haÿ")
    contains = predicate("texte", "CONTIENT", "haÿ")
    track = SimpleNamespace(valeur="L'HAŸ")
    assert eq(track)
    assert contains(track)


def test_two_text_predicates_keep_independent_criteria():
    first = predicate("texte", "EGAL", "alpha")
    second = predicate("texte", "EGAL", "beta")
    assert first(SimpleNamespace(valeur="ALPHA"))
    assert not first(SimpleNamespace(valeur="beta"))
    assert second(SimpleNamespace(valeur="BETA"))


def test_boolean_filters_preserve_legacy_truth_values():
    assert predicate("bool", "TRUE", None)(SimpleNamespace(valeur="1"))
    assert predicate("bool", "FALSE", None)(SimpleNamespace(valeur=None))


def test_numeric_filters_and_ranges_use_safe_literals():
    assert predicate("montant", "SUP", "10.5")(SimpleNamespace(valeur=11.0))
    assert predicate("entier", "COMPRIS", "2;4")(SimpleNamespace(valeur=3))
    assert not predicate("entier", "COMPRIS", "2;4")(SimpleNamespace(valeur=5))


def test_date_filters_keep_iso_string_comparison_contract():
    between = predicate("date", "COMPRIS", "2026-01-01;2026-12-31")
    assert between(SimpleNamespace(valeur="2026-08-24"))
    assert not between(SimpleNamespace(valeur="2027-01-01"))
    assert not between(SimpleNamespace(valeur=None))


def test_registered_filter_resolves_ids_once_and_uses_requested_attribute():
    calls = []
    def resolve(**kwargs):
        calls.append(kwargs)
        return [10, 12]
    pred = predicate("inscrits", "INSCRITS", {"x": 1}, code="individu", get_inscrits=resolve)
    assert calls == [{"mode": "individu", "choix": "INSCRITS", "criteres": {"x": 1}}]
    assert pred(SimpleNamespace(IDindividu=10))
    assert not pred(SimpleNamespace(IDindividu=11))


def test_objectlistview_no_longer_executes_filter_strings():
    source = (ROOT / "teamworks" / "Ctrl" / "CTRL_ObjectListView.py").read_text(encoding="utf-8")
    assert "eval(" not in source
    assert "Filter.Predicate(predicat)" in source
