CREATE TABLE IF NOT EXISTS legal_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    is_minor BOOLEAN NOT NULL DEFAULT 0,
    age_group VARCHAR(32),
    work_regime VARCHAR(64),
    convention_frame VARCHAR(64),
    training_time_included BOOLEAN,
    contract_hours_basis VARCHAR(64),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES people(id)
);
