#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Audit statique de l'iconographie Teamworks-CCNS.

Le but est de rendre mesurable la dette d'icônes historiques avant migration
progressive vers les composants sémantiques et, à terme, Fluent System Icons.
Le contrôle est volontairement non bloquant au premier passage : il produit un
inventaire exploitable par lots sans casser les écrans historiques.
"""
from __future__ import print_function

import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEFAULT_PATH = os.path.join(ROOT, "teamworks")
ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")

PATTERNS = (
    (
        "action.bitmap-button",
        "high",
        re.compile(r"\bwx\.BitmapButton\b"),
        "migrer l'action vers CTRL_Bouton_image ou un composant sémantique",
    ),
    (
        "action.toolbar-bitmap",
        "high",
        re.compile(r"\.(?:AddTool|AddLabelTool|InsertTool)\b"),
        "faire passer l'icône de barre d'outils par le moteur d'icônes responsive",
    ),
    (
        "asset.fixed-raster-path",
        "medium",
        re.compile(r"Images[/\\](?:16x16|22x22|32x32|48x48|80x80|128x128)[/\\]"),
        "ne pas supposer que la taille du fichier est la taille d'affichage",
    ),
    (
        "asset.direct-wx-bitmap",
        "medium",
        re.compile(r"\bwx\.Bitmap\b"),
        "vérifier le DPI/zoom ou déléguer le chargement au moteur commun",
    ),
    (
        "asset.image-list",
        "medium",
        re.compile(r"\bwx\.ImageList\b|\b(?:self\.)?il\.Add\("),
        "adapter la taille de l'ImageList au zoom et à la densité d'affichage",
    ),
    (
        "asset.static-bitmap",
        "low",
        re.compile(r"\bwx\.StaticBitmap\b"),
        "vérifier seulement si l'image participe à une action ou porte du sens",
    ),
    (
        "asset.window-icon-copy",
        "low",
        re.compile(r"CopyFromBitmap\b"),
        "centraliser l'icône de fenêtre si elle n'est pas déjà fournie par le branding",
    ),
)

CENTRAL_MARKERS = (
    "CTRL_Bouton_image.CTRL",
    "UTILS_Styles.ICON_SIZES",
    "_chemin_image_existant(",
)


def _read_text(path):
    data = open(path, "rb").read()
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace"), "latin-1-replace"


def _iter_python_files(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in (".git", "__pycache__")]
        for filename in files:
            if not filename.endswith(".py") or ".bak" in filename.lower():
                continue
            yield os.path.join(base, filename)


def scan(path=DEFAULT_PATH):
    path = os.path.abspath(path)
    hits = []
    files = []
    for filename in sorted(_iter_python_files(path)):
        text, encoding = _read_text(filename)
        relpath = os.path.relpath(filename, ROOT).replace(os.sep, "/")
        central = any(marker in text for marker in CENTRAL_MARKERS)
        file_hits = 0
        for lineno, line in enumerate(text.splitlines(), 1):
            for code, severity, regex, recommendation in PATTERNS:
                if not regex.search(line):
                    continue
                # Le composant central est précisément l'endroit où wx.Bitmap
                # et les chemins multi-résolution sont autorisés et maîtrisés.
                if relpath.endswith("teamworks/Ctrl/CTRL_Bouton_image.py") and code in (
                    "asset.fixed-raster-path",
                    "asset.direct-wx-bitmap",
                ):
                    continue
                hits.append({
                    "file": relpath,
                    "line": lineno,
                    "code": code,
                    "severity": severity,
                    "centralized_file": central,
                    "encoding": encoding,
                    "text": line.strip()[:220],
                    "recommendation": recommendation,
                })
                file_hits += 1
        if file_hits:
            files.append({"file": relpath, "hits": file_hits, "encoding": encoding})
    return hits, files


def summarize(hits, files):
    by_code = {}
    by_file = {}
    by_severity = {"high": 0, "medium": 0, "low": 0}
    centralized_files = set()
    for hit in hits:
        by_code[hit["code"]] = by_code.get(hit["code"], 0) + 1
        by_file[hit["file"]] = by_file.get(hit["file"], 0) + 1
        by_severity[hit["severity"]] = by_severity.get(hit["severity"], 0) + 1
        if hit["centralized_file"]:
            centralized_files.add(hit["file"])
    return {
        "total": len(hits),
        "files": len(files),
        "centralized_files": len(centralized_files),
        "by_severity": by_severity,
        "by_code": dict(sorted(by_code.items(), key=lambda item: (-item[1], item[0]))),
        "top_files": sorted(by_file.items(), key=lambda item: (-item[1], item[0]))[:40],
    }


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# Peigne iconographique Teamworks-CCNS",
        "",
        "Inventaire statique non bloquant. L'objectif est de réduire la dette par familles homogènes.",
        "",
        "- Occurrences : **%d**" % summary["total"],
        "- Fichiers concernés : **%d**" % summary["files"],
        "- Alertes hautes : **%d**" % summary["by_severity"].get("high", 0),
        "- Alertes moyennes : **%d**" % summary["by_severity"].get("medium", 0),
        "",
        "## Par famille",
        "",
        "| Famille | Occurrences |",
        "| --- | ---: |",
    ]
    for code, count in summary["by_code"].items():
        lines.append("| `%s` | %d |" % (code, count))
    lines.extend([
        "",
        "## Fichiers prioritaires",
        "",
        "| Fichier | Occurrences |",
        "| --- | ---: |",
    ])
    for filename, count in summary["top_files"]:
        lines.append("| `%s` | %d |" % (filename, count))
    lines.extend([
        "",
        "## Règle de migration",
        "",
        "1. Actions cliquables : supprimer progressivement `wx.BitmapButton` au profit du composant commun.",
        "2. Barres d'outils et ImageList : taille pilotée par le zoom/DPI, pas par le dossier raster d'origine.",
        "3. Ressources multi-résolution : choisir la meilleure source puis redimensionner, jamais agrandir aveuglément un 16 px.",
        "4. Décorations et photos : ne pas les confondre avec les icônes d'action ; elles sont auditées mais moins prioritaires.",
        "5. À terme : remplacer les pictogrammes d'action disparates par le référentiel Fluent System Icons sans modifier le métier.",
        "",
    ])
    return "\n".join(lines)


def build_report(path=DEFAULT_PATH):
    hits, files = scan(path)
    return {"summary": summarize(hits, files), "hits": hits, "files": files}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Peigne iconographique Teamworks-CCNS")
    parser.add_argument("--path", default=DEFAULT_PATH, help="Racine à analyser")
    parser.add_argument("--json", dest="json_path", help="Écrire le rapport JSON")
    parser.add_argument("--markdown", dest="markdown_path", help="Écrire le rapport Markdown")
    args = parser.parse_args(argv)

    report = build_report(args.path)
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
    if args.markdown_path:
        with open(args.markdown_path, "w", encoding="utf-8") as handle:
            handle.write(render_markdown(report))

    summary = report["summary"]
    print(
        "Iconographie : {total} occurrence(s), {files} fichier(s), "
        "{high} haute(s), {medium} moyenne(s)".format(
            total=summary["total"],
            files=summary["files"],
            high=summary["by_severity"].get("high", 0),
            medium=summary["by_severity"].get("medium", 0),
        )
    )
    for code, count in summary["by_code"].items():
        print("%4d  %s" % (count, code))
    print("\nPriorité :")
    for filename, count in summary["top_files"][:15]:
        print("%4d  %s" % (count, filename))
    return 0


if __name__ == "__main__":
    sys.exit(main())
