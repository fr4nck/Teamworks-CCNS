from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "recipe_qt_contracts_mysql.py"
LAUNCHER = ROOT / "tools" / "run_rail_a_contracts_mysql_windows.cmd"


def _source():
    return SCRIPT.read_text(encoding="utf-8")


def test_rail_a_mysql_recipe_refuses_sqlite_and_requires_windows():
    source = _source()

    assert 'os.name != "nt"' in source
    assert 'getattr(db, "isNetwork", False) is not True' in source
    assert "TEAMWORKS_RAIL_A_BACKEND:MYSQL" in source
    assert "TEAMWORKS_RAIL_A_MYSQL_READY" in source
    assert "TEAMWORKS_RAIL_A_MYSQL_FAILED" in source


def test_rail_a_mysql_recipe_uses_contract_service_and_production_adapter():
    source = _source()

    assert "GestionDbContractWriteAdapter" in source
    assert "create_contract(port" in source
    assert "update_contract(port" in source
    assert "delete_contract(" in source
    assert "contract_exists(contract_id)" in source
    assert 'gross_monthly_salary=Decimal("9999.01")' in source


def test_rail_a_windows_launcher_executes_the_strict_mysql_recipe():
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "recipe_qt_contracts_mysql.py" in source
    assert "artifacts\\rail-a-mysql" in source
    assert "console.txt" in source
    assert "stop-gate Rail A Windows/MySQL" in source


def test_rail_a_mysql_recipe_avoids_contract_overlap_before_writing():
    source = _source()

    assert "def _safe_person_id" in source
    assert "WHERE NOT EXISTS" in source
    assert "c.date_debut<=%s" in source
    assert "c.date_fin>=%s" in source
    assert "excluded_person_ids" in source
    assert "selected_people" not in source
    assert "_first_person_id" not in source
    assert "aucune ecriture n'a ete tentee" in source


def test_rail_a_mysql_recipe_binds_evidence_to_clean_expected_git_source():
    source = _source()

    assert 'EXPECTED_BRANCH = "qt/master"' in source
    assert "def _git_source_preflight" in source
    assert '"status", "--porcelain", "--untracked-files=no"' in source
    assert "branch == EXPECTED_BRANCH" in source
    assert "TEAMWORKS_RAIL_A_RUN:" in source
    assert "TEAMWORKS_RAIL_A_SOURCE:SHA=" in source
    assert "TEAMWORKS_RAIL_A_SOURCE:BRANCH=" in source
    assert "TEAMWORKS_RAIL_A_SOURCE:TRACKED_WORKTREE=CLEAN" in source
    assert '"tracked_worktree_clean": preflight["tracked_worktree_clean"]' in source


def test_rail_a_mysql_recipe_uses_teamworks_configured_mysql_connector():
    source = _source()

    assert "from Utils import UTILS_Config" in source
    assert "def _configure_mysql_interface" in source
    assert '"interface_mysql", "mysql.connector"' in source
    assert "GestionDB.SetInterfaceMySQL(configured)" in source
    assert "GestionDB.IMPORT_MYSQLDB_OK" in source
    assert "GestionDB.IMPORT_MYSQLCONNECTOR_OK" in source
    assert "TEAMWORKS_RAIL_A_PREFLIGHT:CONNECTOR=" in source
    assert "configured_connector = None" in source
    assert "try:\n        configured_connector, active_connector = _configure_mysql_interface()" in source
    assert '"configured_connector": configured_connector' in source
    assert '"active_connector": active_connector' in source


def test_rail_a_mysql_recipe_preflights_real_server_and_transaction_session():
    source = _source()

    assert "SELECT VERSION(), DATABASE(), @@autocommit" in source
    assert "@@session.transaction_isolation" in source
    assert "@@session.tx_isolation" in source
    assert "db.connexion.rollback()" in source
    assert "db.Commit()" in source
    assert '"CDI" in available.value' in source
    assert '"CDD" in available.value' in source
    assert "SalaryMinimumPeriodicity.MONTHLY" in source


def test_rail_a_mysql_recipe_applies_and_inspects_amendment_ddl():
    source = _source()

    assert "contract_amendment_v1.sql" in source
    assert "information_schema.TABLES" in source
    assert "information_schema.COLUMNS" in source
    assert "information_schema.STATISTICS" in source
    assert 'engine.upper() == "INNODB"' in source
    assert '"idempotency_key"' in source
    assert '"VARCHAR(64)"' in source
    assert '"uq_tw_contract_amendment_idempotency"' in source
    assert '"ix_tw_contract_amendment_contract_effective"' in source
    assert '"contract_id", "effective_date", "amendment_id"' in source
    assert "TEAMWORKS_RAIL_A_STAGE:amendment-schema" in source


