from pathlib import Path


SOURCE_PATH = Path("teamworks/Ctrl/CTRL_thumbnailctrl.py")


def test_thumbnailctrl_uses_wx_image_directly():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    get_shadow = source.split("def getShadow():", 1)[1].split("\n#-----------------------------------------------------------------------------", 1)[0]

    assert "fonction = wx.Image" not in get_shadow
    assert "wx.ImageFromStream" not in get_shadow
    assert "'phoenix' in wx.PlatformInfo" not in get_shadow
    assert "wx.Image(six.BytesIO(getDataTR()))" in get_shadow
    assert "wx.Image(six.BytesIO(getDataBL()))" in get_shadow
    assert "wx.Image(six.BytesIO(getDataSH()))" in get_shadow
