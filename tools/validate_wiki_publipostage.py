#!/usr/bin/env python3
"""Vérifie l'inventaire statique de publipostage et les liens du wiki.

Les mots-clés personnalisés stockés en base ne sont pas statiquement énumérables et
sont volontairement hors du rapprochement code/wiki.
"""
from __future__ import annotations
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "Utils" / "UTILS_Publipostage_donnees.py"
WIKI = ROOT / "docs" / "wiki"
REF = WIKI / "Mots-clés de publipostage.md"
TARGETS = {"Importation_personne", "Importation_candidat", "Importation_candidature", "Importation_contrat"}


def slug(key: str) -> str:
    return "publipostage-" + key.lower().replace("_", "-")


def static_keys() -> set[str]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    found: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name not in TARGETS:
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, (ast.Assign, ast.AnnAssign)):
                continue
            value = sub.value
            names = []
            if isinstance(sub, ast.Assign):
                names = [t.id for t in sub.targets if isinstance(t, ast.Name)]
            elif isinstance(sub.target, ast.Name):
                names = [sub.target.id]
            if "listeMotscles" not in names or not isinstance(value, (ast.List, ast.Tuple)):
                continue
            for item in value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str) and not item.value.startswith("_"):
                    found.add(item.value)
    return found


def wiki_checks(keys: set[str]) -> list[str]:
    errors: list[str] = []
    ref = REF.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', ref))
    headings = set(re.findall(r'^### `\{([A-Z0-9_]+)\}`\s*$', ref, flags=re.M))
    for key in sorted(keys):
        if key not in headings:
            errors.append(f"mot-clé exposé mais fiche absente: {key}")
        if slug(key) not in anchors:
            errors.append(f"ancre absente pour {key}: {slug(key)}")
    extra = headings - keys
    if extra:
        errors.append("fiches standard absentes du code: " + ", ".join(sorted(extra)))

    pages = {p.stem for p in WIKI.glob("*.md")}
    for path in WIKI.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        for inner in re.findall(r'\[\[([^\]]+)\]\]', text):
            target = inner.split("|", 1)[1] if "|" in inner else inner
            target = target.split("#", 1)[0]
            if target not in pages:
                errors.append(f"lien wiki cassé dans {path.name}: [[{inner}]]")
        for anc in re.findall(r'\]\(Mots-clés-de-publipostage#([^)]+)\)', text):
            if anc not in anchors:
                errors.append(f"ancre cible absente dans {path.name}: {anc}")
    return errors


def main() -> int:
    if not SOURCE.exists():
        print(f"ERREUR: source introuvable: {SOURCE}")
        return 2
    keys = static_keys()
    errors = wiki_checks(keys)
    print(f"Mots-clés statiques détectés: {len(keys)}")
    if errors:
        for err in errors:
            print("ERREUR:", err)
        return 1
    print("OK: inventaire, fiches, ancres et liens contrôlés.")
    print("NOTE: champs personnalisés en base exclus du contrôle statique par conception.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
