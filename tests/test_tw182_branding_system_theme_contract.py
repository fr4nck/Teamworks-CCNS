from __future__ import annotations

import ast
from pathlib import Path


THEME_PATH = Path("teamworks/Utils/UTILS_Theme.py")
BRANDING_PATH = Path("teamworks/Utils/UTILS_Branding.py")
PATHS_PATH = Path("teamworks/Chemins.py")


def _functions(path: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }


def test_system_theme_reads_windows_application_preference() -> None:
    source = THEME_PATH.read_text(encoding="utf-8")
    functions = _functions(THEME_PATH)

    assert "_windows_apps_dark" in functions
    assert "_system_dark_from_os" in functions
    assert "is_dark_theme" in functions
    assert 'AppsUseLightTheme' in source
    assert 'winreg.HKEY_CURRENT_USER' in source
    assert 'return _system_dark_from_os()' in source


def test_native_dark_mode_is_windows_only() -> None:
    source = THEME_PATH.read_text(encoding="utf-8")

    assert 'if sys.platform == "win32":' in source
    assert 'wx.SystemOptions.SetOption("msw.dark-mode", 2 if dark else 0)' in source


def test_branding_override_remains_limited_to_runtime_brand_assets() -> None:
    source = PATHS_PATH.read_text(encoding="utf-8")

    assert 'Images/Special/Logo_splash.png' in source
    assert 'Images/16x16/Logo.png' in source
    assert 'from Utils import UTILS_Branding' in source
    assert 'UTILS_Branding.GetRuntimeAssetOverride(normalized)' in source


def test_organisation_logo_accepts_only_supported_image_formats() -> None:
    source = BRANDING_PATH.read_text(encoding="utf-8")

    assert 'SUPPORTED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}' in source
    assert 'APPLICATION_NAME = "Teamworks CCNS"' in source
    assert 'logo_association' in source
