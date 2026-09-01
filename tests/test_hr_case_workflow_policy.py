from pathlib import Path


SERVICE = Path("application/services/hr_connections/hr_case_workflow.py")
REPOSITORY = Path(
    "infrastructure/persistence/teamworks_hr_case_workflow_repository.py"
)


def _source(path):
    return path.read_text(encoding="utf-8")


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
