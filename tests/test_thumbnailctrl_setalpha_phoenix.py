from pathlib import Path


SOURCE_PATH = Path('teamworks/Ctrl/CTRL_thumbnailctrl.py')


def test_thumbnailctrl_uses_setalpha_directly():
    source = SOURCE_PATH.read_text(encoding='utf-8')
    start = source.index('    def LoadThumbnail(')
    end = source.index('class ThumbnailEvent', start)
    function_source = source[start:end]

    assert "'phoenix' in wx.PlatformInfo" not in function_source
    assert 'SetAlphaData' not in function_source
    assert 'img.SetAlpha(' in function_source
