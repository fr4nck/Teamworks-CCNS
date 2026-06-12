CREATE TABLE IF NOT EXISTS salary_grids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(64) NOT NULL,
    label VARCHAR(255) NOT NULL,
    employment_regime_id INTEGER,
    effective_date DATE NOT NULL,
    end_date DATE,
    source_reference VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (employment_regime_id) REFERENCES employment_regimes(id)
);
