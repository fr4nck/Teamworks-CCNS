from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "recipe_qt_contracts_mysql.py"
LAUNCHER = ROOT / "tools" / "run_rail_a_contracts_mysql_windows.cmd"


def test_rail_a_mysql_recipe_refuses_sqlite_and_requires_windows():
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'os.name != "nt"' in source
    assert 'getattr(db, "isNetwork", False) is not True' in source
    assert "TEAMWORKS_RAIL_A_BACKEND:MYSQL" in source
    assert "TEAMWORKS_RAIL_A_MYSQL_READY" in source
    assert "TEAMWORKS_RAIL_A_MYSQL_FAILED" in source


def test_rail_a_mysql_recipe_uses_contract_service_and_production_adapter():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "GestionDbContractWriteAdapter" in source
    assert "create_contract(port" in source
    assert "update_contract(port" in source
    assert "delete_contract(" in source
    assert "port.contract_exists(created_id)" in source
    assert "gross_monthly_salary=Decimal(\"9999.01\")" in source


def test_rail_a_windows_launcher_executes_the_strict_mysql_recipe():
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "recipe_qt_contracts_mysql.py" in source
    assert "stop-gate Rail A Windows/MySQL" in source
