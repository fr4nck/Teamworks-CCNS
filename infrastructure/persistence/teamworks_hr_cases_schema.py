"""Migration des seuls schémas CRH-22/36 connus, sans réduction des données."""
from hashlib import sha256
import re

from .teamworks_hr_connections_repository import _execute, _fetchall, _fetchone

_OLD_TYPES = {
    ('tw_hr_cases', 'result'): {'text', 'varchar(500)'},
    ('tw_hr_cases', 'comment'): {'text', 'varchar(1000)'},
    ('tw_hr_case_expected_documents', 'document_label'): {'varchar(200)', 'varchar(240)'},
    ('tw_hr_audit_fields', 'field_value'): {'varchar(500)', 'varchar(1000)', 'text'},
}
_PRIMARY_KEYS = {
    'tw_hr_schema_versions': ('component',),
    'tw_hr_cases': ('structure_ref', 'case_id'),
    'tw_hr_case_expected_documents': ('structure_ref', 'case_id', 'document_code'),
    'tw_hr_audit_events': ('structure_ref', 'event_id'),
    'tw_hr_audit_fields': ('structure_ref', 'event_id', 'position'),
}


def acquire_schema_lock(db):
    if not bool(getattr(db, 'isNetwork', False)):
        _execute(db, 'BEGIN IMMEDIATE')
        return None
    database = _fetchone(db, 'SELECT DATABASE()')[0]
    name = 'tw_hr_cases_' + sha256(database.encode('utf-8')).hexdigest()[:32]
    if _fetchone(db, 'SELECT GET_LOCK(?, 10)', (name,))[0] != 1:
        raise RuntimeError("Le schéma RH est en cours de migration ; réessayez.")
    return name


def release_schema_lock(db, name):
    if name is not None:
        _fetchone(db, 'SELECT RELEASE_LOCK(?)', (name,))


def create_schema_tables(db, statements):
    network = bool(getattr(db, 'isNetwork', False))
    # Refuse a future version before creating any component tables.
    statement = statements[0].strip()
    if network:
        statement += ' ENGINE=InnoDB'
    _execute(db, statement)
    version = _fetchone(db, "SELECT schema_version FROM tw_hr_schema_versions WHERE component = ?", ('hr_cases_runtime',))
    if version is not None and int(version[0]) not in (1, 2):
        raise RuntimeError(f"Version de schéma des démarches RH non prise en charge : {version[0]}.")
    for statement in statements[1:]:
        sql = statement.strip()
        if network:
            sql += ' ENGINE=InnoDB'
        _execute(db, sql)


def migrate_known_columns(db, statements):
    network = bool(getattr(db, 'isNetwork', False))
    changes = []
    # Validate every table before the first ALTER (MySQL DDL commits implicitly).
    for statement in statements:
        table = re.search(r'CREATE TABLE IF NOT EXISTS (\w+)', statement).group(1)
        expected = {}
        expected_nullable = {}
        for line in statement.splitlines():
            match = re.match(r'\s*(\w+)\s+(VARCHAR\(\d+\)|TEXT|INTEGER)(?:\s|,)', line, re.I)
            if match:
                expected[match[1]] = match[2].lower()
                expected_nullable[match[1]] = 'NOT NULL' not in line.upper() and 'PRIMARY KEY' not in line.upper()
        if network:
            rows = _fetchall(db, f'SHOW COLUMNS FROM {table}')
            actual = {row[0]: re.sub(r'^int\(\d+\)$', 'integer', row[1].lower()) for row in rows}
            nullable = {row[0]: row[2] == 'YES' for row in rows}
            keys = _fetchall(db, f"SHOW INDEX FROM {table} WHERE Key_name = 'PRIMARY'")
            primary = tuple(row[4] for row in sorted(keys, key=lambda row: row[3]))
            if any(row[7] is not None for row in keys):
                raise RuntimeError(f"Clé primaire RH préfixée inattendue : {table}.")
            status = _fetchone(db, 'SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?', (table,))
            if not status or str(status[0]).lower() != 'innodb':
                raise RuntimeError(f"Le moteur transactionnel InnoDB est requis pour {table}.")
        else:
            rows = _fetchall(db, f'PRAGMA table_info({table})')
            actual = {row[1]: row[2].lower() for row in rows}
            nullable = {row[1]: not bool(row[3]) for row in rows}
            primary = tuple(row[1] for row in sorted(rows, key=lambda row: row[5]) if row[5])
        if primary != _PRIMARY_KEYS[table]:
            raise RuntimeError(f"Clé primaire RH inattendue pour {table}.")
        if set(actual) != set(expected):
            raise RuntimeError(f"Schéma RH inattendu pour {table} ; aucune migration automatique.")
        if nullable != expected_nullable:
            raise RuntimeError(f"Contraintes NULL RH inattendues pour {table}.")
        for column, target in expected.items():
            allowed = _OLD_TYPES.get((table, column), {target})
            if actual[column] not in allowed:
                raise RuntimeError(f"Type RH inattendu pour {table}.{column} : {actual[column]}.")
            if network and actual[column] != target:
                suffix = ' NOT NULL' if column in ('document_label', 'field_value') else ' NULL'
                changes.append(f'ALTER TABLE {table} MODIFY COLUMN {column} {target.upper()}{suffix}')
    for sql in changes:
        _execute(db, sql)
    # SQLite TEXT and VARCHAR have the same affinity and no length limit;
    # preserve its tables rather than rebuild them just to change metadata.


def _index_columns(db, table, name):
    if bool(getattr(db, 'isNetwork', False)):
        rows = _fetchall(db, f'SHOW INDEX FROM {table} WHERE Key_name = ?', (name,))
        if not rows:
            return None
        if any(row[7] is not None for row in rows):
            raise RuntimeError(f"Index RH préfixé inattendu : {name}.")
        return tuple(row[4] for row in sorted(rows, key=lambda row: row[3]))
    exists = _fetchone(db, "SELECT name FROM sqlite_master WHERE type = 'index' AND name = ?", (name,))
    return tuple(row[2] for row in _fetchall(db, f'PRAGMA index_info({name})')) if exists else None


def normalize_indexes(db, indexes):
    def drop(table, name):
        sql = f'DROP INDEX {name}'
        if bool(getattr(db, 'isNetwork', False)):
            sql += f' ON {table}'
        _execute(db, sql)
    for table, name, columns in indexes:
        target = tuple(item.strip() for item in columns.split(','))
        actual = _index_columns(db, table, name)
        if actual is not None and actual != target:
            if name != 'idx_tw_hr_cases_organization' or actual != target[:-1]:
                raise RuntimeError(f"Définition d'index RH inattendue : {name}.")
            drop(table, name)
            actual = None
        if actual is None:
            _execute(db, f'CREATE INDEX {name} ON {table}({columns})')
    old = _index_columns(db, 'tw_hr_audit_events', 'idx_tw_hr_events_target')
    if old is not None:
        if old != ('structure_ref', 'target_kind', 'target_ref', 'occurred_at'):
            raise RuntimeError("Ancien index d'audit RH inattendu.")
        drop('tw_hr_audit_events', 'idx_tw_hr_events_target')
