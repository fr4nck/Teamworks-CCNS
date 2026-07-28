from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MESSAGEBOX = ROOT / "teamworks" / "Dlg" / "DLG_Messagebox.py"


def test_messagebox_uses_phoenix_multiline_text_extent_directly():
    source = MESSAGEBOX.read_text(encoding="utf-8")

    assert "GetFullMultiLineTextExtent(detail)" in source
    assert "GetMultiLineTextExtent(detail)" not in source
    assert "'phoenix' in wx.PlatformInfo" not in source
    assert '"phoenix" in wx.PlatformInfo' not in source


def test_messagebox_source_is_declared_utf8():
    first_lines = MESSAGEBOX.read_text(encoding="utf-8").splitlines()[:2]

    assert "coding: utf-8" in first_lines[1]
