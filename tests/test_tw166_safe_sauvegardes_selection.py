from pathlib import Path


def test_sauvegardes_auto_reuses_checked_selection_before_indexing():
    source = Path("teamworks/Ol/OL_Sauvegardes_auto.py").read_text(encoding="utf-8")

    assert "selection = self.Selection()" in source
    assert "noSelection = len(selection) == 0" in source
    assert source.count("if not selection:") >= 2
    assert source.count("track = selection[0]") >= 2
    assert "self.Selection()[0]" not in source
