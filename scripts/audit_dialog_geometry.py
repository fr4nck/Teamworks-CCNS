#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Inventorie la géométrie des wx.Dialog et repère les fenêtres « chewing-gum ».

Ce contrôle est volontairement non bloquant : il classe la dette afin de la réduire
par lots sans casser les dialogues qui bénéficient réellement du redimensionnement.
"""
from __future__ import print_function

import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

DIALOG_CLASS = re.compile(r"^class\s+(?P<name>\w+)\s*\((?P<bases>[^\n]*wx\.Dialog[^\n]*)\)\s*:", re.MULTILINE)
NEXT_CLASS = re.compile(r"^class\s+\w+\s*\(", re.MULTILINE)
LITERAL_SIZE = re.compile(r"(?:\bsize\s*=|Set(?:Min|Max)?Size\s*\()\s*\(?\s*\d+\s*,\s*\d+")

EXPANDABLE_MARKERS = (
    "wx.ListCtrl", "ListCtrl", "wx.TreeCtrl", "TreeCtrl", "wx.Grid", "grid.Grid",
    "wx.SplitterWindow", "wx.ScrolledWindow", "ScrolledPanel", "wx.TE_MULTILINE",
    "HtmlWindow", "wx.html", "wx.richtext",
)

FIT_MARKERS = (
    "self.Fit(",
    "FitWindowToContent(",
    "ApplyWindowProfile(self, \"fit\"",
    "ApplyWindowProfile(self, 'fit'",
)

REFIT_MARKERS = FIT_MARKERS + ("RefitWindow(",)


def _read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except TypeError:  # pragma: no cover - compat historique
        import io
        with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()


def _iter_python_files(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for filename in files:
            if not filename.endswith(".py") or ".bak" in filename.lower():
                continue
            yield os.path.join(base, filename)


def _class_blocks(text):
    matches = list(DIALOG_CLASS.finditer(text))
    for match in matches:
        start = match.start()
        following = NEXT_CLASS.search(text, match.end())
        end = following.start() if following else len(text)
        yield match.group("name"), text[start:end]


def _has_any(block, markers):
    return any(marker in block for marker in markers)


def classify(block):
    resizable = "wx.RESIZE_BORDER" in block
    expandable = _has_any(block, EXPANDABLE_MARKERS)
    dynamic = ".Show(" in block or ".Hide(" in block
    fit = _has_any(block, FIT_MARKERS)
    refit = _has_any(block, REFIT_MARKERS)
    fixed_min = "SetMinSize(" in block
    fixed_max = "SetMaxSize(" in block
    literal_size = bool(LITERAL_SIZE.search(block))
    window_profile = "ApplyWindowProfile(" in block
    stretch = "AddStretchSpacer(" in block

    findings = []
    if resizable and not expandable:
        findings.append(("high", "resizable-without-expandable-content", "retirer RESIZE_BORDER ou justifier un contenu expansible"))
    if stretch and not expandable:
        findings.append(("high", "stretch-without-expandable-content", "supprimer l'espace élastique qui ne sert aucun contrôle"))
    if literal_size and not window_profile:
        findings.append(("medium", "literal-window-size", "remplacer la taille arbitraire par le profil fit ou un profil sémantique"))
    if not resizable and expandable and not fixed_min:
        findings.append(("medium", "fixed-workspace-without-minimum", "vérifier qu'une vraie zone de travail peut grandir et possède un minimum"))
    if dynamic and not refit:
        findings.append(("medium", "dynamic-content-without-refit", "appeler RefitWindow après Show/Hide ou ajout/retrait dynamique"))
    if resizable and fit and not expandable:
        findings.append(("medium", "fit-but-still-resizable", "un formulaire fit ne doit pas rester librement étirable"))

    if expandable:
        kind = "workspace"
    elif dynamic:
        kind = "dynamic-form"
    else:
        kind = "compact-form"

    return {
        "kind": kind,
        "resizable": resizable,
        "expandable": expandable,
        "dynamic": dynamic,
        "fit": fit,
        "refit": refit,
        "set_min_size": fixed_min,
        "set_max_size": fixed_max,
        "literal_size": literal_size,
        "window_profile": window_profile,
        "stretch_spacer": stretch,
        "findings": [
            {"severity": severity, "code": code, "recommendation": recommendation}
            for severity, code, recommendation in findings
        ],
    }


def scan(path):
    path = os.path.abspath(path)
    records = []
    for filename in sorted(_iter_python_files(path)):
        text = _read(filename)
        if "wx.Dialog" not in text:
            continue
        for class_name, block in _class_blocks(text):
            record = classify(block)
            record["file"] = os.path.relpath(filename, ROOT).replace(os.sep, "/")
            record["class"] = class_name
            records.append(record)
    return records


def summarize(records):
    counts = {"dialogs": len(records), "high": 0, "medium": 0, "clean": 0}
    by_code = {}
    for record in records:
        if not record["findings"]:
            counts["clean"] += 1
        for finding in record["findings"]:
            counts[finding["severity"]] += 1
            by_code[finding["code"]] = by_code.get(finding["code"], 0) + 1
    return {"counts": counts, "by_code": dict(sorted(by_code.items(), key=lambda item: (-item[1], item[0])))}


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# Audit géométrique des fenêtres wx.Dialog",
        "",
        "Inventaire statique non bloquant. Il signale les géométries suspectes mais ne remplace pas la recette visuelle.",
        "",
        "- Dialogues analysés : **%d**" % summary["counts"]["dialogs"],
        "- Alertes hautes : **%d**" % summary["counts"]["high"],
        "- Alertes moyennes : **%d**" % summary["counts"]["medium"],
        "- Dialogues sans alerte : **%d**" % summary["counts"]["clean"],
        "",
        "## Alertes",
        "",
        "| Gravité | Fichier | Classe | Type | Code | Recommandation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    severity_rank = {"high": 0, "medium": 1}
    rows = []
    for record in report["dialogs"]:
        for finding in record["findings"]:
            rows.append((severity_rank.get(finding["severity"], 9), record["file"], record["class"], record["kind"], finding))
    for _, filename, class_name, kind, finding in sorted(rows, key=lambda row: (row[0], row[1], row[2], row[4]["code"])):
        lines.append("| %s | `%s` | `%s` | %s | `%s` | %s |" % (
            finding["severity"], filename, class_name, kind, finding["code"], finding["recommendation"]
        ))
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit géométrique des wx.Dialog")
    parser.add_argument("--path", default=os.path.join(ROOT, "teamworks"), help="Racine à analyser")
    parser.add_argument("--json", dest="json_path", help="Écrire le rapport JSON")
    parser.add_argument("--markdown", dest="markdown_path", help="Écrire le rapport Markdown")
    args = parser.parse_args(argv)

    records = scan(args.path)
    report = {"summary": summarize(records), "dialogs": records}

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
    if args.markdown_path:
        with open(args.markdown_path, "w", encoding="utf-8") as handle:
            handle.write(render_markdown(report))

    counts = report["summary"]["counts"]
    print("Géométrie : {dialogs} dialogue(s), {high} alerte(s) haute(s), {medium} moyenne(s), {clean} sans alerte".format(**counts))
    for code, count in report["summary"]["by_code"].items():
        print("%4d  %s" % (count, code))
    return 0


if __name__ == "__main__":
    sys.exit(main())
