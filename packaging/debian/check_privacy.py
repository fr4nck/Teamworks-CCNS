#!/usr/bin/env python3
"""Contrôle conservateur des données sensibles du paquet Debian Teamworks-CCNS.

Ne publie jamais les valeurs détectées. Un résultat OK n'est pas un audit
humain de chaque ressource ou des dépendances téléchargées depuis PyPI.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path


APP = "opt/teamworks-ccns/app/"
VENDOR = "opt/teamworks-ccns/vendor/"
ONLY_FILES = {
    "usr/bin/teamworks-ccns",
    "usr/share/applications/teamworks-ccns.desktop",
    "usr/share/pixmaps/teamworks-ccns.png",
    "DEBIAN/control",
}
SOURCES = ("teamworks/", "application/", "domain/", "infrastructure/")
REQUIRED = {
    APP + "VERSION",
    APP + "teamworks/Teamworks.py",
    "usr/bin/teamworks-ccns",
    "usr/share/applications/teamworks-ccns.desktop",
    "usr/share/pixmaps/teamworks-ccns.png",
    "DEBIAN/control",
}
DANGEROUS_SUFFIXES = (
    ".db", ".db3", ".sqlite", ".sqlite3", ".sql", ".dump",
    ".bak", ".backup", ".old", ".swp", ".log",
    ".csv", ".xlsx", ".xls", ".ods", ".odt", ".docx", ".pptx", ".pdf",
    ".eml", ".msg", ".mbox", ".pst", ".ics", ".sqlite-wal", ".sqlite-shm",
    ".p12", ".pfx", ".pem", ".key", ".kdbx", ".ovpn",
    ".zip", ".7z", ".rar", ".tar", ".tar.gz", ".tar.xz", ".tgz",
)
DANGEROUS_NAMES = {
    "id_rsa", "id_ed25519", "id_ecdsa",
    ".env", ".netrc", ".pgpass", "credentials.json",
    "secrets.json", "secrets.yaml", "secrets.yml", "my.cnf",
}
DANGEROUS_DIRS = {
    ".ssh", ".config", ".venv", "venv", "__pycache__",
    "backups", "backup", "sauvegardes", "dumps", "logs",
    "exports", "private", "secrets", "data_personnelles",
}
TEXT_SUFFIXES = {
    ".py", ".pyi", ".sh", ".js", ".ts", ".html", ".css",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".txt", ".md", ".rst", ".xml", ".desktop", ".conf",
}
SECRET_PATTERNS = (
    ("clé privée", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----|-----BEGIN PGP PRIVATE KEY BLOCK-----")),
    ("jeton de service", re.compile(
        rb"\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
        rb"AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{20,})\b"
    )),
    ("secret littéral", re.compile(
        rb"(?i)\b(?:password|passwd|passphrase|client_secret|api_key|"
        rb"access_token|auth_token|db_password|smtp_password|private_key)"
        rb"\b\s*[:=]\s*['\"][^\r\n'\"]{6,}['\"]"
    )),
)
# Évite les faux positifs sur les modèles de fonctions et la documentation
# du code métier ; un doute est un blocage, jamais une exclusion automatique.


def _autorise(rel):
    if rel in ONLY_FILES:
        return True
    if rel.startswith(VENDOR):
        return True
    if rel.startswith(APP):
        suffixe = rel[len(APP):]
        return suffixe == "VERSION" or suffixe.startswith(SOURCES)
    return False


def _risque_nom(rel):
    parts = [s.lower() for s in Path(rel).parts]
    nom = parts[-1]
    if any(p in DANGEROUS_DIRS for p in parts[:-1]):
        return "répertoire de données personnelles/configuration"
    if (nom in DANGEROUS_NAMES or nom.startswith(".env.")
            or nom.endswith("~")
            or any(nom.endswith(s) for s in DANGEROUS_SUFFIXES)):
        return "nom ou extension de fichier sensible"
    return None


def examiner(dossier):
    dossier = Path(dossier)
    erreurs = []
    fichiers = set()
    nombre = 0
    for p in dossier.rglob("*"):
        if p.is_dir() and not p.is_symlink():
            continue
        rel = p.relative_to(dossier).as_posix()
        fichiers.add(rel)
        nombre += 1
        if p.is_symlink():
            erreurs.append((rel, "lien symbolique non contrôlé"))
            continue
        if not p.is_file() or not _autorise(rel):
            erreurs.append((rel, "fichier extérieur à la liste blanche"))
            continue
        risque = _risque_nom(rel)
        if risque:
            erreurs.append((rel, risque))
            continue
        # Les dépendances PyPI sont des paquets tiers publics : on y contrôle
        # les noms à risque, mais pas les exemples de code qu'elles embarquent.
        if rel.startswith(VENDOR):
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES and p.name != "VERSION":
            continue
        donnees = p.read_bytes()
        if len(donnees) > 4 * 1024 * 1024:
            erreurs.append((rel, "texte de taille excessive, revue requise"))
            continue
        for motif_nom, motif in SECRET_PATTERNS:
            if motif.search(donnees):
                erreurs.append((rel, motif_nom))
    for rel in sorted(REQUIRED - fichiers):
        erreurs.append((rel, "fichier attendu absent"))

    if erreurs:
        for rel, raison in sorted(set(erreurs)):
            print("REFUS:", rel, "-", raison, file=sys.stderr)
        print("CONFIDENTIALITE=ECHEC (valeurs non affichées)", file=sys.stderr)
        return 1
    print("CONFIDENTIALITE=PASS_CONTROLES_AUTOMATIQUES")
    print("FICHIERS_CONTROLES=", nombre)
    return 0


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stage", type=Path, help="arborescence du paquet avant dpkg-deb")
    group.add_argument("--deb", type=Path, help="archive .deb à contrôler")
    args = parser.parse_args()
    if args.stage:
        return examiner(args.stage)
    if not args.deb.is_file():
        parser.error("paquet introuvable")
    with tempfile.TemporaryDirectory(prefix="teamworks-deb-audit-") as tmp:
        subprocess.run(["dpkg-deb", "--extract", str(args.deb), tmp], check=True)
        subprocess.run(
            ["dpkg-deb", "--control", str(args.deb), str(Path(tmp) / "DEBIAN")],
            check=True,
        )
        return examiner(tmp)


if __name__ == "__main__":
    raise SystemExit(main())
