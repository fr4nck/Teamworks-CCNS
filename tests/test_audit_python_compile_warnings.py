from pathlib import Path

from scripts.audit_runtime_risks import audit_compile_warnings


def _audit(tmp_path: Path, source: str):
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")
    return audit_compile_warnings(tmp_path, path, source.splitlines())


def test_literal_identity_warning_is_reported(tmp_path):
    findings = _audit(tmp_path, "value = 'x'\nresult = value is 'x'\n")
    assert any(item.category == "python-compile-warning" for item in findings)
    assert any("literal" in item.detail.lower() for item in findings)


def test_invalid_escape_warning_is_reported(tmp_path):
    findings = _audit(tmp_path, "pattern = '\\s+'\n")
    assert any(item.category == "python-compile-warning" for item in findings)
    assert any("escape sequence" in item.detail.lower() for item in findings)


def test_clean_source_has_no_compile_warning(tmp_path):
    findings = _audit(tmp_path, "value = 'x'\nresult = value == 'x'\npattern = r'\\s+'\n")
    assert findings == []
