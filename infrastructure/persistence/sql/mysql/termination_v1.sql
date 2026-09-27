-- SORTIE-002 : persistance des sorties salarié (ContractTermination).
--
-- Compatibilité visée : MySQL 5.5+ et MariaDB 10.x (pas de colonne générée,
-- pas de JSON, DATETIME à la seconde, stockage en UTC).
-- ENGINE=InnoDB est explicite : sans moteur transactionnel, ni le rollback ni
-- l'optimistic locking ne sont garantis.
--
-- Unicité « une sortie active par contrat » : active_contract_id vaut
-- contract_id tant que la sortie n'est pas clôturée, NULL ensuite. L'index
-- UNIQUE accepte plusieurs NULL (sorties clôturées) mais une seule valeur non
-- NULL par contrat, y compris sous insertions concurrentes.
--
-- Aucune ligne n'est créée à partir de contrats.date_fin / contracts.end_date.

CREATE TABLE IF NOT EXISTS tw_contract_termination (
    termination_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    contract_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    active_contract_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
    decision_date DATE NULL,
    known_at DATETIME NOT NULL,
    effective_end_date DATE NOT NULL,
    termination_reason VARCHAR(32) NOT NULL,
    notification_date DATE NULL,
    last_worked_date DATE NOT NULL,
    notice_status VARCHAR(16) NOT NULL,
    notice_start DATE NULL,
    notice_end DATE NULL,
    comments TEXT NOT NULL,
    hr_hours VARCHAR(16) NOT NULL,
    hr_absences VARCHAR(16) NOT NULL,
    hr_leave VARCHAR(16) NOT NULL,
    hr_variable_pay VARCHAR(16) NOT NULL,
    hr_exceptional_items VARCHAR(16) NOT NULL,
    workflow_status VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL,
    created_by VARCHAR(128) NOT NULL,
    updated_at DATETIME NOT NULL,
    version INT UNSIGNED NOT NULL,
    PRIMARY KEY (termination_id),
    UNIQUE KEY uq_tw_contract_termination_active (active_contract_id),
    -- Lecture de l'historique des sorties d'un contrat.
    KEY ix_tw_contract_termination_contract (contract_id),
    CONSTRAINT ck_tw_contract_termination_version CHECK (version >= 1),
    CONSTRAINT ck_tw_contract_termination_dates CHECK (last_worked_date <= effective_end_date),
    CONSTRAINT ck_tw_contract_termination_active CHECK (
        (workflow_status = 'CLOTURE' AND active_contract_id IS NULL)
        OR (workflow_status <> 'CLOTURE' AND active_contract_id = contract_id)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
