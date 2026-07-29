from pathlib import Path

from scripts.audit_wx_classic_api import audit, unexpected_findings


def test_no_unexpected_wx_classic_references_remain() -> None:
    findings = audit(Path("teamworks"))
    unexpected = unexpected_findings(findings)
    assert unexpected == [], f"API wxPython Classic inattendues : {unexpected}"


def test_known_legacy_stockcursor_references_are_still_explicit() -> None:
    findings = audit(Path("teamworks"))
    stock_cursor = {
        (str(item["path"]), str(item["api"]))
        for item in findings
        if item["api"] == "wx.StockCursor"
    }
    assert stock_cursor == {
        ("teamworks/Ctrl/CTRL_Planning.py", "wx.StockCursor"),
        ("teamworks/Dlg/DLG_Editeur_photo.py", "wx.StockCursor"),
    }
