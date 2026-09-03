from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "teamworks" / "Dlg" / "DLG_CCNS_seed.py"
AUDIT = ROOT / "teamworks" / "Dlg" / "DLG_CCNS_audit.py"
AUDIT_LIST = ROOT / "teamworks" / "Dlg" / "DLG_CCNS_audit_list.py"
SALARY_SUMMARY = ROOT / "teamworks" / "Dlg" / "DLG_CCNS_employee_salary_summary.py"
SALARY_DETAIL = ROOT / "teamworks" / "Dlg" / "DLG_CCNS_salary_control_detail.py"
GADGET = ROOT / "teamworks" / "Ctrl" / "CTRL_Gadget_CCNS.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_ccns_seed_uses_common_button_contract():
    source = _source(SEED)
    assert "wx.Button(" not in source
    assert source.count("CTRL_Bouton_image.CTRL(") == 2
    assert 'role="primary"' in source
    assert 'role="quiet"' in source


def test_ccns_audit_uses_common_button_contract():
    source = _source(AUDIT)
    assert "wx.Button(" not in source
    assert source.count("CTRL_Bouton_image.CTRL(") == 2
    assert 'texte="Lancer l\'audit"' in source
    assert 'role="primary"' in source
    assert 'role="quiet"' in source
    assert "UTILS_Styles.Scale(760)" in source
    assert "UTILS_Styles.Scale(500)" in source


def test_ccns_detailed_audit_uses_common_button_contract():
    source = _source(AUDIT_LIST)
    assert "wx.Button(" not in source
    assert source.count("CTRL_Bouton_image.CTRL(") == 12
    assert 'texte="Lancer l\'audit", role="primary"' in source
    assert 'texte="Appliquer", role="primary"' in source
    assert 'texte="Réinitialiser", role="quiet"' in source
    assert 'texte="Fermer", role="quiet"' in source


def test_ccns_employee_salary_summary_uses_common_button_contract():
    source = _source(SALARY_SUMMARY)
    assert "wx.Button(" not in source
    assert source.count("CTRL_Bouton_image.CTRL(") == 2
    assert 'texte="Détail salarial"' in source
    assert 'texte="Fermer", role="quiet"' in source


def test_ccns_salary_detail_uses_common_button_contract():
    source = _source(SALARY_DETAIL)
    assert "wx.Button(" not in source
    assert source.count("CTRL_Bouton_image.CTRL(") == 1
    assert 'texte="Fermer", role="quiet"' in source


def test_ccns_home_gadget_uses_common_button_contract():
    source = _source(GADGET)
    assert "wx.Button(" not in source
    assert source.count("CTRL_Bouton_image.CTRL(") == 2
    assert 'texte=u"Actualiser"' in source
    assert 'texte=u"Ouvrir le contrat"' in source
