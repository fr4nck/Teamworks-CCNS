from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

UTIL_SOURCE = '''# -*- coding: utf-8 -*-
"""Prédicats sûrs pour les filtres de colonnes des ObjectListView."""
from __future__ import annotations

import ast


def _numeric_literal(value):
    if isinstance(value, bool):
        raise ValueError("Un booléen n'est pas un critère numérique")
    if isinstance(value, (int, float)):
        return value
    parsed = ast.literal_eval(str(value))
    if isinstance(parsed, bool) or not isinstance(parsed, (int, float)):
        raise ValueError("Critère numérique invalide : %r" % (value,))
    return parsed


def ConstruirePredicat(dictFiltre, get_inscrits=None):
    """Construit un prédicat sans générer ni exécuter de code Python."""
    code = dictFiltre["code"]
    choix = dictFiltre["choix"]
    criteres = dictFiltre["criteres"]
    type_donnee = dictFiltre["typeDonnee"]

    def valeur(track):
        return getattr(track, code, None)

    if type_donnee == "texte":
        critere = str(criteres).lower()
        if choix == "EGAL":
            return lambda track: valeur(track) is not None and valeur(track).lower() == critere
        if choix == "DIFFERENT":
            return lambda track: valeur(track) is not None and valeur(track).lower() != critere
        if choix == "CONTIENT":
            return lambda track: valeur(track) is not None and critere in valeur(track).lower()
        if choix == "CONTIENTPAS":
            return lambda track: valeur(track) is not None and critere not in valeur(track).lower()
        if choix == "VIDE":
            return lambda track: valeur(track) in ("", None)
        if choix == "PASVIDE":
            return lambda track: valeur(track) not in ("", None)

    if type_donnee == "bool":
        if choix == "TRUE":
            return lambda track: valeur(track) in (True, "True", 1, "1")
        if choix == "FALSE":
            return lambda track: valeur(track) in (False, "False", 0, "0", None, "")

    if type_donnee in ("entier", "montant"):
        if choix == "COMPRIS":
            minimum_texte, maximum_texte = str(criteres).split(";", 1)
            minimum = _numeric_literal(minimum_texte)
            maximum = _numeric_literal(maximum_texte)
            return lambda track: valeur(track) >= minimum and valeur(track) <= maximum
        critere = _numeric_literal(criteres)
        operations = {
            "EGAL": lambda current: current == critere,
            "DIFFERENT": lambda current: current != critere,
            "SUP": lambda current: current > critere,
            "SUPEGAL": lambda current: current >= critere,
            "INF": lambda current: current < critere,
            "INFEGAL": lambda current: current <= critere,
        }
        if choix in operations:
            operation = operations[choix]
            return lambda track: operation(valeur(track))

    if type_donnee in ("date", "dateheure"):
        if choix == "COMPRIS":
            minimum, maximum = str(criteres).split(";", 1)
            return lambda track: (
                valeur(track) is not None
                and str(valeur(track)) >= minimum
                and str(valeur(track)) <= maximum
            )
        critere = str(criteres)
        operations = {
            "EGAL": lambda current: current == critere,
            "DIFFERENT": lambda current: current != critere,
            "SUP": lambda current: current > critere,
            "SUPEGAL": lambda current: current >= critere,
            "INF": lambda current: current < critere,
            "INFEGAL": lambda current: current <= critere,
        }
        if choix in operations:
            operation = operations[choix]
            return lambda track: valeur(track) is not None and operation(str(valeur(track)))

    if type_donnee == "inscrits" and choix in ("INSCRITS", "PRESENTS"):
        if get_inscrits is None:
            raise ValueError("Le résolveur des inscrits est obligatoire")
        identifiants = frozenset(get_inscrits(mode=code, choix=choix, criteres=criteres))
        attribut = "ID%s" % code
        return lambda track: getattr(track, attribut, None) in identifiants

    raise ValueError(
        "Filtre de colonne non supporté : type=%r choix=%r code=%r"
        % (type_donnee, choix, code)
    )
'''

