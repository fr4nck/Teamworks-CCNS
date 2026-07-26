#!/usr/bin/env python3
"""Add a deterministic main-window smoke mode to the legacy Teamworks entry point."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Teamworks.py"

OLD = '''        frame.Show()   

        # Affiche une annonce si c'est un premier démarrage du logiciel
        frame.Annonce()
'''

NEW = '''        frame.Show()

        # Mode de validation fonctionnelle automatisée : la fenêtre principale
        # est réellement construite et affichée, puis la boucle wx est arrêtée
        # proprement sans ouvrir d'assistant ni de fichier utilisateur.
        if os.environ.get("TEAMWORKS_SMOKE_MODE") == "main-window":
            print("TEAMWORKS_SMOKE_MAIN_WINDOW_READY", flush=True)
            wx.CallLater(5000, self.ExitMainLoop)
            return True

        # Affiche une annonce si c'est un premier démarrage du logiciel
        frame.Annonce()
'''


def main() -> int:
    source = TARGET.read_text(encoding="iso-8859-15")
    count = source.count(OLD)
    if count != 1:
        raise SystemExit(f"expected exactly one main-window startup block, found {count}")

    TARGET.write_text(source.replace(OLD, NEW), encoding="iso-8859-15")
    print(f"updated {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
