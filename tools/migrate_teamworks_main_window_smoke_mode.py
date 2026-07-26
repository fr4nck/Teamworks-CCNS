#!/usr/bin/env python3
"""Add or verify the deterministic main-window smoke mode."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Teamworks.py"
MARKER = 'TEAMWORKS_SMOKE_MAIN_WINDOW_READY'

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

    # A richer smoke mode (for example the tabs smoke) legitimately keeps the
    # same readiness marker while extending the body. Treat it as migrated.
    if source.count(MARKER) == 1:
        print(f"already migrated {TARGET.relative_to(ROOT)}")
        return 0

    old_count = source.count(OLD)
    if old_count == 1:
        TARGET.write_text(source.replace(OLD, NEW), encoding="iso-8859-15")
        print(f"updated {TARGET.relative_to(ROOT)}")
        return 0

    raise SystemExit(
        "unexpected main-window startup state: "
        f"legacy_blocks={old_count}, marker_count={source.count(MARKER)}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
