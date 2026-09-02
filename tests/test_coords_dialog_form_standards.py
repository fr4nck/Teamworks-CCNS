from pathlib import Path


SOURCE = Path("teamworks/Dlg/DLG_Saisie_coords.py")
STYLES = Path("teamworks/Utils/UTILS_Styles.py")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_coords_dialog_uses_semantic_form_primitives():
    source = _read(SOURCE)

    assert "CTRL_Texte.H3" in source
    assert "CTRL_Texte.BodySecondary" in source
    assert "UTILS_Styles.ApplyFieldRole(self.text_info_tel, UTILS_Styles.FIELD_PHONE)" in source
    assert "UTILS_Styles.ApplyFieldRole(self.text_info_mail, UTILS_Styles.FIELD_EMAIL)" in source
    assert "UTILS_Styles.ApplyFieldRole(self.text_intitule, UTILS_Styles.FIELD_TEXT)" in source
    assert "wx.GridSizer(rows=1, cols=4" in source
    assert "wx.EVT_TOGGLEBUTTON" in source
    assert "surface_container_low" in source
    assert "primary_container" in source


def test_compact_form_window_profile_is_available():
    source = _read(STYLES)
    assert '"form_compact"' in source
    assert '"min_size": (520, 320)' in source
