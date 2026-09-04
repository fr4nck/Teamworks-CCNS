import pytest

from domain.hr_connections import HrAuditField


@pytest.mark.parametrize(
    "key",
    [
        "secret_note",
        "session_cookie",
        "user_access_token_reference",
        "health_note",
        "medical_comment",
        "diagnosis_code",
        "pathology_reference",
    ],
)
def test_audit_field_rejects_sensitive_key_fragments(key):
    with pytest.raises(ValueError):
        HrAuditField.create(key=key, value="ne-doit-pas-etre-journalise")
