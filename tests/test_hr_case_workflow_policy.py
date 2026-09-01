import ast
from pathlib import Path


SERVICE = Path("application/services/hr_connections/hr_case_workflow.py")
REPOSITORY = Path(
    "infrastructure/persistence/teamworks_hr_case_workflow_repository.py"
)
RUNTIME = Path("application/bootstrap/hr_case_workflow_factory.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _runtime_class():
    tree = ast.parse(_source(RUNTIME), filename=str(RUNTIME))
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "HrCaseWorkflowRuntime"
    )


def test_workflow_service_stays_ui_sql_and_transport_agnostic():
    source = _source(SERVICE)

    for forbidden in (
        "import wx",
        "from wx",
        "GestionDB",
        "sqlite3",
        "infrastructure.persistence",
        "requests",
        "urllib",
        "webbrowser",
        "socket",
        "subprocess",
    ):
        assert forbidden not in source


def test_workflow_service_delegates_state_machine_to_domain():
    source = _source(SERVICE)

    assert ".can_transition_to(" in source
    assert ".transition_to(" in source
    assert "_ALLOWED_TRANSITIONS" not in source
    assert "CASE_STATUS_CHANGED" in source
    assert "from_status" in source
    assert "to_status" in source


def test_atomic_repository_reuses_crh22_schema_without_ddl():
    source = _source(REPOSITORY).upper()

    for forbidden in (
        "CREATE TABLE",
        "ALTER TABLE",
        "DROP TABLE",
        "CREATE INDEX",
        "FOREIGN KEY",
    ):
        assert forbidden not in source


def test_atomic_repository_has_no_network_or_secret_handling():
    source = _source(REPOSITORY).lower()

    for forbidden in (
        "requests",
        "urllib",
        "webbrowser",
        "socket",
        "password",
        "mot_de_passe",
        "access_token",
        "refresh_token",
        "api_key",
    ):
        assert forbidden not in source


def test_atomic_repository_requires_optimistic_concurrency_and_append_only_audit():
    source = _source(REPOSITORY)

    assert "AND status = ?" in source
    assert "AND exchange_status = ?" in source
    assert "rowcount" in source
    assert "DuplicateTeamworksHrAuditEventError" in source
    assert "INSERT INTO tw_hr_audit_events" in source
    assert "UPDATE tw_hr_audit_events" not in source
    assert "DELETE FROM tw_hr_audit_events" not in source


def test_workflow_runtime_hides_structure_identity_and_technical_exchange_axis():
    runtime = _runtime_class()
    fields = {
        node.target.id
        for node in runtime.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    public_methods = {
        node.name: node
        for node in runtime.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }

    assert "_structure_ref" in fields
    assert "structure_ref" not in fields
    assert set(public_methods) == {"available_transitions", "transition"}

    for method in public_methods.values():
        arguments = {
            argument.arg
            for argument in (
                list(method.args.posonlyargs)
                + list(method.args.args)
                + list(method.args.kwonlyargs)
            )
        }
        assert "structure_ref" not in arguments
        assert "exchange_status" not in arguments

    source = _source(RUNTIME)
    assert "with_exchange_status" not in source


def test_workflow_runtime_factory_stays_ui_and_transport_agnostic():
    source = _source(RUNTIME)

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
