from pathlib import Path

from tools.find_redundant_phoenix_branches import (
    Finding,
    find_redundant_phoenix_branches,
    format_findings,
)


def test_detects_identical_phoenix_branches(tmp_path: Path):
    source = tmp_path / "sample.py"
    source.write_text(
        """
import wx

if 'phoenix' in wx.PlatformInfo:
    value = 1
else:
    value = 1
""".lstrip(),
        encoding="utf-8",
    )

    assert find_redundant_phoenix_branches(tmp_path) == [
        Finding(path=source, line=3)
    ]


def test_ignores_distinct_branches(tmp_path: Path):
    source = tmp_path / "sample.py"
    source.write_text(
        """
import wx

if 'phoenix' in wx.PlatformInfo:
    value = 1
else:
    value = 2
""".lstrip(),
        encoding="utf-8",
    )

    assert find_redundant_phoenix_branches(tmp_path) == []


def test_formats_findings():
    findings = [Finding(path=Path("teamworks/example.py"), line=42)]

    assert format_findings(findings) == "teamworks/example.py:42"
