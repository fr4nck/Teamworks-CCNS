-- SORTIE-003 : transmission à Impact Emploi, snapshots immuables, corrections.
-- S'applique après termination_v1.sql. Compatibilité MySQL 5.5+ / MariaDB.
--
-- canonical_payload est un LONGTEXT utf8mb4_bin, jamais un type JSON : le
-- moteur ne doit ni réordonner ni reformater les octets hachés.
-- Les deux tables sont en ajout seul : aucune API ne les modifie, et les
-- déclencheurs de termination_v2_guards.sql refusent UPDATE et DELETE en base.
-- Corriger = insérer une nouvelle version.
-- Ces tables tracent ce que Teamworks affirme avoir communiqué, rien de plus :
-- ni réception, ni DSN, ni FCTU, ni AER.

-- Correction ouverte (dimension orthogonale au workflow), NULL sinon.
ALTER TABLE tw_contract_termination
    ADD COLUMN correction_reason TEXT NULL,
    ADD COLUMN correction_requested_at DATETIME NULL,
    ADD COLUMN correction_requested_by VARCHAR(128) NULL,
    ADD CONSTRAINT ck_tw_contract_termination_correction CHECK (
        (correction_reason IS NULL AND correction_requested_at IS NULL AND correction_requested_by IS NULL)
        OR (correction_reason IS NOT NULL AND correction_requested_at IS NOT NULL
            AND correction_requested_by IS NOT NULL)
    );

CREATE TABLE IF NOT EXISTS tw_termination_transmission_snapshot (
    snapshot_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    termination_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    version INT UNSIGNED NOT NULL,
    canonical_payload LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    payload_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME NOT NULL,
    created_by VARCHAR(128) NOT NULL,
    transmitted_at DATETIME NOT NULL,
    transmitted_by VARCHAR(128) NOT NULL,
    channel VARCHAR(16) NOT NULL,
    external_reference VARCHAR(255) NULL,
    supersedes_snapshot_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
    correction_reason TEXT NULL,
    PRIMARY KEY (snapshot_id),
    UNIQUE KEY uq_tw_termination_snapshot_version (termination_id, version),
    -- Cible de la clé étrangère composite de supersession (même sortie).
    UNIQUE KEY uq_tw_termination_snapshot_owner (termination_id, snapshot_id),
    -- Chaîne linéaire : un snapshot n'est supersédé qu'une seule fois.
    UNIQUE KEY uq_tw_termination_snapshot_supersedes (supersedes_snapshot_id),
    CONSTRAINT fk_tw_termination_snapshot_termination FOREIGN KEY (termination_id)
        REFERENCES tw_contract_termination (termination_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_tw_termination_snapshot_supersedes FOREIGN KEY (termination_id, supersedes_snapshot_id)
        REFERENCES tw_termination_transmission_snapshot (termination_id, snapshot_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_tw_termination_snapshot_version CHECK (version >= 1),
    CONSTRAINT ck_tw_termination_snapshot_chain CHECK (
        (version = 1 AND supersedes_snapshot_id IS NULL AND correction_reason IS NULL)
        OR (version > 1 AND supersedes_snapshot_id IS NOT NULL AND correction_reason IS NOT NULL)
    ),
    CONSTRAINT ck_tw_termination_snapshot_times CHECK (transmitted_at <= created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Registre d'idempotence et piste d'audit des commandes. Aucun payload RH :
-- identifiants, versions, hash et acteur uniquement.
CREATE TABLE IF NOT EXISTS tw_termination_command (
    command_id VARCHAR(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    command_type VARCHAR(32) NOT NULL,
    command_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    termination_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    snapshot_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
    snapshot_version INT UNSIGNED NULL,
    payload_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
    termination_version_before INT UNSIGNED NOT NULL,
    termination_version_after INT UNSIGNED NOT NULL,
    actor_id VARCHAR(128) NOT NULL,
    recorded_at DATETIME NOT NULL,
    PRIMARY KEY (command_id),
    UNIQUE KEY uq_tw_termination_command_snapshot (snapshot_id),
    KEY ix_tw_termination_command_timeline (termination_id, recorded_at),
    CONSTRAINT fk_tw_termination_command_termination FOREIGN KEY (termination_id)
        REFERENCES tw_contract_termination (termination_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_tw_termination_command_snapshot FOREIGN KEY (snapshot_id)
        REFERENCES tw_termination_transmission_snapshot (snapshot_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_tw_termination_command_versions CHECK (
        termination_version_after = termination_version_before + 1
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
