#!/usr/bin/env python3
"""Inventaire statique reproductible des dépendances candidates à Connecthys.

Le scanner produit des *candidats* : seule une référence explicite à Connecthys
située dans un périmètre actif peut faire échouer ``--fail-on-active-brand``.
Les autres catégories servent à orienter l'analyse humaine (réseau,
synchronisation, secrets, configuration, automatisation, transferts).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urlparse

SELF_PATHS = {
    "tools/audit_connecthys.py",
    "tests/test_audit_connecthys.py",
    "docs/audit_sortie_connecthys.md",
}

ARCHIVE_PARTS = {"patches", "archive", "archives"}
DOCUMENTATION_ROOTS = {"docs"}
TEST_TOOL_ROOTS = {"tests", "tools"}
TOOLING_ROOTS = {".github"}

ACTIVE_ROOTS = {
    "application",
    "domain",
    "infrastructure",
    "migrations",
    "packaging",
    "scripts",
    "teamworks",
}

ROOT_ACTIVE_NAMES = {
    "LANCER_TEAMWORKS_WINDOWS.cmd",
    "Lancer-Teamworks-CCNS.bat",
    "run_teamworks.py",
    "setup.py",
    "setup_cxfreeze.bat",
    "setup_rc1.py",
}

ROOT_ACTIVE_SUFFIXES = {
    ".py",
    ".bat",
    ".cmd",
    ".ps1",
    ".sh",
    ".ini",
    ".cfg",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".toml",
}

PATTERNS: dict[str, re.Pattern[str]] = {
    # Blocant seulement si le scope est actif.
    "brand": re.compile(r"(?i)connect[\s_-]*hys"),
    # Candidats forts : primitives réseau ou URLs explicites.
    "url": re.compile(r"(?i)\b(?:https?|ftp|sftp)://[^\s\"'<>()[\]{}]+"),
    "network_api": re.compile(
        r"(?i)\b(?:requests\s*\.|urllib(?:2|3)?\b|urlopen\s*\(|"
        r"http\.client\b|httplib\b|ftplib\b|paramiko\b|socket\s*\.|"
        r"smtplib\b|xmlrpc\b|webhook\b|curl\b|wget\b)"
    ),
    # Concepts proches d'un portail / d'une synchronisation, sans conclure à Connecthys.
    "sync_portal": re.compile(
        r"(?i)\b(?:sync(?:hron\w*)?|synchron\w*|portail\w*|upload\w*|"
        r"download\w*|remote\w*|push\w*|pull\w*|webhook\w*)\b"
    ),
    # Indices de secrets ou d'identifiants techniques.
    "auth_secret": re.compile(
        r"(?i)\b(?:token\w*|api[ _-]?key\w*|secret\w*|password\w*|passwd\w*|"
        r"mot[ _-]?de[ _-]?passe\w*|login\w*|identifiant\w*|bearer\b|basic auth\b)"
    ),
    # Démarrage / tâche périodique / fin d'application.
    "automation": re.compile(
        r"(?i)\b(?:cron\b|schtasks\b|task scheduler\b|planificateur\w*|"
        r"wx\.Timer\b|threading\.Timer\b|Timer\s*\(|EVT_CLOSE\b|atexit\b|"
        r"daemon\b|background\b|startup\b|d[eé]marrage\b)"
    ),
    # Stockage possible de paramètres hors code.
    "config_storage": re.compile(
        r"(?i)\b(?:winreg\b|registry\b|registre\b|AppData\b|ConfigParser\b|"
        r"param[eè]tre\w*|preferences?\b|GestionDB\b|sqlite\b|mysql\b)"
    ),
    # Faible signal, conservé pour satisfaire le ratissage demandé.
    "transfer_semantics": re.compile(r"(?i)\b(?:export\w*|import\w*)\b"),
}


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    category: str
    match: str
    snippet: str
    scope: str


@dataclass(frozen=True)
class SkippedFile:
    path: str
    reason: str


def normalize_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def classify_scope(relative_path: str) -> str:
    path = Path(relative_path)
    parts = path.parts
    if not parts:
        return "other"
    lower_name = path.name.lower()
    if any(part.lower() in ARCHIVE_PARTS for part in parts) or ".bak" in lower_name:
        return "historical_archive"
    first = parts[0]
    if first in DOCUMENTATION_ROOTS:
        return "documentation"
    if first in TEST_TOOL_ROOTS:
        return "test_or_tool"
    if first in TOOLING_ROOTS:
        return "tooling_config"
    if first in ACTIVE_ROOTS:
        return "active"
    if len(parts) == 1 and (
        path.name in ROOT_ACTIVE_NAMES or path.suffix.lower() in ROOT_ACTIVE_SUFFIXES
    ):
        return "active"
    return "other"


def git_tracked_files(root: Path) -> list[Path]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return sorted(path for path in root.rglob("*") if path.is_file())
    names = [name for name in proc.stdout.decode("utf-8").split("\0") if name]
    return [root / name for name in names]


def decode_text(path: Path) -> tuple[str | None, str | None]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, f"lecture impossible: {exc}"
    if b"\0" in data[:8192]:
        return None, "binaire (octet NUL)"
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding), None
        except UnicodeDecodeError:
            pass
    return None, "texte non UTF-8"


def scan_text(relative_path: str, text: str) -> list[Hit]:
    scope = classify_scope(relative_path)
    hits: list[Hit] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = " ".join(line.strip().split())
        if not stripped:
            continue
        for category, pattern in PATTERNS.items():
            matches = list(pattern.finditer(line))
            if not matches:
                continue
            # Une ligne/catégorie suffit ; la chaîne exacte reste utile comme preuve.
            match = matches[0].group(0)
            hits.append(
                Hit(
                    path=relative_path,
                    line=line_no,
                    category=category,
                    match=match[:160],
                    snippet=stripped[:280],
                    scope=scope,
                )
            )
    return hits


def scan_repository(root: Path) -> tuple[list[Hit], list[SkippedFile], int]:
    hits: list[Hit] = []
    skipped: list[SkippedFile] = []
    files = git_tracked_files(root)
    scanned_count = 0
    for path in files:
        relative = normalize_path(path, root)
        if relative in SELF_PATHS:
            continue
        text, error = decode_text(path)
        if text is None:
            skipped.append(SkippedFile(relative, error or "non texte"))
            continue
        scanned_count += 1
        hits.extend(scan_text(relative, text))
    return hits, skipped, scanned_count


def extract_domains(hits: Iterable[Hit]) -> Counter[str]:
    domains: Counter[str] = Counter()
    for hit in hits:
        if hit.category != "url":
            continue
        hostname = urlparse(hit.match.rstrip(".,;:")).hostname
        if hostname:
            domains[hostname.lower()] += 1
    return domains


def build_report(root: Path, hits: Sequence[Hit], skipped: Sequence[SkippedFile], scanned_count: int) -> dict:
    category_counts = Counter(hit.category for hit in hits)
    scope_counts = Counter(hit.scope for hit in hits)
    active_brand = [hit for hit in hits if hit.category == "brand" and hit.scope == "active"]
    brand_all = [hit for hit in hits if hit.category == "brand"]
    high_signal = [
        hit
        for hit in hits
        if hit.category in {"brand", "url", "network_api", "sync_portal", "automation"}
    ]
    files_by_category: dict[str, list[str]] = defaultdict(list)
    for category in PATTERNS:
        files_by_category[category] = sorted({hit.path for hit in hits if hit.category == category})
    return {
        "root": str(root),
        "scanned_text_files": scanned_count,
        "skipped_files": [asdict(item) for item in skipped],
        "counts": {
            "total_hits": len(hits),
            "brand_hits": len(brand_all),
            "active_brand_hits": len(active_brand),
            "high_signal_hits": len(high_signal),
            "by_category": dict(sorted(category_counts.items())),
            "by_scope": dict(sorted(scope_counts.items())),
        },
        "domains": dict(extract_domains(hits).most_common()),
        "files_by_category": dict(files_by_category),
        "hits": [asdict(hit) for hit in hits],
    }


def markdown_report(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "# Inventaire statique Connecthys",
        "",
        "> Ce rapport contient des candidats statiques. Un candidat n'est pas une dépendance confirmée.",
        "",
        "## Synthèse",
        "",
        f"- fichiers texte suivis analysés : **{report['scanned_text_files']}** ;",
        f"- occurrences totales : **{counts['total_hits']}** ;",
        f"- références explicites Connecthys : **{counts['brand_hits']}** ;",
        f"- références explicites Connecthys dans le périmètre actif : **{counts['active_brand_hits']}** ;",
        f"- fichiers ignorés/non textuels : **{len(report['skipped_files'])}**.",
        "",
        "## Occurrences par catégorie",
        "",
        "| Catégorie | Occurrences |",
        "| --- | ---: |",
    ]
    for category in PATTERNS:
        lines.append(f"| `{category}` | {counts['by_category'].get(category, 0)} |")

    lines.extend(["", "## Domaines vus dans des URL", ""])
    if report["domains"]:
        lines.extend(["| Domaine | Occurrences |", "| --- | ---: |"])
        for domain, count in report["domains"].items():
            lines.append(f"| `{domain}` | {count} |")
    else:
        lines.append("Aucun domaine extrait.")

    lines.extend(["", "## Candidats à examiner", ""])
    selected = [
        hit
        for hit in report["hits"]
        if hit["category"] in {"brand", "url", "network_api", "sync_portal", "automation"}
    ]
    if selected:
        lines.extend(
            [
                "| Catégorie | Scope | Fichier | Ligne | Indice |",
                "| --- | --- | --- | ---: | --- |",
            ]
        )
        for hit in selected:
            snippet = hit["snippet"].replace("|", "\\|")
            lines.append(
                f"| `{hit['category']}` | `{hit['scope']}` | `{hit['path']}` | "
                f"{hit['line']} | `{snippet}` |"
            )
    else:
        lines.append("Aucun candidat à signal fort.")

    if report["skipped_files"]:
        lines.extend(["", "## Fichiers non inspectés comme texte", ""])
        for item in report["skipped_files"]:
            lines.append(f"- `{item['path']}` — {item['reason']}")

    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".", help="racine du dépôt")
    parser.add_argument("--json", dest="json_path", help="écrire le rapport JSON")
    parser.add_argument("--markdown", dest="markdown_path", help="écrire le rapport Markdown")
    parser.add_argument(
        "--fail-on-active-brand",
        action="store_true",
        help="échouer si Connecthys apparaît dans un fichier classé actif",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.path).resolve()
    hits, skipped, scanned_count = scan_repository(root)
    report = build_report(root, hits, skipped, scanned_count)

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.markdown_path:
        Path(args.markdown_path).write_text(markdown_report(report), encoding="utf-8")

    counts = report["counts"]
    print(
        "Audit Connecthys : "
        f"{report['scanned_text_files']} fichiers texte, "
        f"{counts['brand_hits']} référence(s) explicite(s), "
        f"{counts['active_brand_hits']} active(s), "
        f"{counts['high_signal_hits']} candidat(s) à signal fort, "
        f"{len(skipped)} fichier(s) non textuel(s)/illisible(s)."
    )
    if report["domains"]:
        print("Domaines URL : " + ", ".join(report["domains"].keys()))

    if args.fail_on_active_brand and counts["active_brand_hits"]:
        print("Références Connecthys actives détectées :", file=sys.stderr)
        for hit in hits:
            if hit.category == "brand" and hit.scope == "active":
                print(f"- {hit.path}:{hit.line}: {hit.snippet}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
