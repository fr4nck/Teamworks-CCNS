from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ctrl_personnes_guards_missing_person():
    source = (ROOT / "teamworks/Ctrl/CTRL_Personnes.py").read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:\n            return" in source
    assert "donnees = DB.ResultatReq()[0]" not in source