def test_rail_a_mysql_recipe_uses_real_amendment_service_and_hashes():
    source = _source()

    assert "GestionDbContractAmendmentAdapter" in source
    assert "ContractAmendmentCommand" in source
    assert "apply_contract_amendment" in source
    assert "contract_state_hash" in source
    assert 'gross_monthly_salary=Decimal("9999.10")' in source
    assert "TEAMWORKS_RAIL_A_STAGE:amendment-cdi-commit-readback" in source


def test_rail_a_mysql_recipe_covers_idempotent_replay_and_conflict():
    source = _source()

    assert "IDEMPOTENT_REPLAY" in source
    assert 'gross_monthly_salary=Decimal("9999.20")' in source
    assert "_amendment_count(db, cdi_key) == 1" in source
    assert "TEAMWORKS_RAIL_A_STAGE:amendment-idempotent-replay" in source
    assert "TEAMWORKS_RAIL_A_STAGE:amendment-idempotency-conflict" in source


def test_rail_a_mysql_recipe_forces_real_sql_rollback_without_schema_changes():
    source = _source()

    assert "class _RollbackFailureAdapter" in source
    assert "GestionDbContractAmendmentAdapter" in source
    assert "__rail_a_missing_column__" in source
    assert "result.committed is False" in source
    assert "_new_connection()" in source
    assert "_amendment_count(verify_db, rollback_key) == 0" in source
    assert "TEAMWORKS_RAIL_A_STAGE:amendment-real-rollback" in source


def test_rail_a_mysql_recipe_covers_commit_then_readback_failure():
    source = _source()

    assert "class _ReadbackFailureAfterCommitAdapter" in source
    assert "super().commit()" in source
    assert "forced post-commit readback failure" in source
    assert "result.code == WriteCode.READBACK_ERROR" in source
    assert "result.committed is True" in source
    assert 'history["after_hash"] == after_hash' in source
    assert "TEAMWORKS_RAIL_A_STAGE:amendment-readback-after-commit" in source


def test_rail_a_mysql_recipe_runs_two_connection_concurrency_with_timeout():
    source = _source()

    assert "threading.Barrier(2" in source
    assert "threading.Thread" in source
    assert "thread_a" in source and "thread_b" in source
    assert "innodb_lock_wait_timeout=10" in source
    assert "join(timeout=25)" in source
    assert "CONCURRENT_MODIFICATION" in source
    assert "len(winners) == 1" in source
    assert "len(losers) == 1" in source
    assert 'results[loser]["functional_after"] is True' in source
    assert "TEAMWORKS_RAIL_A_STAGE:amendment-concurrency" in source


def test_rail_a_mysql_recipe_preserves_cdd_renewal_genealogy():
    source = _source()

    assert "TEAMWORKS_RAIL_A_STAGE:release-cdi-fixture" in source
    assert "not port.contract_exists(cdi_id)" in source
    assert "person_id = cdi_person" in source
    assert "ContractOperation.CDD_RENEWAL.value" in source
    assert "previous_contract_id=previous_id" in source
    assert 'weekly_hours=Decimal("32.00")' in source
    assert 'history["changed_fields"] == "weekly_hours"' in source
    assert 'history["kind"] == "WORKING_TIME"' in source
    assert "TEAMWORKS_RAIL_A_STAGE:amendment-cdd-renewal" in source


def test_rail_a_mysql_recipe_cleans_history_and_contracts_then_verifies_independently():
    source = _source()

    assert "def _cleanup_verified" in source
    assert "DELETE FROM tw_contract_amendment" in source
    assert 'run_id + "-%"' in source
    assert "for contract_id in reversed(contract_ids)" in source
    assert "delete_contract(" in source
    assert "remaining_contracts" in source
    assert "remaining_history == 0" in source
    assert "table_present" in source
    assert "TEAMWORKS_RAIL_A_CLEANUP:OK" in source
    assert "TEAMWORKS_RAIL_A_CLEANUP:FAILED" in source


def test_rail_a_mysql_recipe_writes_machine_readable_report_without_personal_fields():
    source = _source()

    assert 'REPORT_PATH = REPORT_DIR / "report.json"' in source
    assert '"tested_sha"' in source
    assert '"branch"' in source
    assert '"python_version"' in source
    assert '"mysql"' in source
    assert '"scenarios"' in source
    assert '"technical_ids"' in source
    assert '"cleanup"' in source
    forbidden = ("nom_personne", "prenom", "adresse", "securite_sociale", "telephone")
    assert all(item not in source.lower() for item in forbidden)


def test_ready_marker_is_emitted_only_after_cleanup_and_report_success():
    source = _source()

    cleanup_pos = source.rfind("_cleanup_verified(run_id, contract_ids)")
    report_pos = source.rfind("_write_report(report)")
    ready_pos = source.rfind("print(READY, flush=True)")
    assert cleanup_pos != -1 and report_pos != -1 and ready_pos != -1
    assert cleanup_pos < report_pos < ready_pos
    assert "if scenarios_ok and cleanup_ok and report_ok:" in source
