# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAZY = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_lazy.py"
PACKAGE = ROOT / "teamworks" / "Dlg" / "__init__.py"
CORE = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_core.py"
WRAPPER = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle.py"


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


def test_contract_header_is_loaded_without_building_contract_tab():
    source = LAZY.read_text(encoding="utf-8")
    assert "self._load_contract_summary()" in source
    assert "def _load_contract_summary(self):" in source
    assert "FROM contrats" in source
    assert "LEFT JOIN contrats_class" in source
    assert "dialog.contratEnCours" in source
    assert "self.pageContrats = None" in source


def test_unopened_questionnaire_is_not_saved():
    source = LAZY.read_text(encoding="utf-8")
    assert "if self.notebook.pageQuestionnaire is not None:" in source
    assert "self.notebook.pageQuestionnaire.Sauvegarde()" in source


def test_historical_core_is_preserved_behind_active_wrapper():
    core = CORE.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")

    assert "class Notebook(wx.Notebook):" in core
    assert "class Dialog(wx.Dialog):" in core
    assert "from Dlg import DLG_Fiche_individuelle_core as CORE" in wrapper
    assert "class Dialog(CORE.Dialog):" in wrapper
    assert "DLG_Fiche_individuelle_lazy" not in wrapper
