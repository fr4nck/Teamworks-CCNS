CREATE TABLE IF NOT EXISTS ccns_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(64) NOT NULL,
    label VARCHAR(255) NOT NULL,
    family VARCHAR(64),
    level_order INTEGER,
    effective_date DATE,
    end_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT 1
);
