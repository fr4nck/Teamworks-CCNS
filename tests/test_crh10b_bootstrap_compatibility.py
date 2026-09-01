from pathlib import Path


BOOTSTRAP = Path("application/bootstrap/__init__.py")
SHELL = Path("teamworks/Teamworks.py")


def test_crh10b_preserves_employee_protection_bootstrap_exports():
    source = BOOTSTRAP.read_text(encoding="utf-8")

    for public_name in (
        "EmployeeProtectionActionsRuntime",
        "EmployeeProtectionActionsRuntimeFactory",
        "EmployeeProtectionOrganizationOption",
        "EmployeeProtectionSummaryRuntime",
        "EmployeeProtectionSummaryRuntimeFactory",
    ):
        assert public_name in source


def test_crh10b_keeps_shell_public_frame_and_app_contracts():
    source = SHELL.read_text(encoding="utf-8")

    assert "class MyFrame(_BaseMyFrame):" in source
    assert "CORE.MyFrame = MyFrame" in source
    assert "MyApp = CORE.MyApp" in source
    assert "SaisiePassword = CORE.SaisiePassword" in source
    assert "Redirect = CORE.Redirect" in source
