from pathlib import Path

from scripts import audit_dialog_geometry


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"


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
    remaining = [record for record in records if record["findings"]]
    assert not remaining, _format_findings(remaining)
