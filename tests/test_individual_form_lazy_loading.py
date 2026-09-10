# -*- coding: utf-8 -*-
import importlib
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAZY = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_lazy.py"
PACKAGE = ROOT / "teamworks" / "Dlg" / "__init__.py"
CORE = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_core.py"
WRAPPER = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle.py"


def test_individual_form_is_imported_and_patched_only_on_attribute_access(monkeypatch):
    """Le package Dlg reste léger jusqu'au premier accès à la fiche individuelle."""
    source = PACKAGE.read_text(encoding="utf-8")
    events = []
    individual_form = types.SimpleNamespace()

    def patch_module(label):
        patch = types.SimpleNamespace()

        def install(module):
            events.append(("patch", label))
            if label == "lazy":
                module._LAZY_INDIVIDUAL_FORM_INSTALLED = True
            return module

        patch.install = install
        return patch

    fake_modules = {
        "Dlg_test.DLG_Fiche_individuelle": individual_form,
        "Dlg_test.DLG_Fiche_individuelle_lazy": patch_module("lazy"),
        "Dlg_test.DLG_Fiche_individuelle_problems": patch_module("problems"),
        "Dlg_test.DLG_Fiche_individuelle_refresh": patch_module("refresh"),
    }

    def fake_import_module(name):
        events.append(("import", name))
        return fake_modules[name]

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    package = types.ModuleType("Dlg_test")
    package.__package__ = "Dlg_test"
    exec(compile(source, str(PACKAGE), "exec"), package.__dict__)

    # Charger le package seul ne doit ni importer ni patcher la fiche.
    assert events == []
    assert "DLG_Fiche_individuelle" not in package.__dict__
    assert not hasattr(individual_form, "_LAZY_INDIVIDUAL_FORM_INSTALLED")

    # Un autre attribut, même absent, ne doit pas déclencher ce chargement.
    try:
        getattr(package, "ATTRIBUT_INCONNU")
    except AttributeError:
        pass
    else:
        raise AssertionError("Un attribut inconnu doit lever AttributeError")
    assert events == []
    assert not hasattr(individual_form, "_LAZY_INDIVIDUAL_FORM_INSTALLED")

    # Le premier accès à la fiche déclenche les imports puis les trois patches.
    loaded = package.DLG_Fiche_individuelle
    assert loaded is individual_form
    assert package.__dict__["DLG_Fiche_individuelle"] is individual_form
    assert individual_form._LAZY_INDIVIDUAL_FORM_INSTALLED is True
    assert events == [
        ("import", "Dlg_test.DLG_Fiche_individuelle"),
        ("import", "Dlg_test.DLG_Fiche_individuelle_lazy"),
        ("import", "Dlg_test.DLG_Fiche_individuelle_problems"),
        ("import", "Dlg_test.DLG_Fiche_individuelle_refresh"),
        ("patch", "lazy"),
        ("patch", "problems"),
        ("patch", "refresh"),
    ]

    # L'attribut mis en cache ne doit pas réimporter ni repatcher au second accès.
    first_access_events = list(events)
    assert package.DLG_Fiche_individuelle is individual_form
    assert events == first_access_events


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
