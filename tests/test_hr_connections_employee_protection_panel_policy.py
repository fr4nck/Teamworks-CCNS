from pathlib import Path


PANEL_PATH = Path("teamworks/Ctrl/CTRL_Page_protection_sociale.py")


def _source():
    return PANEL_PATH.read_text(encoding="utf-8")


def test_employee_protection_panel_exists_and_consumes_summary_projection():
    source = _source()

    assert "class Panel(wx.Panel)" in source
    assert "EmployeeProtectionSummary" in source
    assert "def SetSummary" in source
    assert "def SetUnavailable" in source
    assert "organization_configured" in source
    assert "payroll_relevant" in source


def test_employee_protection_panel_does_not_choose_a_backend_or_network_transport():
    source = _source()

    forbidden = (
        "sqlite3",
        "GestionDB",
        "SqliteEmployeeProtectionRepository",
        "requests",
        "urllib",
        "webbrowser",
        "subprocess",
        "socket",
    )
    for token in forbidden:
        assert token not in source


def test_employee_protection_panel_does_not_claim_automatic_legal_compliance():
    source = _source().lower()

    forbidden_claims = (
        "est conforme",
        "non conforme",
        "couverture obligatoire",
        "dispense valide juridiquement",
        "conformité automatique",
    )
    for claim in forbidden_claims:
        assert claim not in source


def test_employee_protection_panel_uses_semantic_theme_and_scale_contracts():
    source = _source()

    assert 'GetToken("surface")' in source
    assert 'GetToken("surface_container_lowest")' in source
    assert 'GetToken("on_surface")' in source
    assert 'GetToken("warning")' in source
    assert "UTILS_Styles.Scale(" in source
    assert "wx.Colour(" not in source
