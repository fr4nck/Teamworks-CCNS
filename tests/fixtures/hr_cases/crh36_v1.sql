CREATE TABLE IF NOT EXISTS tw_hr_schema_versions (
        component VARCHAR(50) NOT NULL PRIMARY KEY,
        schema_version INTEGER NOT NULL
    );
CREATE TABLE IF NOT EXISTS tw_hr_cases (
        structure_ref VARCHAR(80) NOT NULL,
        case_id VARCHAR(100) NOT NULL,
        case_type_code VARCHAR(100) NOT NULL,
        case_type_label VARCHAR(200) NOT NULL,
        subject_kind VARCHAR(30) NOT NULL,
        subject_identifier VARCHAR(100) NOT NULL,
        organization_code VARCHAR(80) NOT NULL,
        opened_on VARCHAR(10) NOT NULL,
        due_on VARCHAR(10),
        status VARCHAR(30) NOT NULL,
        exchange_status VARCHAR(30) NOT NULL,
        source VARCHAR(120),
        result VARCHAR(500),
        comment VARCHAR(1000),
        PRIMARY KEY (structure_ref, case_id)
    );
CREATE TABLE IF NOT EXISTS tw_hr_case_expected_documents (
        structure_ref VARCHAR(80) NOT NULL,
        case_id VARCHAR(100) NOT NULL,
        document_code VARCHAR(100) NOT NULL,
        document_label VARCHAR(240) NOT NULL,
        required INTEGER NOT NULL,
        PRIMARY KEY (structure_ref, case_id, document_code)
    );
CREATE TABLE IF NOT EXISTS tw_hr_audit_events (
        structure_ref VARCHAR(80) NOT NULL,
        event_id VARCHAR(100) NOT NULL,
        event_kind VARCHAR(60) NOT NULL,
        target_kind VARCHAR(40) NOT NULL,
        target_ref VARCHAR(120) NOT NULL,
        occurred_at VARCHAR(40) NOT NULL,
        actor_ref VARCHAR(120),
        source VARCHAR(120),
        PRIMARY KEY (structure_ref, event_id)
    );
CREATE TABLE IF NOT EXISTS tw_hr_audit_fields (
        structure_ref VARCHAR(80) NOT NULL,
        event_id VARCHAR(100) NOT NULL,
        position INTEGER NOT NULL,
        field_key VARCHAR(120) NOT NULL,
        field_value VARCHAR(1000) NOT NULL,
        PRIMARY KEY (structure_ref, event_id, position)
    );
CREATE INDEX idx_tw_hr_cases_status ON tw_hr_cases(structure_ref, status, due_on);
CREATE INDEX idx_tw_hr_cases_subject ON tw_hr_cases(structure_ref, subject_kind, subject_identifier);
CREATE INDEX idx_tw_hr_cases_organization ON tw_hr_cases(structure_ref, organization_code, status);
CREATE INDEX idx_tw_hr_audit_target ON tw_hr_audit_events(structure_ref, target_kind, target_ref, occurred_at);
INSERT INTO tw_hr_schema_versions(component, schema_version) VALUES ('hr_cases_runtime', 1);
