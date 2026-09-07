import re
from pathlib import Path

from scripts import audit_dialog_geometry


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"


EXPANDING_CHILD_PANEL = re.compile(
    r"\.Add\(\s*self\.\w*panel\w*\s*,\s*1\s*,[^\n]*wx\.EXPAND",
    re.IGNORECASE,
)
EXPANDING_DATA_CONTROL = re.compile(
    r"\.Add\(\s*self\.\w*(?:list|liste|tree|grid|check)\w*\s*,\s*1\s*,[^\n]*wx\.EXPAND",
    re.IGNORECASE,
)


def _class_block(record):
    source = (ROOT / record["file"]).read_text(encoding="utf-8", errors="replace")
    for class_name, block in audit_dialog_geometry._class_blocks(source):
        if class_name == record["class"]:
            return block
    return ""


def _is_real_finding(record, finding):
    block = _class_block(record)
    code = finding["code"]

    if code == "resizable-without-expandable-content":
        if EXPANDING_CHILD_PANEL.search(block) or EXPANDING_DATA_CONTROL.search(block):
            return False

    if code == "dynamic-content-without-refit":
        without_initial_hide = block.replace(".Show(False)", "")
        if ".Show(" not in without_initial_hide and ".Hide(" not in without_initial_hide:
            return False

    return True


def _remaining_findings(records):
    remaining = []
    for record in records:
        findings = [
            finding
            for finding in record["findings"]
            if _is_real_finding(record, finding)
        ]
        if findings:
            cleaned = dict(record)
            cleaned["findings"] = findings
            remaining.append(cleaned)
    return remaining


def _format_findings(records):
    rows = []
    for record in records:
        for finding in record["findings"]:
            rows.append(
                "%s:%s:%s:%s"
                % (
                    finding["severity"],
                    record["file"],
                    record["class"],
                    finding["code"],
                )
            )
    return "\n".join(rows)


def test_wx_dialog_geometry_has_no_remaining_findings():
    records = audit_dialog_geometry.scan(str(TEAMWORKS))
    remaining = _remaining_findings(records)
    assert not remaining, _format_findings(remaining)
