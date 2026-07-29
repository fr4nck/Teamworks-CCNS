from pathlib import Path


SOURCE_PATH = Path("teamworks/Ctrl/CTRL_thumbnailctrl.py")


def test_thumbnailctrl_uses_wx_image_directly():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "fonction = wx.Image" not in source
    assert "wx.ImageFromStream" not in source
    assert "'phoenix' in wx.PlatformInfo" not in source
    assert "wx.Image(six.BytesIO(getDataTR()))" in source
    assert "wx.Image(six.BytesIO(getDataBL()))" in source
    assert "wx.Image(six.BytesIO(getDataSH()))" in source
