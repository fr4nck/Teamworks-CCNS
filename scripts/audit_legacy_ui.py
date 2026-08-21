#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Inventaire des constructions UI héritées encore actives dans Teamworks.

L'objectif n'est pas de casser le build dès le premier passage mais de rendre la dette
visuelle mesurable, fichier par fichier. Les sauvegardes historiques sont volontairement
ignorées : seules les sources exécutables doivent être modernisées.
"""

from __future__ import print_function

import argparse
import json
import os
import re
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SCAN_ROOTS = (
    os.path.join(ROOT, "teamworks", "Ctrl"),
    os.path.join(ROOT, "teamworks", "Dlg"),
    os.path.join(ROOT, "teamworks", "Gadget.py"),
    os.path.join(ROOT, "teamworks", "Teamworks_core.py"),
)

PATTERNS = (
    ("layout.flexgrid", "high", re.compile(r"\bwx\.FlexGridSizer\b")),
    ("layout.fit", "high", re.compile(r"\.Fit\(self\)")),
    ("chrome.staticbox", "medium", re.compile(r"\bwx\.StaticBox(?:Sizer)?\b")),
    ("control.bitmapbutton", "high", re.compile(r"\bwx\.BitmapButton\b")),
    ("asset.icon16", "medium", re.compile(r"Images/16x16/")),
    ("chrome.sunken", "high", re.compile(r"\bwx\.SUNKEN_BORDER\b")),
    ("colour.white", "medium", re.compile(r"SetBackgroundColour\(wx\.WHITE\)")),
    ("colour.literal.background", "high", re.compile(r"SetBackgroundColour\(\s*\(")),
    ("colour.literal.foreground", "high", re.compile(r"SetForegroundColour\(\s*\(")),
    ("typography.manual_font", "medium", re.compile(r"\.SetFont\(")),
    ("typography.literal_font", "medium", re.compile(r"\bwx\.Font\(")),
    ("size.literal", "medium", re.compile(r"(?:SetSize|SetMinSize|SetMaxSize)\(\s*\(")),
    ("column.literal", "medium", re.compile(r"SetColumnWidth\(\s*\d+\s*,\s*\d+\s*\)")),
    ("navigation.toolbook", "high", re.compile(r"\bwx\.Toolbook\b")),
    ("agw.platebutton", "high", re.compile(r"\bplatebtn\b|\bPlateButton\b")),
)

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}


def _is_backup(path):
    name = os.path.basename(path).lower()
    return ".bak" in name or name.endswith("~")


def _iter_python_files():
    for root in SCAN_ROOTS:
        if os.path.isfile(root):
            if root.endswith(".py") and not _is_backup(root):
                yield root
            continue
        if not os.path.isdir(root):
            continue
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
            for filename in files:
                path = os.path.join(base, filename)
                if filename.endswith(".py") and not _is_backup(path):
                    yield path


def scan():
    hits = []
    for path in sorted(_iter_python_files()):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                lines = handle.readlines()
        except TypeError:  # pragma: no cover - compat Python 2 historique
            import io
            with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
                lines = handle.readlines()
        relpath = os.path.relpath(path, ROOT).replace(os.sep, "/")
        for lineno, line in enumerate(lines, 1):
            for code, severity, regex in PATTERNS:
                if regex.search(line):
                    hits.append({
                        "file": relpath,
                        "line": lineno,
                        "code": code,
                        "severity": severity,
                        "text": line.strip()[:220],
                    })
    return hits


def summarize(hits):
    by_file = {}
    by_code = {}
    for hit in hits:
        by_file[hit["file"]] = by_file.get(hit["file"], 0) + 1
        by_code[hit["code"]] = by_code.get(hit["code"], 0) + 1
    return {
        "total": len(hits),
        "files": len(by_file),
        "by_file": sorted(by_file.items(), key=lambda item: (-item[1], item[0])),
        "by_code": sorted(by_code.items(), key=lambda item: (-item[1], item[0])),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit des reliques UI historiques de Teamworks")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Sortie JSON")
    parser.add_argument(
        "--fail-on",
        choices=("medium", "high"),
        default=None,
        help="Retourne un code non nul si une occurrence atteint ce niveau",
    )
    args = parser.parse_args(argv)

    hits = scan()
    report = summarize(hits)

    if args.as_json:
        print(json.dumps({"summary": report, "hits": hits}, ensure_ascii=False, indent=2))
    else:
        print("Relique UI : %d occurrence(s) dans %d fichier(s)" % (report["total"], report["files"]))
        for path, count in report["by_file"]:
            print("%4d  %s" % (count, path))
        if report["by_code"]:
            print("\nPar famille :")
            for code, count in report["by_code"]:
                print("%4d  %s" % (count, code))

    if args.fail_on:
        threshold = SEVERITY_ORDER[args.fail_on]
        if any(SEVERITY_ORDER[hit["severity"]] >= threshold for hit in hits):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
