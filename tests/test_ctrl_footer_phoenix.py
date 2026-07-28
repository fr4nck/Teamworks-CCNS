from pathlib import Path


FOOTER_PATH = Path("teamworks/Ctrl/CTRL_Footer.py")


def test_footer_uses_wx_control_directly():
    source = FOOTER_PATH.read_text(encoding="utf-8")

    assert "from wx import Control" in source
    assert "wx.PyControl" not in source
    assert "'phoenix' in wx.PlatformInfo" not in source
    assert '"phoenix" in wx.PlatformInfo' not in source


def test_footer_source_is_utf8():
    data = FOOTER_PATH.read_bytes()
    data.decode("utf-8")
    assert b"iso-8859" not in data.lower()
