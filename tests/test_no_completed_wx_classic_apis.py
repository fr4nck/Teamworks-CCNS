import ast
import io
import tokenize
from pathlib import Path


ROOT = Path("teamworks")
ADAPTER = ROOT / "Utils" / "UTILS_Adaptations.py"
FORBIDDEN_ATTRIBUTES = {
    "InsertStringItem",
    "SetStringItem",
    "SetPyData",
    "GetPyData",
    "EmptyImage",
    "EmptyBitmap",
    "BitmapFromImage",
    "ImageFromStream",
    "PySimpleApp",
    "GetClientSizeTuple",
    "SetToolTipString",
    "NewId",
    "MAXSIZE",
}


def read_source(path: Path) -> str:
    raw = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    return raw.decode(encoding)


def iter_attribute_calls(path: Path):
    try:
        tree = ast.parse(read_source(path))
    except (SyntaxError, UnicodeDecodeError):
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            yield node.func.attr, node.lineno
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "six"
            and node.attr == "MAXSIZE"
        ):
            yield node.attr, node.lineno


def test_completed_wx_classic_apis_do_not_return():
    violations = []

    for path in sorted(ROOT.rglob("*.py")):
        for attribute, line_number in iter_attribute_calls(path) or ():
            if attribute in FORBIDDEN_ATTRIBUTES:
                violations.append(f"{path}:{line_number}: {attribute}")

    assert not violations, "Legacy wx APIs found:\n" + "\n".join(violations)


def test_appendmenu_calls_are_gone_outside_compatibility_adapter():
    violations = []

    for path in sorted(ROOT.rglob("*.py")):
        if path == ADAPTER:
            continue
        for attribute, line_number in iter_attribute_calls(path) or ():
            if attribute == "AppendMenu":
                violations.append(f"{path}:{line_number}")

    assert not violations, "AppendMenu calls found:\n" + "\n".join(violations)
