#!/usr/bin/env python3
"""Valide l'inventaire statique du publipostage contre sa page de référence."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "Utils" / "UTILS_Publipostage_donnees.py"
WIKI = ROOT / "docs" / "wiki"
REF = WIKI / "Mots-clés de publipostage.md"
TARGETS = {
    "Importation_personne",
    "Importation_candidat",
    "Importation_candidature",
    "Importation_contrat",
}
REQUIRED_INDEX_ANCHORS = {
    "index-alphabetique",
    "index-contexte-individu",
    "index-contexte-candidat",
    "index-contexte-candidature",
    "index-contexte-contrat",
    "index-usage-identite",
    "index-usage-coordonnees",
    "index-usage-recrutement",
    "index-usage-contrat",
    "index-usage-remuneration",
    "index-usage-ccns",
    "index-usage-cee",
    "exemples-modeles",
    "champs-personnalises",
}


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


def checks(keys: set[str]) -> list[str]:
    errors: list[str] = []
    ref = REF.read_text(encoding="utf-8")
    anchors = re.findall(r'<a id="([^"]+)"></a>', ref)
    anchor_set = set(anchors)
    headings = set(re.findall(r'^### `\{([A-Z0-9_]+)\}`\s*$', ref, flags=re.M))

    duplicates = sorted({anchor for anchor in anchors if anchors.count(anchor) > 1})
    if duplicates:
        errors.append("ancres dupliquées: " + ", ".join(duplicates))

    for key in sorted(keys):
        if key not in headings:
            errors.append(f"mot-clé exposé mais fiche absente: {key}")
        if slug(key) not in anchor_set:
            errors.append(f"ancre absente pour {key}: {slug(key)}")

    extra = headings - keys
    if extra:
        errors.append("fiches standard absentes du code: " + ", ".join(sorted(extra)))

    missing_indexes = REQUIRED_INDEX_ANCHORS - anchor_set
    if missing_indexes:
        errors.append("index/sections de référence absents: " + ", ".join(sorted(missing_indexes)))

    examples = (
        "Bonjour {CIVILITE} {NOM}",
        "Votre contrat débute le {DATEDEBUT}",
        "Salaire brut mensuel : {SALAIREBRUTMENSUEL}",
    )
    for example in examples:
        if example not in ref:
            errors.append(f"exemple attendu absent: {example}")

    for match in re.findall(r'Mots-clés-de-publipostage#([A-Za-z0-9_-]+)', "\n".join(
        p.read_text(encoding="utf-8") for p in WIKI.glob("*.md")
    )):
        if match not in anchor_set:
            errors.append(f"lien vers une ancre de mot-clé absente: {match}")

    return errors


def main() -> int:
    if not SOURCE.exists() or not REF.exists():
        print("ERREUR: source ou page de référence introuvable")
        return 2
    keys = static_keys()
    errors = checks(keys)
    print(f"Mots-clés statiques détectés: {len(keys)}")
    if errors:
        for err in errors:
            print("ERREUR:", err)
        return 1
    print("OK: inventaire, 47 fiches, ancres, index, exemples et liens de mots-clés contrôlés.")
    print("NOTE: champs personnalisés en base exclus du rapprochement statique par conception.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
