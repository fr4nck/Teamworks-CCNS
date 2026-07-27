from pathlib import Path

from tools.rewrite_redundant_phoenix_branches import rewrite


def test_rewrite_removes_identical_phoenix_branch(tmp_path: Path):
    source = """\
import wx

def fill(ctrl):
    if 'phoenix' in wx.PlatformInfo:
        ctrl.SetItem(0, 1, 'x')
    else:
        ctrl.SetItem(0, 1, 'x')
"""
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")

    assert rewrite(path) == 1
    rewritten = path.read_text(encoding="utf-8")
    assert "if 'phoenix'" not in rewritten
    assert "ctrl.SetItem(0, 1, 'x')" in rewritten


def test_rewrite_preserves_distinct_branches(tmp_path: Path):
    source = """\
import wx

def fill(ctrl):
    if 'phoenix' in wx.PlatformInfo:
        ctrl.SetItem(0, 1, 'x')
    else:
        ctrl.SetStringItem(0, 1, 'x')
"""
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")

    assert rewrite(path) == 0
    assert path.read_text(encoding="utf-8") == source
