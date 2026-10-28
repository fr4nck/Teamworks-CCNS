"""Qt must never bring a graphical toolkit into the shared engine."""

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_UI_MODULES = {"wx", "wxPython", "PySide6", "PyQt5", "PyQt6", "qtpy"}


def _forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules = (node.module or "",)
        else:
            continue
        for module in modules:
            if module.split(".", 1)[0] in FORBIDDEN_UI_MODULES:
                imports.append(f"{path.relative_to(ROOT)}:{node.lineno}: {module}")
    return imports


@pytest.mark.parametrize("directory", ("application", "domain", "infrastructure"))
def test_shared_engine_never_imports_ui_toolkits(directory: str) -> None:
    source = ROOT / directory
    files = sorted(source.rglob("*.py"))
    assert files, f"Missing source: {source}"
    problems = [item for path in files for item in _forbidden_imports(path)]
    assert not problems, "UI imports found in shared engine:\n" + "\n".join(problems)


@pytest.mark.parametrize(
    "path", ("teamworks/GestionDB.py", "teamworks/Utils/UTILS_Fichiers.py")
)
def test_qt_legacy_persistence_bridge_is_headless(path: str) -> None:
    problems = _forbidden_imports(ROOT / path)
    assert not problems, "GUI import from legacy persistence: " + ", ".join(problems)


def test_qt_legacy_bridge_never_imports_gui_configuration_helpers() -> None:
    source = (ROOT / "teamworks/Utils/UTILS_Fichiers.py").read_text(encoding="utf-8")
    assert "UTILS_Customize" not in source
    database = (ROOT / "teamworks/GestionDB.py").read_text(encoding="utf-8")
    assert "UTILS_Config" not in database
    assert "read_current_database_name" in database


def test_qt_legacy_source_syntax_compiles() -> None:
    for name in ("teamworks/GestionDB.py", "teamworks/Utils/UTILS_Fichiers.py"):
        source = ROOT / name
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
