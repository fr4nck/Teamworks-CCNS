from pathlib import Path

from scripts.audit_wx_classic_api import audit


def test_no_known_wx_classic_calls_remain() -> None:
    findings = audit(Path("teamworks"))
    assert findings == [], f"API wxPython Classic restantes : {findings}"
