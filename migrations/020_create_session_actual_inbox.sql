CREATE TABLE IF NOT EXISTS tw_session_actual_inbox (
    IDinbox INTEGER PRIMARY KEY AUTOINCREMENT,
    idempotence_key VARCHAR(255) NOT NULL UNIQUE,
    revision_key VARCHAR(255) NOT NULL UNIQUE,
    source_domain VARCHAR(64) NOT NULL,
    contract_version VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actual_uuid VARCHAR(64) NOT NULL,
    session_uid VARCHAR(128) NOT NULL,
    actual_revision INTEGER NOT NULL,
    payload_sha256 VARCHAR(64) NOT NULL,
    date_reception DATETIME NOT NULL
);
