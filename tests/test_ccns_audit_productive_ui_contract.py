from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_CCNS_audit_list.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_ccns_audit_uses_semantic_workspace_profile_without_raw_window_sizes():
    source = _source()
    assert 'UTILS_Styles.ApplyWindowProfile(self, "workspace", centre=False)' in source
    assert "self.SetSize((1280, 820))" not in source
    assert "self.SetMinSize((980, 700))" not in source
    assert 'UTILS_Styles.ApplyWindowProfile(dlg, "wide")' in source
    assert "dlg.SetSize((980, 720))" not in source


def test_ccns_audit_short_filters_use_semantic_field_roles():
    source = _source()
    expected_roles = {
        "self.ctrl_group": "FIELD_CODE",
        "self.ctrl_type": "FIELD_NAME",
        "self.ctrl_min_salary": "FIELD_MONEY",
        "self.ctrl_max_salary": "FIELD_MONEY",
        "self.ctrl_salary_status": "FIELD_NAME",
        "self.ctrl_minimum_source": "FIELD_NAME",
        "self.ctrl_salary_sort": "FIELD_NAME",
        "self.ctrl_sort_direction": "FIELD_NAME",
    }
    for control, role in expected_roles.items():
        assert f"UTILS_Styles.ApplyFieldRole({control}, UTILS_Styles.{role})" in source


def test_ccns_audit_does_not_use_colour_as_the_only_severity_signal():
    source = _source()
    assert "Gravité affichée en texte et en couleur" in source
    assert "Bloquant (rouge)" in source
    assert "À revoir (jaune)" in source
    assert "OK (vert)" in source
