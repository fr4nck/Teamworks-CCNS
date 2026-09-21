from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "requirements" / "qt-vanilla-0.1.txt"
BUILD = ROOT / "scripts" / "build_qt_vanilla_windows.ps1"
INSTALLER = ROOT / "packaging" / "windows" / "Teamworks-CCNS-Qt.iss"
ENTRY = ROOT / "poc" / "qt-theme" / "vanilla_launcher.py"
WORKFLOW = ROOT / ".github" / "workflows" / "qt-vanilla-package.yml"


def test_qt_vanilla_runtime_requirements_do_not_install_wx():
    lines = [
        line.strip().lower()
        for line in REQ.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    text = "\n".join(lines)
    assert "pyside6" in text
    assert "mysql-connector-python" in text
    assert all(not line.startswith("wxpython") for line in lines)
    assert all(not line.startswith("wx==") for line in lines)


def test_release_entry_point_defaults_to_production():
    text = ENTRY.read_text(encoding="utf-8")
    assert 'TEAMWORKS_QT_SOURCE", "production"' in text
    assert "from launcher import main" in text


def test_build_explicitly_excludes_wx_and_creates_portable_mode():
    text = BUILD.read_text(encoding="utf-8")
    assert '"--exclude-module", "wx"' in text
    assert '"--exclude-module", "wxPython"' in text
    assert 'New-Item -ItemType Directory -Force -Path (Join-Path $portableApp "Portable")' in text
    assert "Static/Documents" in text
    assert "VANILLA_VERSION.txt" in text


def test_qt_installer_is_side_by_side_and_never_targets_user_data():
    text = INSTALLER.read_text(encoding="utf-8")
    lower = text.lower()
    assert "Teamworks-CCNS-Qt.exe" in text
    assert "DefaultDirName={autopf}\\Teamworks-CCNS-Qt" in text
    assert "CB1D45F1-67A8-4C7D-A2E2-1FA0C5D61C01" in text
    assert "4D07F1CF-3352-4CE3-8CD8-37BE85E51D28" not in text
    for forbidden in (
        "{userappdata}",
        "{localappdata}",
        "{commonappdata}",
        "%appdata%",
        "%programdata%",
        "sqlite3",
        "mysql",
        "[dirs]",
        "[registry]",
        "deleteafterinstall",
        "\\portable\\",
    ):
        assert forbidden not in lower


def test_packaging_workflow_builds_and_smokes_portable_and_installer():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "build_qt_vanilla_windows.ps1" in text
    assert "find_spec('wx') is None" in text
    assert "TEAMWORKS_QT_AUTOCLOSE_MS" in text
    assert "Teamworks-CCNS-Qt.iss" in text
    assert "unins000.exe" in text
    assert "upload-artifact@v4" in text
