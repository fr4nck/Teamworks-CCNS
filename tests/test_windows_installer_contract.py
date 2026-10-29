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


def test_installer_ne_touche_pas_aux_bases_et_ne_modifie_que_customize_ini():
    text = INSTALLER.read_text(encoding="utf-8")
    lower = text.lower()
    for token in (
        "sqlite3",
        "mysql",
        "[dirs]",
        "[registry]",
        "deleteafterinstall",
        "{localappdata}",
        "{commonappdata}",
        "%programdata%",
    ):
        assert token not in lower

    assert "{userappdata}\\teamworks\\Customize.ini" in text
    assert "SetIniString(" in text
    assert "'historique'" in text
    assert "'afficher_ressources'" in text
    assert ".dat" not in _section(text, "Code").lower()


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
    assert "(github.ref == 'refs/heads/master' || github.ref == 'refs/heads/wx/master') && contains(github.event.head_commit.message, '[windows]')" in build
    assert "Teamworks-CCNS-*-windows-x64-setup.exe" in build
    assert "$icon = (Resolve-Path 'teamworks/Static/Images/Branding/Teamworks-CCNS.ico').Path" in build
    assert "'--icon', $icon" in build


def test_packaging_includes_complete_licence_at_executable_root():
    """La RC6 copiait Versions.txt mais oubliait Licence.txt : crash à propos."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'Copy-Item teamworks/Licence.txt "$package/Licence.txt" -Force' in workflow
    assert "'Licence.txt'," in workflow
    assert 'Get-FileHash "$package/Licence.txt" -Algorithm SHA256' in workflow
    assert "Join-Path $installDir 'Licence.txt'" in workflow
    portable_test = (
        ROOT / "scripts" / "test_windows_portable_isolated.ps1"
    ).read_text(encoding="utf-8-sig")
    assert '"Licence.txt",' in portable_test
    assert (ROOT / "teamworks" / "Licence.txt").stat().st_size > 1000
