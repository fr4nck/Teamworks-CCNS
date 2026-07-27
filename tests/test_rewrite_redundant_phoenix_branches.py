import importlib.util
from pathlib import Path


MODULE_PATH = Path("tools/rewrite_redundant_phoenix_branches.py")
SPEC = importlib.util.spec_from_file_location("rewrite_redundant_phoenix_branches", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
rewrite = MODULE.rewrite


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
