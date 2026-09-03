from pathlib import Path


GENERALITES = Path("teamworks/Ctrl/CTRL_Page_generalites.py")
RESPONSIVE = Path("teamworks/Utils/UTILS_Responsive.py")
INTERNATIONAL = Path("teamworks/Utils/UTILS_Generalites_international.py")


def test_socles_responsive_et_international_sont_disponibles():
    responsive = RESPONSIVE.read_text(encoding="utf-8")
    international = INTERNATIONAL.read_text(encoding="utf-8")
    assert "def form_column_count" in responsive
    assert "def logical_width" in responsive
    assert "def normalise_code_postal" in international
    assert "def nir_lieu_compatible" in international


def test_generalites_conserve_les_sections_metier_attendues():
    source = GENERALITES.read_text(encoding="utf-8")
    for titre in ("Identité", "Situation sociale", "Adresse", "Coordonnées", "Mémo"):
        assert 'titre=_(u"%s")' % titre in source
    assert "adresse_resid" in source
    assert "cp_resid" in source
    assert "ville_resid" in source
    assert "coordonnees" in source
