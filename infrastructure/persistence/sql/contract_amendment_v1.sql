-- Rail A Contrats — historique append-only des avenants.
-- Compatible MySQL 5.5+ / MariaDB : pas de JSON, colonne générée ni CHECK requis.
-- La table contrats reste la projection courante consommée par le legacy.

CREATE TABLE IF NOT EXISTS tw_contract_amendment (
    amendment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    contract_id INT NOT NULL,
    effective_date DATE NOT NULL,
    kind VARCHAR(32) NOT NULL,
    idempotency_key VARCHAR(64) NOT NULL,
    request_hash CHAR(64) NOT NULL,
    changed_fields VARCHAR(255) NOT NULL,
    before_hash CHAR(64) NOT NULL,
    after_hash CHAR(64) NOT NULL,
    before_payload TEXT NOT NULL,
    after_payload TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (amendment_id),
    UNIQUE KEY uq_tw_contract_amendment_idempotency (idempotency_key),
    KEY ix_tw_contract_amendment_contract_effective (
        contract_id, effective_date, amendment_id
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
