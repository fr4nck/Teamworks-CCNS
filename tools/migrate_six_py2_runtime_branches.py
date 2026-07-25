#!/usr/bin/env python3
"""Remove allowlisted Python 2 runtime branches whose Python 3 path is definitive."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path


REPLACEMENTS = {
    Path("teamworks/Dlg/DLG_Saisie_procedure_sauvegarde.py"): [
        (
            """            if six.PY2:\n                labelPoste = _(u\"Ce poste (%s)\") % socket.gethostname().decode(\"iso-8859-15\")\n            else :\n                labelPoste = _(u\"Ce poste (%s)\") % socket.gethostname()\n""",
            """            labelPoste = _(u\"Ce poste (%s)\") % socket.gethostname()\n""",
        ),
    ],
    Path("teamworks/Utils/UTILS_Cryptage_fichier.py"): [
        (
            """\t\tif six.PY2:\n\t\t\tmessage  = message + '_'\n\t\telse :\n\t\t\tmessage = message + b'_'\n""",
            """\t\tmessage = message + b'_'\n""",
        ),
    ],
    Path("teamworks/Ctrl/CTRL_ObjectListView.py"): [
        (
            """        if six.PY2:\n            groups.sort(key=_getLowerCaseKey, reverse=(not ascending))\n        else:\n            groups = sorted(groups, key=_getLowerCaseKey,\n                            reverse=(not ascending))\n            # update self.groups which is used e.g. in _SetGroups\n            self.groups = groups\n""",
            """        groups = sorted(groups, key=_getLowerCaseKey,\n                        reverse=(not ascending))\n        # update self.groups which is used e.g. in _SetGroups\n        self.groups = groups\n""",
        ),
    ],
    Path("teamworks/ObjectListView/ObjectListView.py"): [
        (
            """        if six.PY2:\n            groups.sort(key=_getLowerCaseKey, reverse=(not ascending))\n        else:\n            groups = sorted(groups, key=_getLowerCaseKey,\n                            reverse=(not ascending))\n            # update self.groups which is used e.g. in _SetGroups\n            self.groups = groups\n""",
            """        groups = sorted(groups, key=_getLowerCaseKey,\n                        reverse=(not ascending))\n        # update self.groups which is used e.g. in _SetGroups\n        self.groups = groups\n""",
        ),
    ],
    Path("teamworks/Outils/mail/message.py"): [
        (
            """    if six.PY2:\n        # On Python 2, use the stdlib since `email.headerregistry` doesn't exist.\n        from email.utils import formataddr\n        if localpart and domain:\n            addr = '@'.join([localpart, domain])\n        return formataddr((nm, addr))\n\n""",
            "",
        ),
        (
            """        if six.PY2:\n            g.flatten(self, unixfrom=unixfrom)\n        else:\n            g.flatten(self, unixfrom=unixfrom, linesep=linesep)\n""",
            """        g.flatten(self, unixfrom=unixfrom, linesep=linesep)\n""",
        ),
        (
            """    if six.PY2:\n        as_bytes = as_string\n    else:\n        def as_bytes(self, unixfrom=False, linesep='\\n'):\n""",
            """    def as_bytes(self, unixfrom=False, linesep='\\n'):\n""",
        ),
        (
            """                if six.PY2:\n                    filename = filename.encode('utf-8')\n                filename = ('utf-8', '', filename)\n""",
            """                filename = ('utf-8', '', filename)\n""",
        ),
    ],
    Path("teamworks/Utils/UTILS_Sauvegarde.py"): [
        (
            """            if six.PY2:\n                args = args.encode('utf8')\n""",
            "",
        ),
        (
            """                try :\n                    if six.PY2:\n                        out = str(out).decode(\"iso-8859-15\")\n                except :\n                    pass\n""",
            "",
        ),
        (
            """                try :\n                    if six.PY2:\n                        err = str(err).decode(\"iso-8859-15\")\n                except :\n                    pass\n""",
            "",
        ),
        (
            """        if six.PY3:\n            motdepasse = motdepasse.decode('utf8')\n""",
            """        motdepasse = motdepasse.decode('utf8')\n""",
        ),
        (
            """            if six.PY2:\n                args = args.encode(\"iso-8859-15\")\n""",
            "",
        ),
        (
            """                if six.PY2:\n                    out = str(out).decode(\"iso-8859-15\")\n""",
            "",
        ),
    ],
    Path("teamworks/Utils/UTILS_Envoi_email.py"): [
        (
            """                    if six.PY2:\n                        err = str(erreur).decode(\"iso-8859-15\")\n                    else:\n                        err = six.text_type(erreur)\n""",
            """                    err = six.text_type(erreur)\n""",
        ),
    ],
    Path("teamworks/Teamworks.py"): [
        (
            """from six.moves.urllib.request import urlopen\n\nif six.PY2:\n    import shelve\n    import dbhash\n    import anydbm\n""",
            """from urllib.request import urlopen\n""",
        ),
        (
            """        if six.PY2:\n            version_python = \"2\"\n        else :\n            version_python = \"3\"\n""",
            """        version_python = \"3\"\n""",
        ),
    ],
    Path("teamworks/GestionDB.py"): [
        (
            """        ID, prenom, genre = ligne.split(\";\")\n            genre = genre.decode(\"iso-8859-15\")\n        listeDonnees = [(\"prenom\", prenom), (\"genre\", genre),]\n""",
            """        ID, prenom, genre = ligne.split(\";\")\n        listeDonnees = [(\"prenom\", prenom), (\"genre\", genre),]\n""",
        ),
    ],
}


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate_file(path: Path, replacements: list[tuple[str, str]], write: bool) -> int:
    source, encoding = read_source(path)
    changed = 0
    for old, new in replacements:
        count = source.count(old)
        if count not in (0, 1):
            raise SystemExit(f"Unexpected match count in {path}: {count}")
        if count:
            source = source.replace(old, new)
            changed += 1
    if changed and write:
        path.write_text(source, encoding=encoding, newline="")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    total = 0
    for relative_path, replacements in REPLACEMENTS.items():
        path = args.root / relative_path
        changed = migrate_file(path, replacements, write=args.write)
        if changed:
            print(f"{relative_path}: {changed}")
            total += changed

    print(f"obsolete_runtime_branches={total}")
    if args.check and total:
        raise SystemExit(f"{total} obsolete six.PY2 runtime branches remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
