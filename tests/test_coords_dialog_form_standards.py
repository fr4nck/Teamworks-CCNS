from pathlib import Path


SOURCE = Path("teamworks/Dlg/DLG_Saisie_coords.py")
STYLES = Path("teamworks/Utils/UTILS_Styles.py")
GENERALITES = Path("teamworks/Ctrl/CTRL_Page_generalites.py")


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


def test_short_coords_dialog_is_bounded_to_its_content():
    source = _read(SOURCE)
    assert "style=wx.DEFAULT_DIALOG_STYLE)" in source
    assert "wx.RESIZE_BORDER" not in source
    assert "self._fit_to_content()" in source
    assert "self.Fit()" in source
    assert "self.SetMaxSize((largeur, hauteur))" in source


def test_compact_form_window_profile_remains_available_for_other_forms():
    source = _read(STYLES)
    assert '"form_compact"' in source
    assert '"min_size": (520, 320)' in source


def test_generalites_is_the_primary_home_for_contact_details():
    source = _read(GENERALITES)
    assert 'titre=_(u"Adresse postale")' in source
    assert 'titre=_(u"Téléphones et e-mails")' in source
    assert 'self.list_ctrl_coords = ListCtrlCoords(' in source
    assert 'self.button_coords_ajout' in source
    assert 'self.button_coords_modif' in source
    assert 'self.button_coords_suppr' in source
