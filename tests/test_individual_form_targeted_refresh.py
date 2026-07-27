# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFRESH = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_refresh.py"
PACKAGE = ROOT / "teamworks" / "Dlg" / "__init__.py"


def test_targeted_refresh_is_installed_last():
    source = PACKAGE.read_text(encoding="utf-8")
    assert "DLG_Fiche_individuelle_refresh" in source
    assert source.index("problems.install(module)") < source.index("refresh.install(module)")


def test_fast_path_only_applies_to_existing_general_form_edits():
    source = REFRESH.read_text(encoding="utf-8")
    assert "self.nouvelleFiche is False" in source
    assert "_secondary_pages_are_unloaded(self.notebook)" in source
    assert "save is True" in source


def test_targeted_refresh_reads_one_person_only():
    source = REFRESH.read_text(encoding="utf-8")
    assert "FROM personnes WHERE IDpersonne=%d" in source
    assert "list_ctrl.RefreshObject(track)" in source
    assert "track.__dict__.update(replacement.__dict__)" in source


def test_full_refresh_remains_as_fallback():
    source = REFRESH.read_text(encoding="utf-8")
    assert "if not fast_path:" in source
    assert "frame.listCtrl_personnes.MAJ(IDpersonne=self.IDpersonne)" in source
