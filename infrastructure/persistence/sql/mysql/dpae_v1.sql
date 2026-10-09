-- DPAE DATA-001 / V2 — contraintes MySQL/MariaDB compatibles avec le socle historique.
-- Pas d'index partiel, colonne générée ni CHECK requis : les verrous logiques
-- sont matérialisés dans des tables dédiées pour rester compatibles MySQL 5.5.

CREATE TABLE IF NOT EXISTS tw_dpae_case (
    id VARCHAR(64) NOT NULL,
    case_key VARCHAR(128) NOT NULL,
    contract_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    origin VARCHAR(16) NOT NULL DEFAULT 'TEAMWORKS',
    created_at DATETIME NOT NULL,
    closed_at DATETIME NULL,
    version INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tw_dpae_case_key (case_key),
    KEY ix_tw_dpae_case_contract (contract_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_snapshot (
    id VARCHAR(64) NOT NULL,
    case_id VARCHAR(64) NOT NULL,
    contract_id VARCHAR(64) NOT NULL,
    rules_version VARCHAR(64) NOT NULL,
    source_fingerprint CHAR(64) NOT NULL,
    canonical_payload LONGTEXT NOT NULL,
    payload_hash CHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY ix_tw_dpae_snapshot_case_created (case_id, created_at),
    KEY ix_tw_dpae_snapshot_contract_created (contract_id, created_at),
    CONSTRAINT fk_tw_dpae_snapshot_case FOREIGN KEY (case_id) REFERENCES tw_dpae_case(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_case_event (
    id VARCHAR(64) NOT NULL,
    case_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    state_before VARCHAR(32) NOT NULL,
    state_after VARCHAR(32) NOT NULL,
    version_before INTEGER NOT NULL,
    version_after INTEGER NOT NULL,
    actor_type VARCHAR(16) NOT NULL,
    actor_id VARCHAR(64) NULL,
    reason_code VARCHAR(64) NULL,
    reason_text VARCHAR(512) NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    command_hash CHAR(64) NOT NULL,
    occurred_at DATETIME NOT NULL,
    recorded_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tw_dpae_case_event_idempotency (case_id, idempotency_key),
    UNIQUE KEY uq_tw_dpae_case_event_version (case_id, version_after),
    KEY ix_tw_dpae_case_event_timeline (case_id, occurred_at, id),
    KEY ix_tw_dpae_case_event_type (event_type, occurred_at),
    CONSTRAINT fk_tw_dpae_case_event_case FOREIGN KEY (case_id) REFERENCES tw_dpae_case(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Audit des commandes, y compris celles refusées. Ne contient aucun payload RH :
-- seulement les identités techniques, empreintes, versions et codes de décision.
CREATE TABLE IF NOT EXISTS tw_dpae_command_audit (
    id VARCHAR(64) NOT NULL,
    command_id VARCHAR(128) NOT NULL,
    command_type VARCHAR(64) NOT NULL,
    command_hash CHAR(64) NOT NULL,
    actor_type VARCHAR(16) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    execution_id VARCHAR(128) NULL,
    initiated_by_type VARCHAR(16) NULL,
    initiated_by_id VARCHAR(64) NULL,
    case_id VARCHAR(64) NULL,
    submission_id VARCHAR(64) NULL,
    requested_at DATETIME NOT NULL,
    decided_at DATETIME NOT NULL,
    decision VARCHAR(32) NOT NULL,
    decision_code VARCHAR(64) NULL,
    case_version_seen INTEGER NULL,
    submission_version_seen INTEGER NULL,
    reason_code VARCHAR(64) NULL,
    correlation_id VARCHAR(128) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tw_dpae_command_audit_command (command_id),
    KEY ix_tw_dpae_command_audit_case_date (case_id, requested_at),
    KEY ix_tw_dpae_command_audit_actor_date (actor_type, actor_id, requested_at),
    KEY ix_tw_dpae_command_audit_decision_date (decision, requested_at),
    CONSTRAINT fk_tw_dpae_command_audit_case FOREIGN KEY (case_id) REFERENCES tw_dpae_case(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_submission (
    id VARCHAR(64) NOT NULL,
    case_id VARCHAR(64) NOT NULL,
    snapshot_id VARCHAR(64) NOT NULL,
    attempt_no INTEGER NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    payload_hash CHAR(64) NOT NULL,
    state VARCHAR(32) NOT NULL,
    external_flux_id VARCHAR(128) NULL,
    version INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    sent_at DATETIME NULL,
    completed_at DATETIME NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tw_dpae_submission_attempt (case_id, attempt_no),
    UNIQUE KEY uq_tw_dpae_submission_idempotency (idempotency_key),
    KEY ix_tw_dpae_submission_case_created (case_id, created_at),
    KEY ix_tw_dpae_submission_snapshot (snapshot_id),
    KEY ix_tw_dpae_submission_external_flux (external_flux_id),
    CONSTRAINT fk_tw_dpae_submission_case FOREIGN KEY (case_id) REFERENCES tw_dpae_case(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_submission_snapshot FOREIGN KEY (snapshot_id) REFERENCES tw_dpae_snapshot(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_case_submission_lock (
    case_id VARCHAR(64) NOT NULL,
    submission_id VARCHAR(64) NOT NULL,
    acquired_at DATETIME NOT NULL,
    PRIMARY KEY (case_id),
    UNIQUE KEY uq_tw_dpae_case_submission_lock_submission (submission_id),
    CONSTRAINT fk_tw_dpae_lock_case FOREIGN KEY (case_id) REFERENCES tw_dpae_case(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_lock_submission FOREIGN KEY (submission_id) REFERENCES tw_dpae_submission(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_return (
    id VARCHAR(64) NOT NULL,
    provider VARCHAR(32) NOT NULL,
    return_type VARCHAR(32) NOT NULL,
    raw_hash CHAR(64) NOT NULL,
    received_at DATETIME NOT NULL,
    external_return_id VARCHAR(128) NULL,
    external_flux_id VARCHAR(128) NULL,
    employer_siret VARCHAR(14) NULL,
    submission_id VARCHAR(64) NULL,
    case_id VARCHAR(64) NULL,
    correlation_status VARCHAR(32) NOT NULL,
    processing_status VARCHAR(32) NOT NULL DEFAULT 'RECEIVED',
    version INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tw_dpae_return_external (provider, external_return_id),
    UNIQUE KEY uq_tw_dpae_return_raw (provider, return_type, raw_hash),
    KEY ix_tw_dpae_return_flux (external_flux_id),
    KEY ix_tw_dpae_return_submission_received (submission_id, received_at),
    KEY ix_tw_dpae_return_status_received (correlation_status, received_at),
    CONSTRAINT fk_tw_dpae_return_submission FOREIGN KEY (submission_id) REFERENCES tw_dpae_submission(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_return_case FOREIGN KEY (case_id) REFERENCES tw_dpae_case(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_correlation_decision (
    id VARCHAR(64) NOT NULL,
    return_id VARCHAR(64) NOT NULL,
    action VARCHAR(32) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    decided_at DATETIME NOT NULL,
    candidate_submission_id VARCHAR(64) NULL,
    reason_code VARCHAR(64) NULL,
    supersedes_id VARCHAR(64) NULL,
    PRIMARY KEY (id),
    KEY ix_tw_dpae_decision_return_date (return_id, decided_at),
    CONSTRAINT fk_tw_dpae_decision_return FOREIGN KEY (return_id) REFERENCES tw_dpae_return(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_decision_submission FOREIGN KEY (candidate_submission_id) REFERENCES tw_dpae_submission(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_decision_supersedes FOREIGN KEY (supersedes_id) REFERENCES tw_dpae_correlation_decision(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_current_correlation (
    return_id VARCHAR(64) NOT NULL,
    submission_id VARCHAR(64) NOT NULL,
    decision_id VARCHAR(64) NOT NULL,
    confirmed_at DATETIME NOT NULL,
    PRIMARY KEY (return_id),
    UNIQUE KEY uq_tw_dpae_current_correlation_decision (decision_id),
    CONSTRAINT fk_tw_dpae_current_return FOREIGN KEY (return_id) REFERENCES tw_dpae_return(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_current_submission FOREIGN KEY (submission_id) REFERENCES tw_dpae_submission(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_current_decision FOREIGN KEY (decision_id) REFERENCES tw_dpae_correlation_decision(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_return_effect (
    return_id VARCHAR(64) NOT NULL,
    effect_type VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (return_id, effect_type),
    CONSTRAINT fk_tw_dpae_effect_return FOREIGN KEY (return_id) REFERENCES tw_dpae_return(id) ON DELETE RESTRICT
) ENGINE=InnoDB;
