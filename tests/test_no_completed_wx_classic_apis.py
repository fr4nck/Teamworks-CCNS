from pathlib import Path


ROOT = Path("teamworks")
FORBIDDEN = (
    ".InsertStringItem(",
    ".SetStringItem(",
    ".SetPyData(",
    ".GetPyData(",
    "wx.EmptyImage(",
    "wx.EmptyBitmap(",
    "wx.BitmapFromImage(",
    "wx.ImageFromStream(",
    "wx.PySimpleApp(",
    ".GetClientSizeTuple(",
    ".SetToolTipString(",
    "wx.NewId()",
    "six.MAXSIZE",
)


def test_completed_wx_classic_apis_do_not_return():
    violations = []
    for path in sorted(ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8", errors="ignore")
        for token in FORBIDDEN:
            if token in source:
                violations.append(f"{path}: {token}")

    assert not violations, "Legacy wx APIs found:\n" + "\n".join(violations)


def test_appendmenu_calls_are_gone_outside_compatibility_adapter():
    violations = []
    adapter = ROOT / "Utils" / "UTILS_Adaptations.py"
    for path in sorted(ROOT.rglob("*.py")):
        if path == adapter:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if ".AppendMenu(" in source:
            violations.append(str(path))

    assert not violations, "AppendMenu calls found:\n" + "\n".join(violations)
