from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "packaging" / "windows" / "Teamworks-CCNS.iss"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _section(text: str, name: str) -> str:
    marker = f"[{name}]"
    start = text.index(marker) + len(marker)
    tail = text[start:]
    match = re.search(r"\n\[[^\]]+\]", tail)
    if match:
        return tail[: match.start()]
    return tail


def test_installer_only_writes_application_files_to_app_dir():
    text = INSTALLER.read_text(encoding="utf-8")
    files = _section(text, "Files")
    destinations = re.findall(r'DestDir:\s*"([^"]+)"', files)
    assert destinations
    assert set(destinations) == {"{app}"}


def test_installer_does_not_manage_user_data_or_databases():
    text = INSTALLER.read_text(encoding="utf-8").lower()
    forbidden = (
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
    )
    for token in forbidden:
        assert token not in text


def test_installer_has_stable_identity_and_uninstaller():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "AppId={{4D07F1CF-3352-4CE3-8CD8-37BE85E51D28}" in text
    assert "UninstallDisplayIcon={app}\\{#AppExeName}" in text
    assert "UsePreviousAppDir=yes" in text
    assert "SetupIconFile=..\\..\\teamworks\\Static\\Images\\Branding\\Teamworks-CCNS.ico" in text


def test_windows_packages_are_not_built_on_every_commit():
    text = WORKFLOW.read_text(encoding="utf-8")
    build = text.split("  build-windows:", 1)[1]
    assert "startsWith(github.ref, 'refs/tags/v')" in build
    assert "github.event_name == 'workflow_dispatch' && inputs.build_windows" in build
    assert "github.ref == 'refs/heads/master' && contains(github.event.head_commit.message, '[windows]')" in build
    assert "Teamworks-CCNS-*-windows-x64-setup.exe" in build
    assert "'--icon', 'teamworks/Static/Images/Branding/Teamworks-CCNS.ico'" in build
