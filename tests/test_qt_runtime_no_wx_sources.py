"""Static safety gate: the Qt-specific UI must not import wx at any depth.

The packaging smoke still checks the frozen runtime separately. This audit
does not pretend to prove parity of every inherited Teamworks workflow.
"""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QT_SOURCE = ROOT / "poc" / "qt-theme"
FORBIDDEN = {"wx", "wxPython"}


def test_qt_python_modules_contain_no_static_wx_import_or_dynamic_import_literal():
    files = sorted(QT_SOURCE.rglob("*.py"))
    assert len(files) >= 30
    problems = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "__import__"
            ):
                names = [
                    arg.value for arg in node.args[:1]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                ]
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            ):
                names = [
                    arg.value for arg in node.args[:1]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                ]
            for name in names:
                if name.split(".", 1)[0] in FORBIDDEN:
                    problems.append(f"{path.relative_to(ROOT)}:{node.lineno}: {name}")
    assert not problems, "wx import in Qt UI:\n" + "\n".join(problems)


def test_qualifying_qt_runtime_excludes_wx_and_does_not_depend_on_wx_buttons():
    requirements = (ROOT / "requirements" / "qt-vanilla-0.1.txt").read_text(encoding="utf-8")
    packages = [
        line.split("#", 1)[0].strip().lower()
        for line in requirements.splitlines()
        if line.split("#", 1)[0].strip()
    ]
    build = (ROOT / "scripts" / "build_qt_vanilla_windows.ps1").read_text(encoding="utf-8")
    assert any(line.startswith("pyside6") for line in packages)
    assert not any(line.startswith(("wxpython", "wx==", "wx>=", "wx<=")) for line in packages)
    assert '"--exclude-module", "wx"' in build
    assert '"--exclude-module", "wxPython"' in build
    editor = (QT_SOURCE / "person_editor.py").read_text(encoding="utf-8")
    assert "from PySide6.QtWidgets import" in editor
    assert "validate_person_details" in editor
