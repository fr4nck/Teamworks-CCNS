from pathlib import Path


SOURCE = Path("infrastructure/persistence/teamworks_hr_cases_repository.py")


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_production_case_store_stays_additive_and_legacy_decoupled():
    source = _source()

    assert "ALTER TABLE" not in source.upper()
    assert "FOREIGN KEY" not in source.upper()
    assert "ON CONFLICT" not in source.upper()
    assert "INSERT OR REPLACE" not in source.upper()
    assert "INSERT OR IGNORE" not in source.upper()

    for historical_table in (
        "individus",
        "contrats",
        "employes",
        "salaries",
    ):
        assert historical_table not in source.lower()


def test_production_case_store_does_not_persist_secrets_or_medical_content():
    source = _source().lower()

    for forbidden_column in (
        "password",
        "mot_de_passe",
        "access_token",
        "refresh_token",
        "api_key",
        "cookie",
        "diagnosis",
        "pathology",
        "medical_data",
        "health_data",
    ):
        assert forbidden_column not in source


def test_audit_store_has_no_update_or_delete_api_for_events():
    source = _source()

    assert "def update_event" not in source
    assert "def delete_event" not in source
    assert "def remove_event" not in source
    assert "DuplicateTeamworksHrAuditEventError" in source


def test_repository_uses_shared_gestiondb_boundary_not_direct_sqlite():
    source = _source()

    assert "import sqlite3" not in source
    assert "from sqlite3" not in source
    assert "GestionDB.DB()" in source
    assert "_adapt_placeholders" not in source
    assert "_execute" in source
