"""Tests de non-regression de l'audit geometrique wx."""

from pathlib import Path

import pytest

from scripts import audit_dialog_geometry as geometry


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"


@pytest.mark.parametrize(
    "statement",
    [
        "sizer.Add(self.notebook, 1, wx.EXPAND)",
        "sizer.Add(self.panel, 1, wx.ALL | wx.EXPAND, 10)",
        "sizer.Add(page, 1, wx.EXPAND, 0)",
        "sizer.Add(self.content, proportion=1, flag=wx.EXPAND)",
    ],
)
def test_expanding_child_is_recognized(statement):
    result = geometry.classify("wx.RESIZE_BORDER\n" + statement)
    assert result["expandable"]
    assert not any(
        item["code"] == "resizable-without-expandable-content"
        for item in result["findings"]
    )


@pytest.mark.parametrize(
    "statement",
    [
        "sizer.Add(self.label, 0, wx.EXPAND)",
        "sizer.Add(self.button, 0, wx.EXPAND)",
        "sizer.AddStretchSpacer(1)",
        "sizer.Add(self.field, 1, wx.ALL)",
    ],
)
def test_non_expanding_child_is_not_misclassified(statement):
    result = geometry.classify("wx.RESIZE_BORDER\n" + statement)
    assert not result["expandable"]
    assert any(
        item["code"] == "resizable-without-expandable-content"
        for item in result["findings"]
    )


@pytest.mark.parametrize(
    "filename",
    [
        "DLG_Filtre_texte.py",
        "DLG_Creation_contrat.py",
        "DLG_Fiche_individuelle_core.py",
    ],
)
def test_known_resizable_dialogue_is_recognized(filename):
    records = [
        record
        for record in geometry.scan(str(TEAMWORKS))
        if Path(record["file"]).name == filename
    ]
    assert records, "Dialogue absent : " + filename
    assert all(record["expandable"] for record in records)


def test_audit_keeps_medium_findings_visible():
    records = geometry.scan(str(TEAMWORKS))
    summary = geometry.summarize(records)
    assert summary["counts"]["dialogs"] > 0
    assert summary["counts"]["medium"] > 0
    assert "literal-window-size" in summary["by_code"]
