-- DPAE v1 — contraintes MySQL/MariaDB compatibles avec le socle historique.
-- Pas d'index partiel, colonne générée ni CHECK requis : les verrous logiques
-- sont matérialisés dans des tables dédiées pour rester compatibles MySQL 5.5.

CREATE TABLE IF NOT EXISTS tw_dpae_case (
    id VARCHAR(64) NOT NULL,
    case_key VARCHAR(128) NOT NULL,
    employee_id VARCHAR(64) NOT NULL,
    contract_id VARCHAR(64) NOT NULL,
    establishment_id VARCHAR(64) NOT NULL,
    expected_hiring_at DATETIME NOT NULL,
    status VARCHAR(32) NOT NULL,
    origin VARCHAR(16) NOT NULL DEFAULT 'TEAMWORKS',
    created_at DATETIME NOT NULL,
    closed_at DATETIME NULL,
    version INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tw_dpae_case_key (case_key)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tw_dpae_submission (
    id VARCHAR(64) NOT NULL,
    case_id VARCHAR(64) NOT NULL,
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
    KEY ix_tw_dpae_submission_external_flux (external_flux_id),
    CONSTRAINT fk_tw_dpae_submission_case FOREIGN KEY (case_id)
        REFERENCES tw_dpae_case(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Une seule tentative SENDING/OUTCOME_UNKNOWN par Case.
-- Le service insère la ligne au passage dans un état incertain et la retire
-- uniquement lors d'une résolution définitive, dans la même transaction.
CREATE TABLE IF NOT EXISTS tw_dpae_case_submission_lock (
    case_id VARCHAR(64) NOT NULL,
    submission_id VARCHAR(64) NOT NULL,
    acquired_at DATETIME NOT NULL,
    PRIMARY KEY (case_id),
    UNIQUE KEY uq_tw_dpae_case_submission_lock_submission (submission_id),
    CONSTRAINT fk_tw_dpae_lock_case FOREIGN KEY (case_id)
        REFERENCES tw_dpae_case(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_lock_submission FOREIGN KEY (submission_id)
        REFERENCES tw_dpae_submission(id) ON DELETE RESTRICT
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
    CONSTRAINT fk_tw_dpae_return_submission FOREIGN KEY (submission_id)
        REFERENCES tw_dpae_submission(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_return_case FOREIGN KEY (case_id)
        REFERENCES tw_dpae_case(id) ON DELETE RESTRICT
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
    CONSTRAINT fk_tw_dpae_decision_return FOREIGN KEY (return_id)
        REFERENCES tw_dpae_return(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_decision_submission FOREIGN KEY (candidate_submission_id)
        REFERENCES tw_dpae_submission(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_decision_supersedes FOREIGN KEY (supersedes_id)
        REFERENCES tw_dpae_correlation_decision(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Une seule corrélation courante par retour, sans dépendre d'un index partiel.
CREATE TABLE IF NOT EXISTS tw_dpae_current_correlation (
    return_id VARCHAR(64) NOT NULL,
    submission_id VARCHAR(64) NOT NULL,
    decision_id VARCHAR(64) NOT NULL,
    confirmed_at DATETIME NOT NULL,
    PRIMARY KEY (return_id),
    UNIQUE KEY uq_tw_dpae_current_correlation_decision (decision_id),
    CONSTRAINT fk_tw_dpae_current_return FOREIGN KEY (return_id)
        REFERENCES tw_dpae_return(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_current_submission FOREIGN KEY (submission_id)
        REFERENCES tw_dpae_submission(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tw_dpae_current_decision FOREIGN KEY (decision_id)
        REFERENCES tw_dpae_correlation_decision(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Exactly-once par type d'effet métier et retour.
CREATE TABLE IF NOT EXISTS tw_dpae_return_effect (
    return_id VARCHAR(64) NOT NULL,
    effect_type VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (return_id, effect_type),
    CONSTRAINT fk_tw_dpae_effect_return FOREIGN KEY (return_id)
        REFERENCES tw_dpae_return(id) ON DELETE RESTRICT
) ENGINE=InnoDB;
