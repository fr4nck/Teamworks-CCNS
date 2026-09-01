import ast
from pathlib import Path


DIALOG = Path("teamworks/Dlg/DLG_Demarches_rh_historique.py")
SERVICE = Path("application/services/hr_connections/hr_case_history.py")
RUNTIME = Path("application/bootstrap/hr_case_history_factory.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _imports(path):
    modules = []
    tree = ast.parse(_source(path), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


def test_history_dialog_does_not_choose_persistence_or_transport():
    imported = _imports(DIALOG)

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


def test_history_dialog_is_strictly_read_only():
    source = _source(DIALOG)

    assert "HrCaseHistoryRuntimeFactory" in source
    assert "self._runtime.build(case_id=case_id)" in source
    for forbidden in (
        "save_case(",
        "append_event(",
        "transition(",
        "transition_to(",
        "persist_case_transition(",
        "with_exchange_status(",
        "DeleteItem(",
    ):
        assert forbidden not in source


def test_history_service_is_ui_and_persistence_agnostic():
    source = _source(SERVICE)

    for forbidden in (
        "import wx",
        "from wx",
        "GestionDB",
        "sqlite3",
        "infrastructure.persistence",
    ):
        assert forbidden not in source
    assert "HrEventTargetKind.CASE" in source
    assert "reverse=True" in source


def test_history_runtime_hides_structure_identity():
    source = _source(RUNTIME)
    tree = ast.parse(source, filename=str(RUNTIME))
    runtime = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "HrCaseHistoryRuntime"
    )
    fields = {
        node.target.id
        for node in runtime.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }

    assert "_structure_ref" in fields
    assert "structure_ref" not in fields
    assert "repository" not in fields
    assert "def build(self, *, case_id: str)" in source


def test_history_ui_preserves_timezone_and_shows_audit_metadata():
    source = _source(DIALOG)

    assert 'strftime("%d/%m/%Y %H:%M %z")' in source
    assert "Acteur" in source
    assert "Source" in source
    assert "Statut précédent" in source
    assert "Nouveau statut" in source
