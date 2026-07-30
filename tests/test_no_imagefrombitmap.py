import ast
from pathlib import Path


def _read_source(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8",):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def test_no_wx_imagefrombitmap_remains() -> None:
    """Empêche la réintroduction de l'ancien constructeur wxPython Classic."""
    offenders: list[str] = []

    for path in Path("teamworks").rglob("*.py"):
        tree = ast.parse(_read_source(path), filename=str(path))
        for node in ast.walk(tree):
            func = node.func if isinstance(node, ast.Call) else None
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "ImageFromBitmap"
                and isinstance(func.value, ast.Name)
                and func.value.id == "wx"
            ):
                offenders.append(f"{path}:{node.lineno}")

    assert offenders == [], f"wx.ImageFromBitmap reste présent dans : {offenders}"
