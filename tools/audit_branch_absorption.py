#!/usr/bin/env python3
"""Audit remote Git branches without deleting, merging, or rewriting anything.

The tool is deliberately conservative.  A branch is only classified as
``SUPPRESSION SÛRE`` when it is not structurally active, its changes are
accounted for in a target, its branch-specific tests pass against the target
alone, and no unexplained semantic residue remains.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence


KEEP = "CONSERVER"
SAFE = "SUPPRESSION SÛRE"
REVIEW = "À REVOIR"

DEFAULT_STRUCTURAL = ("master", "wx/master", "qt/master")
TEST_PREFIXES = ("tests/", "test/")
SQL_SUFFIXES = (".sql",)
PY_SUFFIXES = (".py",)


class AuditError(RuntimeError):
    pass


@dataclass(frozen=True)
class PullRequestRef:
    number: int
    state: str
    head: str
    base: str
    merged: bool = False
    title: str = ""


@dataclass
class TargetEvidence:
    target: str
    merge_base: str | None = None
    ancestor: bool = False
    ahead_commits: int | None = None
    behind_commits: int | None = None
    patch_total: int = 0
    patch_absorbed: int = 0
    patch_complete: bool = False
    changed_files: list[str] = field(default_factory=list)
    semantic_found: list[str] = field(default_factory=list)
    semantic_missing: list[str] = field(default_factory=list)
    tests_detected: list[str] = field(default_factory=list)
    tests_executed: list[str] = field(default_factory=list)
    tests_result: str = "NOT_RUN"
    tests_returncode: int | None = None
    tests_output_tail: str = ""
    unexplained_residue: list[str] = field(default_factory=list)

    @property
    def semantic_complete(self) -> bool:
        return not self.semantic_missing and not self.unexplained_residue

    @property
    def absorption_evidence(self) -> bool:
        return self.ancestor or self.patch_complete or (
            bool(self.semantic_found) and self.semantic_complete
        )


@dataclass
class BranchReport:
    branch: str
    head_sha: str
    last_activity: str
    prs: list[dict]
    active_dependencies: list[str]
    structural: bool
    target_evidence: list[TargetEvidence]
    verdict: str
    justification: str
    confidence: str


class Git:
    def __init__(self, root: Path):
        self.root = root

    def run(
        self,
        *args: str,
        check: bool = True,
        input_text: str | None = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd or self.root,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if check and proc.returncode:
            raise AuditError(
                "git %s failed (%s): %s"
                % (" ".join(args), proc.returncode, proc.stderr.strip())
            )
        return proc

    def out(self, *args: str, check: bool = True) -> str:
        return self.run(*args, check=check).stdout.strip()

    def ref_exists(self, ref: str) -> bool:
        return self.run("rev-parse", "--verify", "--quiet", ref, check=False).returncode == 0

    def resolve_branch(self, branch: str, remote: str) -> str | None:
        for ref in (f"refs/remotes/{remote}/{branch}", branch):
            if self.ref_exists(ref):
                return ref
        return None

    def remote_branches(self, remote: str) -> list[str]:
        prefix = f"refs/remotes/{remote}/"
        rows = self.out(
            "for-each-ref", "--format=%(refname)", f"refs/remotes/{remote}"
        ).splitlines()
        branches = []
        for row in rows:
            if not row.startswith(prefix):
                continue
            name = row[len(prefix):]
            if name == "HEAD":
                continue
            branches.append(name)
        return sorted(set(branches))

    def sha(self, ref: str) -> str:
        return self.out("rev-parse", ref)

    def last_activity(self, ref: str) -> str:
        return self.out("log", "-1", "--format=%cI", ref)

    def merge_base(self, a: str, b: str) -> str | None:
        proc = self.run("merge-base", a, b, check=False)
        return (proc.stdout.strip() or None) if proc.returncode == 0 else None

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        return self.run(
            "merge-base", "--is-ancestor", ancestor, descendant, check=False
        ).returncode == 0

    def count(self, revision_range: str) -> int:
        return int(self.out("rev-list", "--count", revision_range) or "0")

    def changed_files(self, base: str, head: str) -> list[str]:
        output = self.out("diff", "--name-only", "--find-renames", base, head)
        return [line for line in output.splitlines() if line]

    def file_at(self, ref: str, path: str) -> bytes | None:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc.stdout if proc.returncode == 0 else None

    def commits(self, revision_range: str) -> list[str]:
        output = self.out("rev-list", "--reverse", revision_range)
        return [line for line in output.splitlines() if line]

    def patch_id(self, commit: str) -> str | None:
        show = subprocess.run(
            ["git", "show", "--pretty=format:", "--patch", "--binary", commit],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if show.returncode:
            return None
        patch = subprocess.run(
            ["git", "patch-id", "--stable"],
            cwd=self.root,
            input=show.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if patch.returncode or not patch.stdout.strip():
            return None
        return patch.stdout.decode("utf-8", errors="replace").split()[0]


class GitHubClient:
    def __init__(self, slug: str, token: str | None = None):
        self.slug = slug
        self.token = token

    def _get_json(self, url: str) -> object:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "teamworks-branch-audit/1",
                **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_prs(self) -> list[PullRequestRef]:
        prs: list[PullRequestRef] = []
        for page in range(1, 100):
            url = (
                f"https://api.github.com/repos/{self.slug}/pulls"
                f"?state=all&per_page=100&page={page}&sort=updated&direction=desc"
            )
            payload = self._get_json(url)
            if not isinstance(payload, list):
                raise AuditError("unexpected GitHub pull request response")
            if not payload:
                break
            for item in payload:
                prs.append(
                    PullRequestRef(
                        number=int(item["number"]),
                        state=str(item["state"]),
                        head=str(item["head"]["ref"]),
                        base=str(item["base"]["ref"]),
                        merged=bool(item.get("merged_at")),
                        title=str(item.get("title") or ""),
                    )
                )
            if len(payload) < 100:
                break
        return prs


def repository_slug(git: Git, remote: str) -> str | None:
    url = git.out("remote", "get-url", remote, check=False)
    if not url:
        return None
    match = re.search(r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$", url)
    return match.group(1) if match else None


def _python_symbols(source: bytes, path: str) -> set[str]:
    try:
        text = source.decode("utf-8")
        tree = ast.parse(text, filename=path)
    except (UnicodeDecodeError, SyntaxError):
        return set()
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.add(f"py:{path}:{node.name}")
        elif isinstance(node, ast.ClassDef):
            symbols.add(f"py:{path}:{node.name}")
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.add(f"py:{path}:{node.name}.{child.name}")
    return symbols


def _sql_symbols(source: bytes, path: str) -> set[str]:
    text = source.decode("utf-8", errors="replace")
    patterns = (
        ("table", r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?([A-Za-z0-9_]+)"),
        ("index", r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+[`\"]?([A-Za-z0-9_]+)"),
        ("trigger", r"\bCREATE\s+TRIGGER\s+[`\"]?([A-Za-z0-9_]+)"),
        ("column", r"\bADD\s+(?:COLUMN\s+)?[`\"]?([A-Za-z0-9_]+)"),
        ("constraint", r"\bCONSTRAINT\s+[`\"]?([A-Za-z0-9_]+)"),
    )
    out = set()
    for kind, pattern in patterns:
        for name in re.findall(pattern, text, flags=re.IGNORECASE):
            out.add(f"sql:{path}:{kind}:{name.lower()}")
    return out


def semantic_symbols(source: bytes | None, path: str) -> set[str]:
    if source is None:
        return set()
    if path.endswith(PY_SUFFIXES):
        return _python_symbols(source, path)
    if path.endswith(SQL_SUFFIXES):
        return _sql_symbols(source, path)
    return set()


def content_fingerprint(source: bytes | None) -> str | None:
    return hashlib.sha256(source).hexdigest() if source is not None else None


def semantic_compare(
    git: Git, candidate_ref: str, target_ref: str, changed_files: Sequence[str]
) -> tuple[list[str], list[str], list[str]]:
    found: list[str] = []
    missing: list[str] = []
    residue: list[str] = []
    for path in changed_files:
        if path.startswith(TEST_PREFIXES):
            continue
        candidate = git.file_at(candidate_ref, path)
        target = git.file_at(target_ref, path)
        if candidate is None:
            continue
        if content_fingerprint(candidate) == content_fingerprint(target):
            found.append(f"file:{path}")
            continue
        candidate_symbols = semantic_symbols(candidate, path)
        target_symbols = semantic_symbols(target, path)
        if candidate_symbols:
            found.extend(sorted(candidate_symbols & target_symbols))
            missing.extend(sorted(candidate_symbols - target_symbols))
            continue
        residue.append(f"file-diff:{path}")
    return sorted(set(found)), sorted(set(missing)), sorted(set(residue))


def patch_evidence(git: Git, base: str, candidate: str, target: str) -> tuple[int, int, bool]:
    candidate_commits = git.commits(f"{base}..{candidate}")
    target_commits = git.commits(f"{base}..{target}")
    target_ids = {pid for c in target_commits if (pid := git.patch_id(c))}
    ids = [pid for c in candidate_commits if (pid := git.patch_id(c))]
    if not ids:
        return 0, 0, False
    absorbed = sum(1 for pid in ids if pid in target_ids)
    return len(ids), absorbed, absorbed == len(ids)


def test_files(git: Git, base: str, candidate: str) -> list[str]:
    return [
        path
        for path in git.changed_files(base, candidate)
        if path.startswith(TEST_PREFIXES) and path.endswith(".py")
    ]


def run_tests_on_target(
    git: Git,
    candidate_ref: str,
    target_ref: str,
    tests: Sequence[str],
    python_executable: str,
    timeout_seconds: int,
) -> tuple[str, int | None, str, list[str]]:
    if not tests:
        return "NO_TESTS", None, "", []
    with tempfile.TemporaryDirectory(prefix="teamworks-branch-audit-") as tmp:
        worktree = Path(tmp) / "target"
        add = git.run("worktree", "add", "--detach", str(worktree), target_ref, check=False)
        if add.returncode:
            return "INFRA_ERROR", add.returncode, add.stderr[-4000:], []
        copied: list[str] = []
        try:
            for path in tests:
                content = git.file_at(candidate_ref, path)
                if content is None:
                    continue
                destination = worktree / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                copied.append(path)
            if not copied:
                return "NO_TESTS", None, "", []
            try:
                proc = subprocess.run(
                    [python_executable, "-m", "pytest", "-q", *copied],
                    cwd=worktree,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                output = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
                return "TIMEOUT", None, output[-4000:], copied
            return (
                "PASS" if proc.returncode == 0 else "FAIL",
                proc.returncode,
                proc.stdout[-4000:],
                copied,
            )
        finally:
            git.run("worktree", "remove", "--force", str(worktree), check=False)
            git.run("worktree", "prune", check=False)


def choose_target(evidence: Sequence[TargetEvidence]) -> TargetEvidence | None:
    if not evidence:
        return None

    def score(item: TargetEvidence) -> tuple[int, int, int, int]:
        return (
            1 if item.tests_result == "PASS" else 0,
            1 if item.semantic_complete else 0,
            1 if item.patch_complete else 0,
            1 if item.ancestor else 0,
        )

    return max(evidence, key=score)


def classify(
    branch: str,
    structural: bool,
    active_reasons: Sequence[str],
    evidence: Sequence[TargetEvidence],
) -> tuple[str, str, str]:
    if structural:
        return KEEP, "branche structurante protégée", "high"
    if active_reasons:
        return KEEP, "; ".join(active_reasons), "high"
    best = choose_target(evidence)
    if best is None:
        return REVIEW, "aucune cible comparable n'a pu être établie", "low"
    if best.tests_result == "FAIL":
        return KEEP, f"tests propres en échec sur {best.target}", "high"
    if best.tests_result in {"INFRA_ERROR", "TIMEOUT"}:
        return REVIEW, f"tests non qualifiés sur {best.target}: {best.tests_result}", "low"
    if best.semantic_missing or best.unexplained_residue:
        detail = best.semantic_missing[:3] + best.unexplained_residue[:3]
        return KEEP, "résidu fonctionnel non absorbé: " + ", ".join(detail), "high"
    if best.tests_result == "NO_TESTS":
        return REVIEW, "aucun test propre permettant de prouver le comportement sur la cible", "medium"
    if best.tests_result == "NOT_RUN":
        return REVIEW, "tests propres non exécutés", "low"
    if best.tests_result == "PASS" and best.absorption_evidence and best.semantic_complete:
        return SAFE, f"absorption prouvée vers {best.target} et tests propres verts", "high"
    return REVIEW, f"preuves d'absorption insuffisantes vers {best.target}", "medium"


def analyze_target(
    git: Git,
    branch_ref: str,
    target_ref: str,
    target_name: str,
    run_tests: bool,
    python_executable: str,
    timeout_seconds: int,
) -> TargetEvidence:
    ev = TargetEvidence(target=target_name)
    base = git.merge_base(branch_ref, target_ref)
    if not base:
        ev.unexplained_residue.append("no-merge-base")
        return ev
    ev.merge_base = base
    ev.ancestor = git.is_ancestor(branch_ref, target_ref)
    ev.ahead_commits = git.count(f"{target_ref}..{branch_ref}")
    ev.behind_commits = git.count(f"{branch_ref}..{target_ref}")
    ev.changed_files = git.changed_files(base, branch_ref)
    ev.patch_total, ev.patch_absorbed, ev.patch_complete = patch_evidence(
        git, base, branch_ref, target_ref
    )
    ev.semantic_found, ev.semantic_missing, ev.unexplained_residue = semantic_compare(
        git, branch_ref, target_ref, ev.changed_files
    )
    ev.tests_detected = test_files(git, base, branch_ref)
    if run_tests:
        (
            ev.tests_result,
            ev.tests_returncode,
            ev.tests_output_tail,
            ev.tests_executed,
        ) = run_tests_on_target(
            git,
            branch_ref,
            target_ref,
            ev.tests_detected,
            python_executable,
            timeout_seconds,
        )
    return ev


def analyze_repository(
    root: Path,
    remote: str,
    targets: Sequence[str],
    structural: Sequence[str],
    prs: Sequence[PullRequestRef],
    run_tests: bool,
    python_executable: str,
    timeout_seconds: int,
    branches: Sequence[str] | None = None,
) -> list[BranchReport]:
    git = Git(root)
    all_branches = list(branches) if branches else git.remote_branches(remote)
    open_prs = [pr for pr in prs if pr.state == "open"]
    active_heads: dict[str, list[PullRequestRef]] = {}
    active_bases: dict[str, list[PullRequestRef]] = {}
    for pr in open_prs:
        active_heads.setdefault(pr.head, []).append(pr)
        active_bases.setdefault(pr.base, []).append(pr)

    prs_by_branch: dict[str, list[PullRequestRef]] = {}
    for pr in prs:
        prs_by_branch.setdefault(pr.head, []).append(pr)

    reports = []
    for branch in all_branches:
        branch_ref = git.resolve_branch(branch, remote)
        if not branch_ref:
            continue
        structural_flag = branch in structural
        reasons: list[str] = []
        if branch in active_heads:
            reasons.append(
                "head de PR ouverte " + ", ".join(f"#{pr.number}" for pr in active_heads[branch])
            )
        if branch in active_bases:
            reasons.append(
                "base de PR ouverte " + ", ".join(f"#{pr.number}" for pr in active_bases[branch])
            )

        evidence: list[TargetEvidence] = []
        if not structural_flag and not reasons:
            candidate_targets = list(dict.fromkeys(targets))
            for pr in prs_by_branch.get(branch, []):
                if pr.base not in candidate_targets:
                    candidate_targets.append(pr.base)
            for target in candidate_targets:
                if target == branch:
                    continue
                target_ref = git.resolve_branch(target, remote)
                if not target_ref:
                    continue
                evidence.append(
                    analyze_target(
                        git,
                        branch_ref,
                        target_ref,
                        target,
                        run_tests,
                        python_executable,
                        timeout_seconds,
                    )
                )

        verdict, justification, confidence = classify(
            branch, structural_flag, reasons, evidence
        )
        reports.append(
            BranchReport(
                branch=branch,
                head_sha=git.sha(branch_ref),
                last_activity=git.last_activity(branch_ref),
                prs=[asdict(pr) for pr in prs_by_branch.get(branch, [])],
                active_dependencies=reasons,
                structural=structural_flag,
                target_evidence=evidence,
                verdict=verdict,
                justification=justification,
                confidence=confidence,
            )
        )
    return reports


def report_to_json(reports: Sequence[BranchReport]) -> dict:
    return {
        "schema": "teamworks.branch-absorption-audit.v1",
        "counts": {
            KEEP: sum(item.verdict == KEEP for item in reports),
            SAFE: sum(item.verdict == SAFE for item in reports),
            REVIEW: sum(item.verdict == REVIEW for item in reports),
            "total": len(reports),
        },
        "branches": [
            {
                **{k: v for k, v in asdict(item).items() if k != "target_evidence"},
                "target_evidence": [asdict(ev) for ev in item.target_evidence],
            }
            for item in reports
        ],
    }


def markdown_report(payload: dict) -> str:
    counts = payload["counts"]
    lines = [
        "# Audit d'absorption des branches",
        "",
        "> Rapport non destructif : aucun merge, fermeture de PR ou suppression de branche.",
        "",
        f"- Total : **{counts['total']}**",
        f"- CONSERVER : **{counts[KEEP]}**",
        f"- SUPPRESSION SÛRE : **{counts[SAFE]}**",
        f"- À REVOIR : **{counts[REVIEW]}**",
        "",
    ]
    for verdict in (KEEP, SAFE, REVIEW):
        lines.extend([f"## {verdict}", ""])
        selected = [b for b in payload["branches"] if b["verdict"] == verdict]
        if not selected:
            lines.extend(["_Aucune branche._", ""])
            continue
        lines.extend([
            "| Branche | SHA | Dernière activité | Justification | Confiance |",
            "|---|---|---|---|---|",
        ])
        for branch in selected:
            justification = branch["justification"].replace("|", "\\|")
            lines.append(
                f"| `{branch['branch']}` | `{branch['head_sha'][:12]}` | "
                f"{branch['last_activity']} | {justification} | {branch['confidence']} |"
            )
        lines.append("")
    lines.extend([
        "## Limites",
        "",
        "- Les réécritures sémantiques sans symbole stable restent volontairement `À REVOIR`.",
        "- Les fichiers non Python/SQL modifiés sans égalité exacte sont des résidus à revoir.",
        "- Une panne ou un timeout de pytest ne produit jamais `SUPPRESSION SÛRE`.",
        "- Une branche sans tests propres ne peut pas être classée `SUPPRESSION SÛRE` automatiquement.",
        "",
    ])
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="checkout Git à auditer")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--github-repo", help="owner/repo ; déduit du remote si absent")
    parser.add_argument("--github-token-env", default="GITHUB_TOKEN")
    parser.add_argument("--target", action="append", dest="targets")
    parser.add_argument("--structural", action="append", dest="structural")
    parser.add_argument("--branch", action="append", dest="branches", help="limiter à une branche")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--test-timeout", type=int, default=900)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--prs-json", help="source PR locale alternative à GitHub")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--markdown", dest="markdown_path")
    return parser.parse_args(argv)


def load_prs(args: argparse.Namespace, git: Git) -> list[PullRequestRef]:
    if args.prs_json:
        payload = json.loads(Path(args.prs_json).read_text(encoding="utf-8"))
        return [PullRequestRef(**item) for item in payload]
    slug = args.github_repo or repository_slug(git, args.remote)
    if not slug:
        raise AuditError("GitHub repository slug is required (--github-repo owner/repo)")
    token = os.environ.get(args.github_token_env)
    return GitHubClient(slug, token=token).list_prs()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo).resolve()
    git = Git(root)
    git.run("rev-parse", "--git-dir")
    prs = load_prs(args, git)
    reports = analyze_repository(
        root=root,
        remote=args.remote,
        targets=args.targets or list(DEFAULT_STRUCTURAL),
        structural=args.structural or list(DEFAULT_STRUCTURAL),
        prs=prs,
        run_tests=args.run_tests,
        python_executable=args.python,
        timeout_seconds=args.test_timeout,
        branches=args.branches,
    )
    payload = report_to_json(reports)
    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.markdown_path:
        Path(args.markdown_path).write_text(markdown_report(payload), encoding="utf-8")
    print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
