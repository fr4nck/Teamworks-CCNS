import ast
from pathlib import Path


FACTORY = Path("application/bootstrap/hr_case_dashboard_factory.py")


def _source():
    return FACTORY.read_text(encoding="utf-8")


def test_dashboard_runtime_factory_remains_ui_agnostic():
    source = _source()

    for forbidden in (
        "import wx",
        "from wx",
        "from Dlg",
        "from Ctrl",
        "webbrowser",
        "requests",
        "urllib",
        "socket",
        "subprocess",
    ):
        assert forbidden not in source


def test_dashboard_runtime_does_not_expose_repository_or_structure_identity_publicly():
    tree = ast.parse(_source(), filename=str(FACTORY))
    runtime = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "HrCaseDashboardRuntime"
    )
    fields = {
        node.target.id
        for node in runtime.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }

    assert "structure_ref" not in fields
    assert "repository" not in fields
    assert "case_repository" not in fields
    assert "profile_repository" not in fields
    assert "_structure_ref" in fields
    assert "_service" in fields


def test_dashboard_runtime_requires_caller_supplied_date():
    source = _source()

    assert "date.today" not in source
    assert "datetime.now" not in source
    assert "def build(self, *, as_of: date)" in source


def test_dashboard_runtime_is_read_only_composition():
    source = _source()

    assert "TeamworksStructureIdentityRepository" in source
    assert "TeamworksHrCasesRepository" in source
    assert "TeamworksHrConnectionsRepository" in source
    assert "HrCaseDashboardService" in source

    for forbidden_action in (
        ".save_case(",
        ".append_event(",
        ".transition_to(",
        ".record_manual_status(",
        ".save_profile(",
        ".save_employee_protection(",
    ):
        assert forbidden_action not in source
