import json
from pathlib import Path

from tools import smoke_runtime


ROOT = Path(__file__).resolve().parents[1]


def test_smoke_diagnostic_survives_legacy_windows_console_encoding() -> None:
    diagnostic = "Chaîne historique endommagée : \ufffd"

    safe = smoke_runtime.console_safe_text(diagnostic, encoding="cp1252")

    assert safe == r"Chaîne historique endommagée : \ufffd"


def test_windows_runtime_and_portable_use_the_same_wxpython_version() -> None:
    expected = "wxPython==4.3.1"

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    windows_core = (
        ROOT / "requirements" / "python311-core.txt"
    ).read_text(encoding="utf-8").splitlines()

    assert requirements[0] == expected
    assert windows_core[1] == expected


def test_deprecated_list_item_attribute_cannot_return() -> None:
    offenders = []
    for path in (ROOT / "teamworks").rglob("*.py"):
        if "wx.ListItemAttr()" in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(ROOT).as_posix())

    assert offenders == []


def test_vscode_diagnostic_launch_uses_the_repository_entrypoint() -> None:
    launch = json.loads(
        (ROOT / ".vscode" / "launch.json").read_text(encoding="utf-8")
    )
    configuration = launch["configurations"][0]

    assert configuration["name"] == "Teamworks — mode diagnostic"
    assert configuration["program"].endswith("run_teamworks.py")
    assert configuration["console"] == "integratedTerminal"
    assert configuration["justMyCode"] is False
    assert configuration["env"]["PYTHONFAULTHANDLER"] == "1"
    assert configuration["env"]["PYTHONUNBUFFERED"] == "1"
