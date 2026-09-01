import ast
from pathlib import Path


SERVICE = Path("application/services/hr_connections/hr_case_creation.py")
RUNTIME = Path("application/bootstrap/hr_case_creation_factory.py")
ADAPTER = Path("infrastructure/persistence/teamworks_hr_case_creation_repository.py")


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


def test_creation_service_is_ui_persistence_and_transport_agnostic():
    imported = _imports(SERVICE)
    for forbidden in (
        "wx",
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


def test_creation_service_does_not_encode_legal_catalog_or_automatic_transport():
    source = _source(SERVICE)

    for forbidden in (
        "DPAE",
        "DSN",
        "France Travail",
        "Net-entreprises",
        "api.",
        "submit(",
        "send(",
        "upload(",
        "with_exchange_status",
    ):
        assert forbidden not in source
    assert "HrCase.create(" in source
    assert "HrEventKind.CASE_CREATED" in source


def test_creation_adapter_reuses_crh22_schema_without_ddl():
    source = _source(ADAPTER)

    assert "TeamworksHrCasesRepository" in source
    assert "CREATE TABLE" not in source
    assert "ALTER TABLE" not in source
    assert "DROP TABLE" not in source
    assert "create_case_with_event" in source
    assert "_commit(db)" in source
    assert "_rollback(db)" in source


def test_creation_adapter_locks_initial_business_state_and_audit_kind():
    source = _source(ADAPTER)

    assert "case.status is not HrCaseStatus.TODO" in source
    assert "event.kind is not HrEventKind.CASE_CREATED" in source
    assert "event.target_ref != case.case_id" in source
    assert "with_exchange_status" not in source
    assert "exchange_status =" not in source


def test_creation_runtime_hides_structure_identity_and_db_from_callers():
    source = _source(RUNTIME)
    tree = ast.parse(source, filename=str(RUNTIME))
    runtime = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "HrCaseCreationRuntime"
    )
    fields = {
        node.target.id
        for node in runtime.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    imported = _imports(RUNTIME)

    assert "_structure_ref" in fields
    assert "structure_ref" not in fields
    assert "repository" not in fields
    assert all(
        module != "GestionDB" and not module.startswith("GestionDB.")
        for module in imported
    )
    assert "def create(" in source
