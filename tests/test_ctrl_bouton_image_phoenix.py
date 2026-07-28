from pathlib import Path


SOURCE_PATH = Path("teamworks/Ctrl/CTRL_Bouton_image.py")


def test_ctrl_bouton_image_uses_phoenix_alpha_api_only():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "'phoenix' in wx.PlatformInfo" not in source
    assert '"phoenix" in wx.PlatformInfo' not in source
    assert "SetAlphaData" not in source
    assert ".SetAlpha(" in source
