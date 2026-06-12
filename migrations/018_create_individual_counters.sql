CREATE TABLE IF NOT EXISTS individual_counters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    contract_id INTEGER,
    season_id INTEGER,
    period_id INTEGER,
    counter_code VARCHAR(64) NOT NULL,
    value DECIMAL(12,2) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details_json TEXT,
    FOREIGN KEY (person_id) REFERENCES people(id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (season_id) REFERENCES seasons(id),
    FOREIGN KEY (period_id) REFERENCES periods(id)
);
