from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "audit_branch_absorption.py"
spec = importlib.util.spec_from_file_location("audit_branch_absorption_full", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def test_full_repository_branch_absorption_audit(capsys):
    """One-shot qualification on the audit PR; never runs on normal CI branches."""
    if os.environ.get("GITHUB_HEAD_REF") != "audit/branch-absorption":
        pytest.skip("one-shot audit only on audit/branch-absorption")

    # actions/checkout is intentionally shallow in the normal CI.  This test
    # fetches history only for this audit PR, without changing the workflow.
    _git("fetch", "--unshallow", "origin", check=False)
    fetch = _git(
        "fetch",
        "--no-tags",
        "--prune",
        "origin",
        "+refs/heads/*:refs/remotes/origin/*",
        check=False,
    )
    assert fetch.returncode == 0, fetch.stderr

    git = mod.Git(ROOT)
    slug = mod.repository_slug(git, "origin")
    assert slug == "fr4nck/Teamworks-CCNS"
    prs = mod.GitHubClient(slug, os.environ.get("GITHUB_TOKEN")).list_prs()

    reports = mod.analyze_repository(
        root=ROOT,
        remote="origin",
        targets=list(mod.DEFAULT_STRUCTURAL),
        structural=list(mod.DEFAULT_STRUCTURAL),
        prs=prs,
        run_tests=False,
        python_executable=sys.executable,
        timeout_seconds=300,
    )

    # Frugal second pass: tests are expensive, so run them only where the
    # static proof says the branch could actually become SUPPRESSION SÛRE.
    git = mod.Git(ROOT)
    for report in reports:
        if report.structural or report.active_dependencies:
            continue
        best = mod.choose_target(report.target_evidence)
        if best is None:
            continue
        if not best.semantic_complete or not best.absorption_evidence:
            continue
        if not best.tests_detected:
            best.tests_result = "NO_TESTS"
        else:
            target_ref = git.resolve_branch(best.target, "origin")
            assert target_ref is not None
            (
                best.tests_result,
                best.tests_returncode,
                best.tests_output_tail,
                best.tests_executed,
            ) = mod.run_tests_on_target(
                git,
                f"refs/remotes/origin/{report.branch}",
                target_ref,
                best.tests_detected,
                sys.executable,
                300,
            )
        report.verdict, report.justification, report.confidence = mod.classify(
            report.branch,
            report.structural,
            report.active_dependencies,
            report.target_evidence,
        )

    payload = mod.report_to_json(reports)
    json_path = ROOT / "branch-audit.json"
    md_path = ROOT / "branch-audit.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(mod.markdown_report(payload), encoding="utf-8")

    safe = [item for item in payload["branches"] if item["verdict"] == mod.SAFE]
    with capsys.disabled():
        print("BRANCH_AUDIT_COUNTS=" + json.dumps(payload["counts"], ensure_ascii=False), flush=True)
        print(
            "BRANCH_AUDIT_SAFE="
            + json.dumps(
                [
                    {
                        "branch": item["branch"],
                        "sha": item["head_sha"],
                        "justification": item["justification"],
                    }
                    for item in safe
                ],
                ensure_ascii=False,
            ),
            flush=True,
        )

    assert payload["counts"]["total"] >= 3
