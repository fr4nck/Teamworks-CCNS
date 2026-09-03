from pathlib import Path


EXPOSED = (
    "teamworks/Ctrl/CTRL_Personnes.py",
    "teamworks/Ctrl/CTRL_Recrutement.py",
    "teamworks/Ctrl/CTRL_Recrutement_navigation.py",
    "teamworks/Ctrl/CTRL_Page_presences.py",
    "teamworks/Ctrl/CTRL_Page_frais.py",
    "teamworks/Ctrl/CTRL_Page_generalites.py",
    "teamworks/Dlg/DLG_Application_modele.py",
    "teamworks/Dlg/DLG_Saisie_coords.py",
    "teamworks/Dlg/DLG_Publiposteur.py",
    "teamworks/Dlg/DLG_CCNS_audit.py",
    "teamworks/Dlg/DLG_CCNS_audit_list.py",
)


def test_ecrans_exposes_ne_reintroduisent_pas_de_bitmapbutton_brut():
    for path in EXPOSED:
        source = Path(path).read_text(encoding="utf-8")
        assert "wx.BitmapButton(" not in source, path


def test_ecrans_exposes_ne_reintroduisent_pas_de_togglebutton_brut():
    for path in EXPOSED:
        source = Path(path).read_text(encoding="utf-8")
        assert "wx.ToggleButton(" not in source, path
