# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBLEMS = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_problems.py"
PACKAGE = ROOT / "teamworks" / "Dlg" / "__init__.py"


def test_individual_problem_patch_is_installed_after_lazy_loading():
    source = PACKAGE.read_text(encoding="utf-8")
    assert "DLG_Fiche_individuelle_problems" in source
    assert source.index("lazy.install(module)") < source.index("problems.install(module)")


def test_contract_lookup_is_scoped_to_opened_person():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert "WHERE contrats.IDpersonne=%d" in source
    assert "LIMIT 1" in source
    assert "_has_current_or_future_contract(module, IDpersonne)" in source


def test_contract_dates_keep_historical_predicate():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert "contrats.date_fin>='%s' AND contrats.date_rupture=''" in source
    assert "contrats.date_rupture<>'' AND contrats.date_rupture>='%s'" in source


def test_global_contract_function_is_temporarily_replaced_and_restored():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert "original_contract_search" in source
    assert "lambda: [IDpersonne] if has_contract else []" in source
    assert "finally:" in source
    assert "Recherche_ContratsEnCoursOuAVenir = original_contract_search" in source


def test_fallback_does_not_retry_dialog_initialization():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert "has_contract = IDpersonne in original_contract_search()" in source
    assert source.count("super(ScopedProblemsDialog, self).__init__") == 1


def test_contract_page_refresh_reuses_scoped_lookup():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert "module.CTRL_Page_contrats.Panel_Contrats" in source
    assert "has_contract = _has_current_or_future_contract(module, self.IDpersonne)" in source
    assert "grand_parent.barre_problemes = has_contract" in source
    assert "grand_parent.MAJ_barre_problemes()" in source


def test_contract_page_refresh_keeps_historical_fallback():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert "original_refresh = panel_class.MAJ_barre_problemes" in source
    assert "return original_refresh(self)" in source
    assert "_SCOPED_CONTRACT_REFRESH_INSTALLED" in source


def test_problem_fallback_is_scoped_to_current_person():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert "listeIDpersonnes=(self.IDpersonne,)" in source
    assert "Recup_liste_pb_personnes" not in source
    assert "Creation_liste_pb_personnes" not in source


def test_existing_global_cache_is_reused():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert "top_window.dictProblemesPersonnes" in source
    assert "cached.get(self.IDpersonne, {})" in source


def test_problem_text_format_remains_compatible():
    source = PROBLEMS.read_text(encoding="utf-8")
    assert '"%s (%s)" % (category, ", ".join(labels))' in source
    assert '"       ".join(parts) + "       "' in source
