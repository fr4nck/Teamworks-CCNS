from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "audit_branch_absorption.py"
spec = importlib.util.spec_from_file_location("audit_branch_absorption", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def write(repo: Path, path: str, content: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "master")
    git(repo, "config", "user.email", "audit@example.test")
    git(repo, "config", "user.name", "Audit Test")
    write(repo, "app.py", "def value():\n    return 1\n")
    write(
        repo,
        "tests/test_app.py",
        "from app import value\n\ndef test_value():\n    assert value() == 1\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "base")
    return repo


def test_active_branch_is_always_kept():
    verdict, reason, confidence = mod.classify(
        "feature/x", False, ["head de PR ouverte #10"], []
    )
    assert verdict == mod.KEEP
    assert "#10" in reason
    assert confidence == "high"


def test_branch_without_own_tests_is_never_automatically_safe():
    ev = mod.TargetEvidence(
        target="master",
        ancestor=True,
        patch_complete=True,
        tests_result="NO_TESTS",
    )
    verdict, reason, _ = mod.classify("old", False, [], [ev])
    assert verdict == mod.REVIEW
    assert "aucun test propre" in reason


def test_missing_semantic_symbol_keeps_branch():
    ev = mod.TargetEvidence(
        target="master",
        patch_complete=True,
        tests_result="PASS",
        semantic_missing=["py:domain/x.py:ImportantRule"],
    )
    verdict, reason, _ = mod.classify("feature/x", False, [], [ev])
    assert verdict == mod.KEEP
    assert "ImportantRule" in reason


def test_cherry_picked_branch_with_tests_can_be_safe(tmp_path: Path):
    repo = init_repo(tmp_path)

    git(repo, "checkout", "-b", "feature/change")
    write(repo, "app.py", "def value():\n    return 2\n")
    write(
        repo,
        "tests/test_app.py",
        "from app import value\n\ndef test_value():\n    assert value() == 2\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "change behavior")
    feature = git(repo, "rev-parse", "HEAD")

    git(repo, "checkout", "master")
    write(repo, "app.py", "def value():\n    return 2\n")
    write(
        repo,
        "tests/test_app.py",
        "from app import value\n\ndef test_value():\n    assert value() == 2\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "squashed equivalent")

    helper = mod.Git(repo)
    ev = mod.analyze_target(
        helper,
        feature,
        "master",
        "master",
        run_tests=True,
        python_executable=sys.executable,
        timeout_seconds=60,
    )
    assert ev.tests_result == "PASS"
    assert not ev.semantic_missing
    assert not ev.unexplained_residue
    assert ev.semantic_complete
    assert ev.absorption_evidence

    verdict, _, confidence = mod.classify("feature/change", False, [], [ev])
    assert verdict == mod.SAFE
    assert confidence == "high"


def test_wrong_target_fails_reinjected_branch_test(tmp_path: Path):
    repo = init_repo(tmp_path)
    git(repo, "checkout", "-b", "feature/change")
    write(repo, "app.py", "def value():\n    return 3\n")
    write(
        repo,
        "tests/test_app.py",
        "from app import value\n\ndef test_value():\n    assert value() == 3\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "feature")
    feature = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "master")

    ev = mod.analyze_target(
        mod.Git(repo),
        feature,
        "master",
        "master",
        run_tests=True,
        python_executable=sys.executable,
        timeout_seconds=60,
    )
    assert ev.tests_result == "FAIL"
    verdict, _, _ = mod.classify("feature/change", False, [], [ev])
    assert verdict == mod.KEEP
