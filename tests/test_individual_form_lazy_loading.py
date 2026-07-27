# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAZY = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_lazy.py"
PACKAGE = ROOT / "teamworks" / "Dlg" / "__init__.py"


def test_individual_form_is_patched_only_when_requested():
    source = PACKAGE.read_text(encoding="utf-8")
    assert "def __getattr__(name):" in source
    assert 'name != "DLG_Fiche_individuelle"' in source
    assert "lazy.install(module)" in source
    assert "DLG_Fiche_individuelle_lazy" not in source.split("def __getattr__", 1)[0]


def test_secondary_tabs_are_declared_as_lazy_factories():
    source = LAZY.read_text(encoding="utf-8")
    assert "class LazyNotebook" in source
    assert "self.pageQuestionnaire = None" in source
    assert "self.pageStatut = None" in source
    assert "self.pageContrats = None" in source
    assert "self.pagePresences = None" in source
    assert "self.pageScenarios = None" in source
    assert "self.pageFrais = None" in source
    assert "self.pageCandidatures = None" in source
    assert "wx.CallAfter(self.EnsurePageLoaded, new_page)" in source


def test_unopened_questionnaire_is_not_saved():
    source = LAZY.read_text(encoding="utf-8")
    assert "if self.notebook.pageQuestionnaire is not None:" in source
    assert "self.notebook.pageQuestionnaire.Sauvegarde()" in source


def test_historical_dialog_is_not_rewritten():
    historical = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle.py"
    raw = historical.read_bytes()
    assert b"class Notebook(wx.Notebook):" in raw
    assert b"DLG_Fiche_individuelle_lazy" not in raw
