CREATE TABLE IF NOT EXISTS periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL,
    code VARCHAR(64),
    label VARCHAR(255) NOT NULL,
    period_type VARCHAR(64),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_planning_active BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (season_id) REFERENCES seasons(id)
);
