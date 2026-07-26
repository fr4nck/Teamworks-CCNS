#!/usr/bin/env python3
"""Remplace l'intersection de filtres Recrutement basée sur exec."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Ol" / "OL_candidatures.py"
ENCODING = "iso-8859-15"

OLD = '''        else :
            # Si plusieurs listes 
            texteFonction = ""
            index = 0
            for liste in listeListes :
                texteFonction += "set(listeListes[%d]) & " % index
                index += 1
            texteFonction = texteFonction[:-3]
            exec("listeID=%s" % texteFonction)
            listeID = list(listeID)
'''

NEW = '''        else :
            # Si plusieurs listes, conserve uniquement les candidatures communes.
            listeID = list(set.intersection(*(set(liste) for liste in listeListes)))
'''


def main() -> int:
    source = TARGET.read_text(encoding=ENCODING)
    if NEW in source:
        print("Intersection des filtres Recrutement déjà corrigée")
        return 0
    if source.count(OLD) != 1:
        raise RuntimeError("bloc historique d'intersection absent ou ambigu")
    updated = source.replace(OLD, NEW, 1)
    if 'exec("listeID=%s" % texteFonction)' in updated:
        raise RuntimeError("exec résiduel dans l'intersection des filtres")
    compile(updated, str(TARGET), "exec")
    TARGET.write_text(updated, encoding=ENCODING)
    print("Intersection des filtres Recrutement corrigée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
