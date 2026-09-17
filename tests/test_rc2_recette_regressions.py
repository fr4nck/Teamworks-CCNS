# -*- coding: utf-8 -*-
import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _method_source(path, class_name, method_name):
    text = (ROOT / path).read_text(encoding="utf-8")
    tree = ast.parse(text)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method_name)
    lines = text.splitlines()
    return "\n".join(lines[method.lineno - 1:method.end_lineno])


def test_contract_context_menu_no_longer_targets_missing_page_handlers():
    path = "teamworks/Ctrl/CTRL_Creation_contrat_p4.py"
    for method_name in ("Menu_Ajouter", "Menu_Modifier", "Menu_Supprimer"):
        body = _method_source(path, "ListCtrl_champs", method_name)
        assert "self.parent.OnBoutonChamps(None)" in body
        assert "self.parent.OnBoutonAjouter" not in body
        assert "self.parent.OnBoutonModifier" not in body
        assert "self.parent.OnBoutonSupprimer" not in body


def test_nullable_mailmerge_field_values_are_normalized_before_wx_setvalue():
    body = _method_source(
        "teamworks/Dlg/DLG_Saisie_champs_publipostage.py",
        "Dialog",
        "Importation",
    )
    assert 'nom = "" if nom is None else str(nom)' in body
    assert 'defaut = "" if defaut is None else str(defaut)' in body
    assert 'mot_cle = "" if mot_cle is None else str(mot_cle)' in body
    assert body.index('nom = "" if nom is None else str(nom)') < body.index("self.text_nom.SetValue(nom)")


def test_mailmerge_worker_snapshot_never_passes_none_or_missing_advertised_tags():
    lifecycle = _load(
        "teamworks/Dlg/DLG_Publiposteur_lifecycle.py",
        "dlg_publiposteur_lifecycle_rc2",
    )
    source = {
        "NBREDOCUMENTS": 1,
        "MOTSCLES": [("NOM", "base"), ("CPNAISS", "base"), ("ADRESSERESID", "base")],
        1: {"NOM": None, "ADRESSERESID": None, "_IDPERSONNE": 42},
    }
    snapshot = lifecycle.normalize_merge_documents(source)
    assert snapshot[1]["NOM"] == ""
    assert snapshot[1]["CPNAISS"] == ""
    assert snapshot[1]["ADRESSERESID"] == ""
    assert source[1]["NOM"] is None
    assert "CPNAISS" not in source[1]


def test_worker_owns_automation_without_reading_wx_controls():
    text = (ROOT / "teamworks/Dlg/DLG_Publiposteur_lifecycle.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "_PublipostageWorker")
    run = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "run")
    lines = text.splitlines()
    body = "\n".join(lines[run.lineno - 1:run.end_lineno])
    assert "GetGrandParent" not in body
    assert ".gauge" not in body
    assert ".bouton_" not in body
    assert "wx." not in body
    assert "_post(" in body
    assert ".isAlive(" not in text
    assert ".is_alive()" in text


def test_runtime_patch_is_installed_without_removing_existing_lazy_fiche_patch():
    dlg_init = (ROOT / "teamworks/Dlg/__init__.py").read_text(encoding="utf-8")
    assert 'name == "DLG_Publiposteur"' in dlg_init
    assert "DLG_Publiposteur_lifecycle" in dlg_init
    assert "lifecycle.install(module)" in dlg_init
    assert 'name == "DLG_Fiche_individuelle"' in dlg_init
    assert "lazy.install(module)" in dlg_init
    assert "problems.install(module)" in dlg_init
    assert "refresh.install(module)" in dlg_init


def test_contract_mapping_uses_real_ccns_group_and_keeps_cee_distinct():
    mapping = _load(
        "teamworks/Utils/UTILS_Publipostage_donnees_rc2.py",
        "utils_publipostage_donnees_rc2",
    )
    ccns = {
        "CLASSIFICATION": "G3",
        "CONVENTION": "CCNS",
        "GROUPECCNS": "G3",
        "QUALIFICATIONCEE": "",
        "DATEDEBUT": "01/02/2026",
    }
    assert mapping.classification_for_contract(ccns, has_legacy_classification=False) == "Groupe 3"

    cee = {
        "CLASSIFICATION": "BAFA titulaire",
        "CONVENTION": "",
        "GROUPECCNS": "",
        "QUALIFICATIONCEE": "BAFA titulaire",
        "DATEDEBUT": "01/02/2026",
    }
    assert mapping.classification_for_contract(cee, has_legacy_classification=False) == ""

    historical = {
        "CLASSIFICATION": "Technicien",
        "CONVENTION": "CCNS",
        "GROUPECCNS": "G3",
        "QUALIFICATIONCEE": "",
        "DATEDEBUT": "01/02/2026",
    }
    assert mapping.classification_for_contract(historical, has_legacy_classification=True) == "Technicien"


def test_all_advertised_contract_and_person_tags_are_text_normalized():
    mapping = _load(
        "teamworks/Utils/UTILS_Publipostage_donnees_rc2.py",
        "utils_publipostage_donnees_rc2_normalize",
    )
    keywords, data = mapping.normalize_public_document(
        ["CLASSIFICATION", "CPNAISS", "ADRESSERESID", "CUSTOM"],
        {"CLASSIFICATION": "Groupe 2", "CPNAISS": None, "ADRESSERESID": None},
    )
    assert keywords == ["CLASSIFICATION", "CPNAISS", "ADRESSERESID", "CUSTOM"]
    assert data == {
        "CLASSIFICATION": "Groupe 2",
        "CPNAISS": "",
        "ADRESSERESID": "",
        "CUSTOM": "",
    }

    source = (ROOT / "teamworks/Utils/UTILS_Publipostage_donnees.py").read_text(encoding="utf-8")
    assert 'dictDonnees["CPNAISS"] = _format_postal_code(cp_naiss)' in source
    assert 'dictDonnees["ADRESSERESID"] = adresse_resid' in source
    assert '"CPNAISS", "VILLENAISS"' in source
    assert '"ADRESSERESID", "CPRESID"' in source

    utils_init = (ROOT / "teamworks/Utils/__init__.py").read_text(encoding="utf-8")
    assert 'name == "UTILS_Publipostage_donnees"' in utils_init
    assert "UTILS_Publipostage_donnees_rc2" in utils_init
    assert "rc2.install(module)" in utils_init
