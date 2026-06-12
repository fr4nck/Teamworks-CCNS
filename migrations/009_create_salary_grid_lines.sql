CREATE TABLE IF NOT EXISTS salary_grid_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    salary_grid_id INTEGER NOT NULL,
    ccns_classification_id INTEGER,
    minimum_type VARCHAR(64) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    min_age INTEGER,
    max_age INTEGER,
    min_execution_year INTEGER,
    max_execution_year INTEGER,
    notes TEXT,
    FOREIGN KEY (salary_grid_id) REFERENCES salary_grids(id),
    FOREIGN KEY (ccns_classification_id) REFERENCES ccns_classifications(id)
);
