-- SORTIE-004 : résultats externes et documents du dossier de sortie.
-- S'applique après termination_v1.sql et termination_v2.sql.
-- Le contenu binaire reste dans le stockage documentaire existant/futur : cette
-- table conserve uniquement la référence, l'empreinte et les faits de suivi.
CREATE TABLE IF NOT EXISTS tw_termination_document (
    document_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    termination_id VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    document_type VARCHAR(32) NOT NULL,
    source VARCHAR(32) NOT NULL,
    document_date DATE NOT NULL,
    received_at DATETIME NOT NULL,
    received_by VARCHAR(128) NOT NULL,
    file_reference VARCHAR(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    external_reference VARCHAR(255) NULL,
    archived_at DATETIME NULL,
    archived_by VARCHAR(128) NULL,
    delivered_at DATETIME NULL,
    delivered_by VARCHAR(128) NULL,
    PRIMARY KEY (document_id),
    -- Un même fichier ne peut pas être importé deux fois dans le même dossier.
    UNIQUE KEY uq_tw_termination_document_hash (termination_id, sha256),
    KEY ix_tw_termination_document_type (termination_id, document_type),
    KEY ix_tw_termination_document_received (termination_id, received_at),
    CONSTRAINT fk_tw_termination_document_termination FOREIGN KEY (termination_id)
        REFERENCES tw_contract_termination (termination_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_tw_termination_document_archive_pair CHECK (
        (archived_at IS NULL AND archived_by IS NULL) OR
        (archived_at IS NOT NULL AND archived_by IS NOT NULL)
    ),
    CONSTRAINT ck_tw_termination_document_delivery_pair CHECK (
        (delivered_at IS NULL AND delivered_by IS NULL) OR
        (delivered_at IS NOT NULL AND delivered_by IS NOT NULL)
    ),
    CONSTRAINT ck_tw_termination_document_archive_time CHECK (
        archived_at IS NULL OR archived_at >= received_at
    ),
    CONSTRAINT ck_tw_termination_document_delivery_time CHECK (
        delivered_at IS NULL OR delivered_at >= received_at
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
