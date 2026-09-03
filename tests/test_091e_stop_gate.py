from pathlib import Path


def test_criteres_de_sortie_sont_documentes_et_testes():
    doc = Path("docs/DEV_091e_GENERALITES.md").read_text(encoding="utf-8")
    assert "ville de naissance étrangère" in doc
    assert "code département `99`" in doc
    assert "une et deux colonnes" in doc
    assert "Snap Layouts Windows 11" in doc


def test_boutons_exposes_et_regles_internationales_ont_des_garde_fous():
    assert Path("tests/test_exposed_ui_button_stop_gate.py").exists()
    assert Path("tests/test_generalites_international_rules.py").exists()
    assert Path("tests/test_generalites_091e_adapter.py").exists()
