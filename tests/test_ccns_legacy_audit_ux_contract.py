from pathlib import Path


AUDIT_DIALOG = Path("teamworks/Dlg/DLG_CCNS_audit.py")


def test_legacy_ccns_audit_hides_python_exception_details():
    source = AUDIT_DIALOG.read_text(encoding="utf-8")
    assert '"Une erreur est survenue pendant l\'audit CCNS.\\n\\n%s" % exc' not in source
    assert "LOGGER.exception(" in source


def test_legacy_ccns_audit_uses_semantic_geometry_and_initial_focus():
    source = AUDIT_DIALOG.read_text(encoding="utf-8")
    assert "SetMinSize((UTILS_Styles.Scale(760), UTILS_Styles.Scale(500)))" not in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source
    assert "self.ctrl_limit.SetFocus()" in source
