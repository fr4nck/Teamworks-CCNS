from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "collect_qt_vanilla_mysql_evidence.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("qt_mysql_evidence", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_database_and_sha_guards():
    tool = _load_tool()

    assert tool._validate_database("base_qt_vanilla_recette") == "base_qt_vanilla_recette"
    assert tool._validate_sha("a" * 40) == "a" * 40

    for invalid in ("prod", "base-recette", "qt_vanilla_recette;DROP"):
        try:
            tool._validate_database(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Nom de base accepté à tort : {invalid}")

    try:
        tool._validate_sha("abc")
    except ValueError:
        pass
    else:
        raise AssertionError("SHA court accepté à tort")


def test_nearest_rank_and_median_are_deterministic():
    tool = _load_tool()

    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert tool._median(values) == 3.0
    assert tool._nearest_rank(values, 0.95) == 5.0

    even = [1.0, 2.0, 3.0, 4.0]
    assert tool._median(even) == 2.5


def test_compare_only_claims_environment_and_schema_gate(tmp_path):
    tool = _load_tool()

    before = {
        "rc_sha": "a" * 40,
        "database": "base_qt_vanilla_recette",
        "mysql_version": "5.5.62",
        "schema": {
            "tables_hash": "t",
            "columns_hash": "c",
            "indexes_hash": "i",
        },
        "counts": {
            "personnes": 100,
            "contrats": 50,
            "presences": 200,
            "scenarios": 20,
            "deplacements": 10,
            "remboursements": 5,
        },
        "processlist": {"count": 1},
    }
    after = json.loads(json.dumps(before))
    after["counts"]["contrats"] = 51

    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    output = tmp_path / "compare.json"
    before_path.write_text(json.dumps(before), encoding="utf-8")
    after_path.write_text(json.dumps(after), encoding="utf-8")

    args = argparse.Namespace(before=before_path, after=after_path, output=output)
    assert tool._compare(args) == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["automatic_schema_gate"] is True
    assert report["count_deltas"]["contrats"] == 1
    assert "automatic_integrity_gate" not in report


def test_performance_gate_requires_all_tests_and_ten_samples(tmp_path):
    tool = _load_tool()

    csv_path = tmp_path / "perf.csv"
    output = tmp_path / "perf.json"

    lines = ["test_id,qt_seconds,wx_seconds"]
    for test_id, (p50_limit, _p95_limit) in tool.PERFORMANCE_THRESHOLDS.items():
        qt_value = max(0.01, p50_limit * 0.5)
        wx_value = qt_value
        for _ in range(10):
            lines.append(f"{test_id},{qt_value},{wx_value}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    args = argparse.Namespace(
        input=csv_path,
        output=output,
        minimum_samples=10,
    )
    assert tool._performance(args) == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["automatic_performance_gate"] is True
    assert report["missing_tests"] == []


def test_performance_ratio_over_120_requires_manual_analysis(tmp_path):
    tool = _load_tool()

    csv_path = tmp_path / "perf.csv"
    output = tmp_path / "perf.json"

    lines = ["test_id,qt_seconds,wx_seconds"]
    for test_id, (p50_limit, _p95_limit) in tool.PERFORMANCE_THRESHOLDS.items():
        qt_value = max(0.01, p50_limit * 0.5)
        wx_value = qt_value
        if test_id == "P-03":
            wx_value = qt_value / 1.30
        for _ in range(10):
            lines.append(f"{test_id},{qt_value},{wx_value}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    args = argparse.Namespace(
        input=csv_path,
        output=output,
        minimum_samples=10,
    )
    assert tool._performance(args) == 2

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["tests"]["P-03"]["verdict"] == "ANALYSE"
    assert report["automatic_performance_gate"] is False


def test_tool_never_accepts_password_on_command_line():
    source = TOOL.read_text(encoding="utf-8")

    assert "TEAMWORKS_MYSQL_PASSWORD" in source
    assert '"--password"' not in source
    assert "'--password'" not in source
    assert "SHOW PROCESSLIST" in source
    assert "info" not in source.lower().split("SHOW PROCESSLIST")[1][:200]
