from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "teamworks" / "Utils" / "UTILS_Styles.py"
ORGANISATION = ROOT / "teamworks" / "Dlg" / "DLG_Organisation.py"
REFERENCES = ROOT / "teamworks" / "Dlg" / "DLG_References_admin.py"


def test_field_roles_are_central_and_font_metric_driven() -> None:
    source = STYLES.read_text(encoding="utf-8")
    for role in (
        "FIELD_XS", "FIELD_CODE", "FIELD_POSTAL_CODE", "FIELD_DATE",
        "FIELD_TIME", "FIELD_NUMBER", "FIELD_PERCENT", "FIELD_MONEY",
        "FIELD_PHONE", "FIELD_NIR", "FIELD_SIRET", "FIELD_IBAN",
        "FIELD_NAME", "FIELD_CITY", "FIELD_EMAIL", "FIELD_ADDRESS",
        "FIELD_TEXT", "FIELD_LONG_TEXT",
    ):
        assert role in source
    assert "control.GetTextExtent" in source
    assert "control.SetMinSize" in source
    assert "def GetFieldSizerFlag" in source


def test_short_administrative_fields_consume_shared_roles() -> None:
    organisation = ORGANISATION.read_text(encoding="utf-8")
    references = REFERENCES.read_text(encoding="utf-8")
    assert "UTILS_Styles.ApplyFieldRole" in organisation
    assert '"code_postal": UTILS_Styles.FIELD_POSTAL_CODE' in organisation
    assert '"siret": UTILS_Styles.FIELD_SIRET' in organisation
    assert "UTILS_Styles.ApplyFieldRole" in references
    assert '"medecine_telephone": UTILS_Styles.FIELD_PHONE' in references
    assert "UTILS_Styles.GetFieldSizerFlag" in organisation
    assert "UTILS_Styles.GetFieldSizerFlag" in references
