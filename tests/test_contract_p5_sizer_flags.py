from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p5.py"


def test_vertical_contract_sizer_does_not_use_vertical_alignment_flag() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")

    assert "wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL" not in source
    assert 'sizer_champ.Add(getattr(self, "label_%sEX" % nom), 0, wx.ALIGN_RIGHT, 0)' in source


def test_contract_page_five_source_compiles() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")
    compile(source, str(TARGET), "exec")
