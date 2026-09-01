import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Teamworks.py"
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Demarches_rh.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path), filename=str(path))


def _find_method(tree, class_name, method_name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


def _imported_modules(path):
    modules = []
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


def test_shell_exposes_dashboard_without_touching_historical_core():
    source = _source(SHELL)

    assert 'self.dictInfosMenu["demarches_rh"]' in source
    assert "Démarches RH" in source
    assert "class MyFrame(_BaseMyFrame):" in source
    assert "CORE.MyFrame = MyFrame" in source


def test_dashboard_dialog_is_imported_only_from_explicit_menu_handler():
    tree = _tree(SHELL)
    handler = _find_method(tree, "MyFrame", "On_demarches_rh")

    lazy_imports = [
        alias.name
        for node in ast.walk(handler)
        if isinstance(node, ast.ImportFrom) and node.module == "Dlg"
        for alias in node.names
    ]
    assert "DLG_Demarches_rh" in lazy_imports

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "Dlg":
            assert all(alias.name != "DLG_Demarches_rh" for alias in node.names)


def test_dashboard_dialog_does_not_choose_persistence_or_external_transport():
    imported = _imported_modules(DIALOG)
    for forbidden in (
        "GestionDB",
        "sqlite3",
        "infrastructure.persistence",
        "requests",
        "urllib",
        "webbrowser",
        "socket",
        "subprocess",
    ):
        assert all(
            module != forbidden and not module.startswith(forbidden + ".")
            for module in imported
        )


def test_dashboard_dialog_is_strictly_read_only():
    tree = _tree(DIALOG)
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    for forbidden in (
        "save_case",
        "append_event",
        "transition_to",
        "with_exchange_status",
        "record_manual_status",
        "save_profile",
        "save_employee_protection",
        "delete_profile",
    ):
        assert forbidden not in called_attributes

    source = _source(DIALOG)
    assert "HrCaseDashboardRuntimeFactory" in source
    assert "_runtime.build(as_of=as_of)" in source
    assert "structure_ref" not in source


def test_dashboard_ui_keeps_business_and_technical_statuses_distinct():
    source = _source(DIALOG)

    assert "_STATUS_LABELS" in source
    assert "_EXCHANGE_LABELS" in source
    assert "row.business_attention" in source
    assert "row.technical_attention" in source
    assert "Échecs techniques" in source
    assert "Anomalies" in source
