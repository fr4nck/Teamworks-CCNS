#!/usr/bin/env python3
"""Exécute le smoke principal avec construction réelle du formulaire de présence."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
SOURCE = TEAMWORKS_DIR / "Teamworks.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_presence_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "presence-dialog-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER = 'print("TEAMWORKS_SMOKE_EXAMPLE_READY")'
SECONDARY_MARKER = "TEAMWORKS_SMOKE_PRESENCE_DIALOG_READY"

INJECTION = r'''
                print("TEAMWORKS_SMOKE_EXAMPLE_READY")
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Saisie_presence as _smoke_presence

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke présence")

                _smoke_dialog = wx.Dialog(frame, title="Smoke présence")
                _smoke_panel = _smoke_presence.Panel(
                    _smoke_dialog,
                    listeDonnees=[(_smoke_rows[0][0], _smoke_datetime.date.today())],
                    mode="planning",
                )
                _smoke_panel.text_heure_debut.SetValue("09:00")
                _smoke_panel.text_heure_fin.SetValue("10:00")
                _smoke_panel.text_intitule.SetValue("Recette automatisée")
                _smoke_dialog.SetSizer(wx.BoxSizer(wx.VERTICAL))
                _smoke_dialog.GetSizer().Add(_smoke_panel, 1, wx.EXPAND)
                _smoke_dialog.GetSizer().Fit(_smoke_dialog)
                _smoke_dialog.Layout()
                _smoke_dialog.Show()
                wx.Yield()

                assert _smoke_panel.text_heure_debut.GetValue() == "09:00"
                assert _smoke_panel.text_heure_fin.GetValue() == "10:00"
                assert _smoke_panel.text_intitule.GetValue() == "Recette automatisée"
                assert _smoke_panel.listCtrl_donnees.GetItemCount() >= 1
                assert _smoke_panel.treeCtrl_categories.GetCount() >= 1
                assert _smoke_panel.bouton_ok.IsEnabled()
                assert _smoke_panel.bouton_annuler.IsEnabled()
                print("TEAMWORKS_SMOKE_PRESENCE_DIALOG_READY")
                _smoke_dialog.Destroy()
'''


def build_patched_entrypoint() -> None:
    source = SOURCE.read_text(encoding="iso-8859-15")
    if source.count(MARKER) != 1:
        raise RuntimeError("marqueur du smoke principal introuvable ou ambigu")
    PATCHED.write_text(source.replace(MARKER, INJECTION), encoding="iso-8859-15")


def decode_output(data: bytes) -> str:
    for encoding in ("utf-8", "cp1252", "iso-8859-15"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def github_error_summary(output: str, max_lines: int = 24) -> None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    tail = lines[-max_lines:]
    summary = " | ".join(tail).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error title=Presence dialog smoke failed::{summary}")


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    build_patched_entrypoint()
    env = os.environ.copy()
    env["TEAMWORKS_SMOKE_MODE"] = "1"
    command = [sys.executable, str(PATCHED)]
    try:
        result = subprocess.run(
            command,
            cwd=TEAMWORKS_DIR,
            env=env,
            capture_output=True,
            timeout=120,
            check=False,
        )
        output = decode_output(result.stdout) + "\n" + decode_output(result.stderr)
        diagnostic = (
            f"return_code={result.returncode}\n"
            f"secondary_marker={SECONDARY_MARKER in output}\n"
            "--- output ---\n"
            f"{output}"
        )
        REPORT.write_text(diagnostic, encoding="utf-8")
        print(diagnostic)
        if result.returncode != 0:
            github_error_summary(output)
            return result.returncode or 1
        if SECONDARY_MARKER not in output:
            github_error_summary(output)
            print("marqueur du formulaire de présence absent", file=sys.stderr)
            return 2
        return 0
    finally:
        PATCHED.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
