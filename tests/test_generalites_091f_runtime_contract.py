from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_active_individual_dialog_uses_generalites_adapter():
    core = _source("teamworks/Dlg/DLG_Fiche_individuelle_core.py")
    assert "CTRL_Page_generalites_091e as CTRL_Page_generalites" in core


def test_generalites_adapter_keeps_all_sections_scrollable_and_stable():
    source = _source("teamworks/Ctrl/CTRL_Page_generalites_091e.py")

    assert "wx.ScrolledWindow" in source
    assert "self._scroll_host.FitInside()" in source
    assert "section.Reparent(host)" in source
    assert "self._appliquer_layout_responsive(force=True)" in source
    assert "wx.CallAfter(self._appliquer_layout_responsive)" not in source


def test_residence_address_is_free_and_non_blocking():
    source = _source("teamworks/Ctrl/CTRL_Page_generalites_091e.py")

    assert "def _configurer_cp_residence_libre(self):" in source
    assert 'self.text_cp.SetCtrlParameters(mask="")' in source
    assert "def Code_KillFocus2(self, event):" in source
    assert "def Ville_KillFocus2(self, event):" in source
    assert "def VilleText2(self, event):" in source

    residence = source.split("# Résidence", 1)[1].split("def SetEtatNumSecu", 1)[0]
    assert "wx.MessageDialog" not in residence
    assert "LEGACY.Panel_general.VilleText2" not in residence


def test_foreign_birth_remains_free_and_uses_nir_99_rule():
    source = _source("teamworks/Ctrl/CTRL_Page_generalites_091e.py")

    assert 'self.text_cp_naiss.SetCtrlParameters(mask="#####" if france else "")' in source
    assert "INTERNATIONAL.departement_nir_attendu" in source
    assert "pays_naissance=pays" in source
