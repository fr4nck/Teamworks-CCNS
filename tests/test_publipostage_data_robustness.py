from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "teamworks" / "Utils" / "UTILS_Publipostage_donnees.py"


def _source():
    return SOURCE_PATH.read_text(encoding="utf-8")


def _tree():
    return ast.parse(_source(), filename=str(SOURCE_PATH))


def _load_helpers(*names):
    tree = _tree()
    wanted = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    module = ast.Module(body=wanted, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    return [namespace[name] for name in names]


def test_postal_codes_are_formatted_without_silent_data_loss():
    format_postal, = _load_helpers("_format_postal_code")
    assert format_postal(None) == ""
    assert format_postal("   ") == ""
    assert format_postal(7501) == "07501"
    assert format_postal("7501") == "07501"
    assert format_postal("2A000") == "2A000"


def test_optional_choice_indexes_are_safe():
    choice, = _load_helpers("_choice_label")
    values = ["A", "B"]
    assert choice(values, 1) == "B"
    assert choice(values, "0") == "A"
    assert choice(values, None) == ""
    assert choice(values, 99, "inconnu") == "inconnu"


def test_empty_mailmerge_selection_has_an_empty_keyword_list():
    tree = _tree()
    func = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "GetDictDonnees")
    module = ast.Module(body=[func], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"NOMS_EDITION": {"contrat": "NOM"}}
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    result = namespace["GetDictDonnees"]("contrat", [])
    assert result["NBREDOCUMENTS"] == 0
    assert result["MOTSCLES"] == []


def test_missing_records_use_the_same_tuple_contract():
    source = _source()
    assert source.count("if len(listeDonnees) == 0 : return [], {}") == 4
    assert "if not dictDonneesContrat:\n            return [], {}" in source
    assert "if not dictDonneesCandidature:\n            return [], {}" in source


def test_candidature_response_type_is_indexed_not_called():
    source = _source()
    assert "listeTypesReponses(IDtype_reponse)" not in source
    assert "_choice_label(listeTypesReponses, IDtype_reponse)" in source
    assert 'dictDonnees["DATEREPONSE"] = ""' in source
    assert 'dictDonnees["TYPEREPONSE"] = ""' in source


def test_person_mailmerge_tolerates_orphan_country_references_by_contract():
    source = _source()
    assert '_get_country_value(nationalite, "nationalite")' in source
    assert '_get_country_value(pays_naiss, "nom")' in source
    assert "listePays[0][0]" not in source


def test_candidate_no_longer_reads_an_undefined_birth_postal_code():
    tree = _tree()
    func = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "Importation_candidat")
    segment = ast.get_source_segment(_source(), func) or ""
    assert "cp_naiss" not in segment
    assert 'dictDonnees["CPRESID"] = _format_postal_code(cp_resid)' in segment


def test_legacy_six_postal_conversion_is_gone():
    source = _source()
    assert "import six" not in source
    assert "six." not in source
