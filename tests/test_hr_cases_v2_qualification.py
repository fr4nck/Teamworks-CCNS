"""Même contrat exercé sur SQLite et, explicitement, les serveurs SQL jetables."""
import os
import sqlite3
import threading
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from domain.hr_connections import ExpectedDocument, HrAuditField, HrCaseStatus
from infrastructure.persistence.teamworks_hr_cases_repository import (
    TeamworksHrCasesRepository, DuplicateTeamworksHrAuditEventError,
)
from infrastructure.persistence.teamworks_hr_case_workflow_repository import (
    TeamworksHrCaseWorkflowRepository, StaleTeamworksHrCaseTransitionError,
)
from infrastructure.persistence.teamworks_hr_case_creation_repository import TeamworksHrCaseCreationRepository
from infrastructure.persistence.teamworks_hr_connections_repository import _execute, _fetchall
from tests.test_teamworks_hr_cases_repository import _case, _event
from tests.test_teamworks_hr_case_workflow_repository import _event as transition_event


@pytest.fixture
def db_factory(tmp_path):
    port = os.environ.get('TEAMWORKS_CRH_MYSQL_TEST_PORT')
    if port:
        import mysql.connector
        options = dict(host=os.environ.get('TEAMWORKS_CRH_MYSQL_TEST_HOST', '127.0.0.1'), port=int(port), user=os.environ.get('TEAMWORKS_CRH_MYSQL_TEST_USER', 'root'), password=os.environ['TEAMWORKS_CRH_MYSQL_TEST_PASSWORD'], use_pure=True, charset='utf8', connection_timeout=5)
        database = 'tw_crh_qual_' + uuid4().hex
        admin = mysql.connector.connect(**options)
        cursor = admin.cursor()
        cursor.execute('CREATE DATABASE ' + database + ' CHARACTER SET utf8 COLLATE utf8_unicode_ci')
    class DB:
        isNetwork = bool(port)
        def __init__(self):
            if port:
                self.connexion = mysql.connector.connect(**options, database=database)
            else:
                self.connexion = sqlite3.connect(tmp_path/'qualification.sqlite', timeout=15)
            self.cursor = self.connexion.cursor()
            if port:
                self.cursor.execute("SET SESSION sql_mode='STRICT_ALL_TABLES'")
        def Commit(self): self.connexion.commit()
        def Close(self): self.connexion.close()
    try:
        yield DB
    finally:
        if port:
            # This exact random database was created above by this fixture.
            cursor.execute('DROP DATABASE ' + database)
            admin.close()


def seed(factory, label):
    sql = (Path(__file__).parent/'fixtures/hr_cases'/f'{label}_v1.sql').read_text(encoding='utf-8')
    db = factory()
    try:
        for statement in sql.split(';'):
            if statement.strip(): _execute(db, statement)
        db.Commit()
    finally: db.Close()


@pytest.mark.parametrize('label', ['crh22', 'crh36'])
def test_v1_migration_preserves_data_and_widens_long_values(db_factory, label):
    seed(db_factory, label)
    old = TeamworksHrCasesRepository(db_factory=db_factory, ensure_schema=False)
    initial = _case()
    event = _event()
    old.save_case(structure_ref='audit', case=initial)
    old.append_event(structure_ref='audit', event=event)
    new = TeamworksHrCasesRepository(db_factory=db_factory)
    assert new.schema_version() == 2
    assert new.get_case(structure_ref='audit', case_id=initial.case_id) == initial
    assert new.get_event(structure_ref='audit', event_id=event.event_id) == event
    long_case = replace(initial, result='R'*501, comment='C'*1001, expected_documents=frozenset({ExpectedDocument.create(code='long', label='L'*240)}))
    new.save_case(structure_ref='audit', case=long_case)
    assert new.get_case(structure_ref='audit', case_id=initial.case_id) == long_case
    long_event = replace(event, event_id='long-event', fields=(HrAuditField.create(key='detail', value='V'*1001),))
    new.append_event(structure_ref='audit', event=long_event)
    assert new.get_event(structure_ref='audit', event_id='long-event') == long_event
    new.ensure_schema()
    assert new.schema_version() == 2
    db=db_factory()
    try:
        if db.isNetwork:
            rows=_fetchall(db, 'SHOW INDEX FROM tw_hr_audit_events')
            names={row[2] for row in rows}
        else:
            names={row[1] for row in _fetchall(db, 'PRAGMA index_list(tw_hr_audit_events)')}
        assert 'idx_tw_hr_audit_target' in names
        assert 'idx_tw_hr_events_target' not in names
    finally: db.Close()


