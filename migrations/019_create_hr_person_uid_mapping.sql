CREATE TABLE IF NOT EXISTS tw_hr_person_uid_mapping (
    IDmapping INTEGER PRIMARY KEY AUTOINCREMENT,
    person_uid VARCHAR(100) NOT NULL UNIQUE,
    IDpersonne INTEGER NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    date_creation DATETIME,
    date_modification DATETIME
);
