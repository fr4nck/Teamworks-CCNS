from pathlib import Path

from scripts.audit_wx_classic_api import audit, unexpected_findings


def test_no_wx_classic_references_remain() -> None:
    findings = audit(Path("teamworks"))
    assert findings == [], f"API wxPython Classic restantes : {findings}"
    assert unexpected_findings(findings) == []
