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
