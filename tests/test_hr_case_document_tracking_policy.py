import ast
from pathlib import Path


DOMAIN = Path("domain/hr_connections/case_documents.py")
SERVICE = Path("application/services/hr_connections/hr_case_documents.py")
RUNTIME = Path("application/bootstrap/hr_case_documents_factory.py")
ADAPTER = Path("infrastructure/persistence/teamworks_hr_case_document_repository.py")


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


def test_domain_and_service_are_ui_persistence_and_transport_agnostic():
    for path in (DOMAIN, SERVICE):
        imported = _imports(path)
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


def test_document_projection_never_stores_binary_payload_or_local_path():
    source = _source(ADAPTER)
    lowered = source.lower()

    for forbidden in (
        " blob",
        "mediumblob",
        "longblob",
        "file_path",
        "filepath",
        "local_path",
        "binary_content",
        "document_content",
        "payload",
    ):
        assert forbidden not in lowered
    assert "artifact_ref VARCHAR(240)" in source


def test_document_projection_is_additive_and_withdrawal_is_not_a_delete():
    source = _source(ADAPTER)

    assert "CREATE TABLE IF NOT EXISTS tw_hr_case_document_receipts" in source
    assert "CREATE INDEX" in source
    assert "ALTER TABLE" not in source
    assert "DROP TABLE" not in source
    assert "DELETE FROM tw_hr_case_document_receipts" not in source
    assert "ON CONFLICT" not in source
    assert "INSERT OR REPLACE" not in source
    assert "REPLACE INTO" not in source
    assert "FOREIGN KEY" not in source


def test_document_changes_are_audited_on_the_case_history():
    source = _source(SERVICE)

    assert "HrEventKind.DOCUMENT_ADDED" in source
    assert "HrEventKind.DOCUMENT_REMOVED" in source
    assert "target_kind=HrEventTargetKind.CASE" in source
    assert 'key="document_code"' in source
    assert "persist_receipt_change" in source


def test_service_does_not_create_or_change_expected_document_requirements():
    source = _source(SERVICE)

    assert "ExpectedDocument.create(" not in source
    assert "expected_documents=" not in source
    assert "save_case(" not in source
    assert "with_exchange_status" not in source
    assert "exchange_status" not in source


def test_runtime_hides_structure_identity_and_repository_from_public_methods():
    source = _source(RUNTIME)
    tree = ast.parse(source, filename=str(RUNTIME))
    runtime = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "HrCaseDocumentTrackingRuntime"
    )
    fields = {
        node.target.id
        for node in runtime.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }

    assert "_structure_ref" in fields
    assert "structure_ref" not in fields
    assert "repository" not in fields
    assert "GestionDB" not in _imports(RUNTIME)
    assert "def build_checklist(" in source
    assert "def record_received(" in source
    assert "def withdraw_received(" in source
