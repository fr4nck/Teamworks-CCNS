from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_residence_city_and_address_are_not_blocked_by_legacy_autocomplete():
    source = _source("teamworks/Utils/UTILS_Generalites_091f.py")

    assert '"text_adresse", "text_cp", "text_ville", "text_ville_naiss"' in source
    assert "control.Enable(True)" in source
    assert "control.SetEditable(True)" in source
    assert "Unbind(event, handler=handler)" in source
    assert "panel.text_ville.Bind(wx.EVT_TEXT, panel.OnTextVille)" in source
    assert "panel.text_cp.Bind(wx.EVT_TEXT, panel.OnTextCP)" in source


def test_foreign_birth_city_bypasses_french_city_database_validation():
    source = _source("teamworks/Utils/UTILS_Generalites_091f.py")

    assert "def _country_is_france(panel):" in source
    assert "if _country_is_france(panel):" in source
    assert "panel.Ville_KillFocus1(event)" in source
    assert "panel.Code_KillFocus1(event)" in source
    assert "panel.MaJ_DateNaiss_Fiche()" in source


def test_theme_installs_generalites_fix_before_first_show():
    source = _source("teamworks/Utils/UTILS_Theme.py")

    assert 'window.GetName() == "panel_generalites"' in source
    assert "UTILS_Generalites_091f.stabilise(window)" in source
    apply = source.split("def apply_to_window", 1)[1].split("def _install_preferences_menu", 1)[0]
    assert "_apply_screen_specific_fixes(window)" in apply
