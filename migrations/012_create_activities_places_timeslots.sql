CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(64),
    label VARCHAR(255) NOT NULL,
    category VARCHAR(64),
    is_active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(64),
    label VARCHAR(255) NOT NULL,
    city VARCHAR(128),
    is_active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS timeslots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER,
    place_id INTEGER,
    code VARCHAR(64),
    label VARCHAR(255) NOT NULL,
    weekday INTEGER,
    default_start_time VARCHAR(8),
    default_end_time VARCHAR(8),
    default_break_minutes INTEGER,
    prep_ratio DECIMAL(8,4),
    is_active BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (place_id) REFERENCES places(id)
);
