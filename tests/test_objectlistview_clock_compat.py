# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "teamworks" / "ObjectListView" / "__init__.py"
IMPLEMENTATION = ROOT / "teamworks" / "ObjectListView" / "ObjectListView.py"


def test_objectlistview_restores_removed_time_clock():
    source = PACKAGE.read_text(encoding="utf-8")
    assert 'if not hasattr(time, "clock"):' in source
    assert "time.clock = time.monotonic" in source


def test_clock_compatibility_is_installed_before_legacy_import():
    source = PACKAGE.read_text(encoding="utf-8")
    assert source.index("time.clock = time.monotonic") < source.index(
        "from . ObjectListView import"
    )


def test_legacy_batching_calls_are_covered():
    source = IMPLEMENTATION.read_text(encoding="utf-8")
    assert source.count("time.clock()") >= 10
    assert "class BatchedUpdate" in source


def test_existing_clock_is_not_overwritten():
    source = PACKAGE.read_text(encoding="utf-8")
    block = source.split('if not hasattr(time, "clock"):', 1)[1].split(
        "__version__", 1
    )[0]
    assert "else:" not in block