def run_two(action):
    results=[]
    def run(index):
        try: action(index); results.append('saved')
        except Exception as exc: results.append(type(exc).__name__)
    threads=[threading.Thread(target=run,args=(i,)) for i in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join(20)
    assert not any(thread.is_alive() for thread in threads)
    return sorted(results)


def test_schema_initialization_is_safe_for_two_connections(db_factory):
    start=threading.Barrier(2)
    def create(index):
        start.wait(timeout=10)
        assert TeamworksHrCasesRepository(db_factory=db_factory).schema_version() == 2
    assert run_two(create) == ['saved', 'saved']


def hooked_factory(factory, *, select_barrier=None, fail_insert_fields=False):
    class Cursor:
        def __init__(self, raw): self.raw=raw; self.wait=False
        def execute(self, sql, params=()):
            if fail_insert_fields and 'INSERT INTO tw_hr_audit_fields' in ' '.join(sql.split()):
                raise RuntimeError('late audit failure')
            self.wait=select_barrier is not None and 'SELECT 1 FROM tw_hr_audit_events' in ' '.join(sql.split())
            return self.raw.execute(sql,params)
        def fetchone(self):
            row=self.raw.fetchone()
            if self.wait:
                self.wait=False
                select_barrier.wait(timeout=10)
            return row
        def __getattr__(self,name): return getattr(self.raw,name)
    class DB(factory):
        def __init__(self): super().__init__(); self.cursor=Cursor(self.cursor)
    return DB


def test_racing_duplicate_event_has_domain_error_and_one_event(db_factory):
    repository=TeamworksHrCasesRepository(db_factory=db_factory)
    raced=TeamworksHrCasesRepository(db_factory=hooked_factory(db_factory,select_barrier=threading.Barrier(2)),ensure_schema=False)
    def append(index): raced.append_event(structure_ref='audit',event=_event())
    assert run_two(append) == ['DuplicateTeamworksHrAuditEventError', 'saved']
    assert len(repository.list_events(structure_ref='audit')) == 1


def test_late_audit_failure_rolls_back_projection_and_event(db_factory):
    cases=TeamworksHrCasesRepository(db_factory=db_factory)
    initial=_case()
    cases.save_case(structure_ref='audit',case=initial)
    workflow=TeamworksHrCaseWorkflowRepository(db_factory=hooked_factory(db_factory,fail_insert_fields=True),ensure_schema=False)
    with pytest.raises(RuntimeError,match='late audit failure'):
        workflow.persist_case_transition(structure_ref='audit',expected_status=HrCaseStatus.TODO,case=initial.transition_to(HrCaseStatus.PREPARED),event=transition_event())
    assert cases.get_case(structure_ref='audit',case_id=initial.case_id) == initial
    assert cases.list_events(structure_ref='audit') == ()


def test_two_transitions_from_same_status_only_commit_one_audit(db_factory):
    cases=TeamworksHrCasesRepository(db_factory=db_factory)
    initial=_case()
    cases.save_case(structure_ref='audit',case=initial)
    start=threading.Barrier(2)
    def transition(index):
        repository=TeamworksHrCaseWorkflowRepository(db_factory=db_factory,ensure_schema=False)
        start.wait(timeout=10)
        repository.persist_case_transition(structure_ref='audit',expected_status=HrCaseStatus.TODO,case=initial.transition_to(HrCaseStatus.PREPARED),event=transition_event(event_id='transition-'+str(index)))
    assert run_two(transition) == ['StaleTeamworksHrCaseTransitionError', 'saved']
    assert len(cases.list_events(structure_ref='audit')) == 1


def test_future_schema_is_rejected_without_component_tables(db_factory):
    db=db_factory()
    try:
        _execute(db,'CREATE TABLE tw_hr_schema_versions(component VARCHAR(50) NOT NULL PRIMARY KEY, schema_version INTEGER NOT NULL)')
        _execute(db,"INSERT INTO tw_hr_schema_versions VALUES ('hr_cases_runtime', 99)")
        db.Commit()
    finally: db.Close()
    with pytest.raises(RuntimeError,match='Version de schéma'):
        TeamworksHrCasesRepository(db_factory=db_factory)
    db=db_factory()
    try:
        tables=[row[0] for row in _fetchall(db,'SHOW TABLES' if db.isNetwork else "SELECT name FROM sqlite_master WHERE type='table'")]
        assert tables == ['tw_hr_schema_versions']
    finally: db.Close()


def test_unknown_column_refuses_automatic_migration(db_factory):
    seed(db_factory,'crh36')
    db=db_factory()
    try:
        _execute(db,'ALTER TABLE tw_hr_cases ADD COLUMN unexpected VARCHAR(20)')
        db.Commit()
    finally: db.Close()
    with pytest.raises(RuntimeError,match='Schéma RH inattendu'):
        TeamworksHrCasesRepository(db_factory=db_factory)
    assert TeamworksHrCasesRepository(db_factory=db_factory,ensure_schema=False).schema_version() == 1


@pytest.mark.parametrize('same_case', [True, False])
def test_concurrent_creation_collisions_roll_back_loser(db_factory, same_case):
    cases=TeamworksHrCasesRepository(db_factory=db_factory)
    raced=TeamworksHrCaseCreationRepository(db_factory=hooked_factory(db_factory,select_barrier=threading.Barrier(2)),ensure_schema=False)
    def create(index):
        case=_case(case_id='case-1' if same_case else 'case-'+str(index))
        event=_event(event_id='event-'+str(index) if same_case else 'same-event',target_ref=case.case_id)
        raced.create_case_with_event(structure_ref='audit',case=case,event=event)
    error='DuplicateTeamworksHrCaseError' if same_case else 'DuplicateTeamworksHrAuditEventError'
    assert run_two(create) == [error, 'saved']
    assert len(cases.list_cases(structure_ref='audit')) == 1
    assert len(cases.list_events(structure_ref='audit')) == 1


def test_nontransactional_engine_is_rejected(db_factory):
    db=db_factory()
    if not db.isNetwork:
        db.Close()
        pytest.skip('SQLite est transactionnel ; test moteur réservé à SQL réseau.')
    db.Close()
    seed(db_factory,'crh36')
    db=db_factory()
    try:
        _execute(db,'ALTER TABLE tw_hr_audit_events ENGINE=MyISAM')
    finally: db.Close()
    with pytest.raises(RuntimeError,match='InnoDB'):
        TeamworksHrCasesRepository(db_factory=db_factory)
    assert TeamworksHrCasesRepository(db_factory=db_factory,ensure_schema=False).schema_version() == 1


def test_interrupted_network_ddl_migration_can_resume(db_factory):
    db=db_factory()
    if not db.isNetwork:
        db.Close()
        pytest.skip('SQLite migre dans une transaction ; test DDL implicite réservé à SQL réseau.')
    db.Close()
    seed(db_factory,'crh36')
    old=TeamworksHrCasesRepository(db_factory=db_factory,ensure_schema=False)
    old.save_case(structure_ref='audit',case=_case())
    class Cursor:
        def __init__(self, raw): self.raw=raw; self.alters=0
        def execute(self,sql,params=()):
            if sql.startswith('ALTER TABLE'):
                self.alters+=1
                if self.alters==2: raise RuntimeError('migration interrupted')
            return self.raw.execute(sql,params)
        def __getattr__(self,key): return getattr(self.raw,key)
    class BrokenDB(db_factory):
        def __init__(self): super().__init__(); self.cursor=Cursor(self.cursor)
    with pytest.raises(RuntimeError,match='migration interrupted'):
        TeamworksHrCasesRepository(db_factory=BrokenDB)
    assert old.schema_version() == 1
    new=TeamworksHrCasesRepository(db_factory=db_factory)
    assert new.schema_version() == 2
    assert new.get_case(structure_ref='audit',case_id='case-1') == _case()
