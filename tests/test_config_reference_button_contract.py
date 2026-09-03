from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "teamworks" / "Dlg" / "DLG_Config_classifications.py",
    ROOT / "teamworks" / "Dlg" / "DLG_Config_types_diplomes.py",
)


def test_referentiels_traitent_leurs_boutons_par_le_contrat_commun():
    for path in FILES:
        source = path.read_text(encoding="utf-8")
        assert "wx.BitmapButton(" not in source
        assert "wx.Button(" not in source
        assert "CTRL_Bouton_image.CTRL(" in source
        assert 'role="danger"' in source
        assert 'role="quiet"' in source
