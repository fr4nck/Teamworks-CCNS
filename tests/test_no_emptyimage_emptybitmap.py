import ast
from pathlib import Path


BANNED_WX_CALLS = {"EmptyBitmap", "EmptyImage"}


def _read_source(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "iso-8859-15", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def test_no_wx_emptyimage_or_emptybitmap_remains() -> None:
    offenders: list[str] = []

    for path in Path("teamworks").rglob("*.py"):
        tree = ast.parse(_read_source(path), filename=str(path))
        for node in ast.walk(tree):
            func = node.func if isinstance(node, ast.Call) else None
            if (
                isinstance(func, ast.Attribute)
                and func.attr in BANNED_WX_CALLS
                and isinstance(func.value, ast.Name)
                and func.value.id == "wx"
            ):
                offenders.append(f"{path}:{node.lineno}:{func.attr}")

    assert offenders == [], f"API wxPython Classic restantes : {offenders}"
