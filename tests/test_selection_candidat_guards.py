from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "teamworks/Dlg/DLG_Selection_candidat.py").read_text(encoding="utf-8")


def test_get_id_candidat_guards_empty_selection():
    assert "selection = self.listCtrl_candidats.Selection()" in SOURCE
    assert "if not selection:" in SOURCE
    assert "return selection[0].IDcandidat" in SOURCE
    assert "self.listCtrl_candidats.Selection()[0].IDcandidat" not in SOURCE


def test_get_id_personne_guards_empty_selection():
    assert "selection = self.listCtrl_personnes.Selection()" in SOURCE
    assert SOURCE.count("if not selection:") >= 2
    assert "return selection[0].IDpersonne" in SOURCE
    assert "self.listCtrl_personnes.Selection()[0].IDpersonne" not in SOURCE
