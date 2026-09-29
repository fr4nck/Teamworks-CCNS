from pathlib import Path

SCHEMA = Path("infrastructure/persistence/sql/mysql/dpae_v1.sql")


def schema_text():
    return SCHEMA.read_text(encoding="utf-8")


def test_dpae_mysql_schema_contains_absolute_uniqueness_guards():
    sql = schema_text()
    required = (
        "UNIQUE KEY uq_tw_dpae_case_key (case_key)",
        "UNIQUE KEY uq_tw_dpae_submission_attempt (case_id, attempt_no)",
        "UNIQUE KEY uq_tw_dpae_submission_idempotency (idempotency_key)",
        "PRIMARY KEY (case_id)",
        "UNIQUE KEY uq_tw_dpae_return_external (provider, external_return_id)",
        "UNIQUE KEY uq_tw_dpae_return_raw (provider, return_type, raw_hash)",
        "PRIMARY KEY (return_id)",
        "PRIMARY KEY (return_id, effect_type)",
    )
    for fragment in required:
        assert fragment in sql


def test_dpae_mysql_schema_never_cascades_audit_history():
    sql = schema_text().upper()
    assert "ON DELETE CASCADE" not in sql
    assert sql.count("ON DELETE RESTRICT") >= 10


def test_dpae_mysql_schema_stays_compatible_with_historical_mysql_baseline():
    sql = schema_text().upper()
    forbidden = (
        "CREATE UNIQUE INDEX IF NOT EXISTS",
        "GENERATED ALWAYS",
        " WHERE STATE IN ",
        "JSON ",
    )
    for fragment in forbidden:
        assert fragment not in sql
    # Les invariants conditionnels sont matérialisés dans des tables de verrou,
    # plutôt que de dépendre d'index partiels absents du MySQL historique.
    assert "TW_DPAE_CASE_SUBMISSION_LOCK" in sql
    assert "TW_DPAE_CURRENT_CORRELATION" in sql
