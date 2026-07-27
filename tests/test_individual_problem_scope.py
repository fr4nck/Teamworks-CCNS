# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBLEMS = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_problems.py"
PACKAGE = ROOT / "teamworks" / "Dlg" / "__init__.py"


def test_individual_problem_patch_is_installed_after_lazy_loading():
    source = PACKAGE.read_text(encoding="utf-8")
    assert "DLG_Fiche_individuelle_problems" in source
    assert source.index("lazy.install(module)") < source.index("problems.install(module)")


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