TEST_SOURCE = '''from __future__ import annotations

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
'''


def main() -> None:
    util_path = ROOT / "teamworks" / "Utils" / "UTILS_Filtres_listes.py"
    compile(UTIL_SOURCE, str(util_path), "exec")
    util_path.write_text(UTIL_SOURCE, encoding="utf-8")

    path = ROOT / "teamworks" / "Ctrl" / "CTRL_ObjectListView.py"
    source = path.read_text(encoding="utf-8")
    anchor = "from Utils import UTILS_Adaptations\n"
    if source.count(anchor) != 1:
        raise RuntimeError("Import UTILS_Adaptations inattendu")
    source = source.replace(anchor, anchor + "from Utils import UTILS_Filtres_listes\n")

    old_filter = '''        # Filtres de colonnes\n        for texteFiltre in self.formatageFiltres(self.listeFiltresColonnes) :\n            filtre = Filter.Predicate(lambda track: eval(texteFiltre))\n            listeFiltres.append(filtre)\n'''
    new_filter = '''        # Filtres de colonnes\n        for predicat in self.formatageFiltres(self.listeFiltresColonnes):\n            listeFiltres.append(Filter.Predicate(predicat))\n'''
    if source.count(old_filter) != 1:
        raise RuntimeError("Bloc Filtrer inattendu")
    source = source.replace(old_filter, new_filter)

    start = source.index("    def formatageFiltres(")
    end = source.index("    def GetInscrits(", start)
    source = source[:start] + '''    def formatageFiltres(self, listeFiltres=None):\n        """Transforme les spécifications de filtres en prédicats indépendants."""\n        if listeFiltres is None:\n            listeFiltres = []\n        return [\n            UTILS_Filtres_listes.ConstruirePredicat(\n                dictFiltre,\n                get_inscrits=self.GetInscrits,\n            )\n            for dictFiltre in listeFiltres\n        ]\n\n''' + source[end:]

    replacements = {
        "    def SetFiltresColonnes(self, listeFiltresColonnes=[]):\n        self.listeFiltresColonnes = listeFiltresColonnes\n": "    def SetFiltresColonnes(self, listeFiltresColonnes=None):\n        if listeFiltresColonnes is None:\n            listeFiltresColonnes = []\n        self.listeFiltresColonnes = listeFiltresColonnes\n",
        '    def GetInscrits(self, mode="individu", choix="", criteres={}):\n        """ Récupération de la liste des individus inscrits et présents """\n': '    def GetInscrits(self, mode="individu", choix="", criteres=None):\n        """ Récupération de la liste des individus inscrits et présents """\n        if criteres is None:\n            criteres = {}\n',
        "    def SetFooter(self, ctrl=None, dictColonnes={}):\n        self.ctrl_footer = ctrl\n": "    def SetFooter(self, ctrl=None, dictColonnes=None):\n        if dictColonnes is None:\n            dictColonnes = {}\n        self.ctrl_footer = ctrl\n",
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise RuntimeError("Signature mutable inattendue: %r" % old.splitlines()[0])
        source = source.replace(old, new)

    if "eval(" in source:
        raise RuntimeError("CTRL_ObjectListView contient encore eval(")
    compile(source, str(path), "exec")
    path.write_text(source, encoding="utf-8")

    test_path = ROOT / "tests" / "test_safe_list_filter_predicates.py"
    compile(TEST_SOURCE, str(test_path), "exec")
    test_path.write_text(TEST_SOURCE, encoding="utf-8")

    namespace = {}
    exec(compile(UTIL_SOURCE, str(util_path), "exec"), namespace)
    build = namespace["ConstruirePredicat"]
    class Track:
        valeur = "Alpha"
    assert build({"typeDonnee": "texte", "choix": "EGAL", "criteres": "alpha", "code": "valeur"})(Track())
    assert not build({"typeDonnee": "texte", "choix": "EGAL", "criteres": "beta", "code": "valeur"})(Track())


if __name__ == "__main__":
    main()
