#!/usr/bin/env python3
"""Construit la page Recrutement et exerce ses listes, filtres et tris sous Windows."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
SOURCE = TEAMWORKS_DIR / "Teamworks.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_recruitment_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "recruitment-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                import GestionDB as _smoke_gestiondb
                from Ctrl import CTRL_Page_candidatures as _smoke_recruitment
                from Ol import OL_candidatures as _smoke_candidates

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke recrutement")
                _smoke_person_id = _smoke_rows[0][0]

                _smoke_host = wx.Frame(frame, title="Smoke recrutement")
                _smoke_panel = _smoke_recruitment.Panel(_smoke_host, IDpersonne=_smoke_person_id)
                _smoke_panel.Show()
                _smoke_host.Show()
                wx.Yield()

                assert _smoke_panel.ctrl_candidatures is not None
                assert _smoke_panel.ctrl_entretiens is not None
                assert _smoke_panel.ctrl_candidatures.GetColumnCount() >= 7
                assert _smoke_panel.ctrl_entretiens.GetColumnCount() >= 1
                assert isinstance(_smoke_panel.ctrl_candidatures.donnees, list)
                assert isinstance(_smoke_panel.ctrl_entretiens.donnees, list)

                _smoke_panel.ctrl_candidatures.MAJ()
                _smoke_panel.ctrl_entretiens.MAJ()
                wx.Yield()

                # Vérifie l'intersection déterministe de plusieurs filtres métier.
                _smoke_candidates.DICT_DISPONIBILITES = {
                    1: [(1, __import__('datetime').date(2026, 1, 1), __import__('datetime').date(2026, 12, 31))],
                    2: [(2, __import__('datetime').date(2026, 1, 1), __import__('datetime').date(2026, 12, 31))],
                }
                _smoke_candidates.DICT_CAND_FONCTIONS = {1: [10], 2: [20]}
                _smoke_candidates.DICT_CAND_AFFECTATIONS = {1: [30], 2: [30]}
                _smoke_filters = [
                    {"nomControle": "candidature_dispo", "valeur": (__import__('datetime').date(2026, 6, 1), __import__('datetime').date(2026, 6, 30)), "sql": ""},
                    {"nomControle": "candidature_fonctions", "valeur": [(10, "Animation")], "sql": ""},
                    {"nomControle": "candidature_affectations", "valeur": [(30, "ALSH")], "sql": ""},
                ]
                _smoke_ids, _smoke_sql = _smoke_panel.ctrl_candidatures.GetListeFiltres(_smoke_filters)
                assert _smoke_ids == [1]
                assert _smoke_sql == ""

                # Le tri doit pouvoir être demandé sur une colonne réellement construite.
                if _smoke_panel.ctrl_candidatures.GetColumnCount() > 1:
                    _smoke_panel.ctrl_candidatures.SortBy(1)
                    wx.Yield()

                assert _smoke_panel.bouton_candidatures_ajouter.IsEnabled()
                assert _smoke_panel.bouton_entretiens_ajouter.IsEnabled()
                print("TEAMWORKS_SMOKE_RECRUITMENT_READY", flush=True)
                _smoke_host.Destroy()
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_RECRUITMENT_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    source = SOURCE.read_text(encoding="iso-8859-15")
    marker_count = source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur du smoke principal introuvable: {marker_count}")
    patched_source = source.replace(MARKER_LINE, INJECTION, 1)
    compile(patched_source, str(PATCHED), "exec")
    PATCHED.write_text(patched_source, encoding="iso-8859-15")
    return marker_count


def decode_output(data: bytes) -> str:
    for encoding in ("utf-8", "cp1252", "iso-8859-15"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def build_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["TEAMWORKS_SMOKE_MODE"] = "main-window"
    paths = [str(ROOT), str(TEAMWORKS_DIR)]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    marker_count = None
    try:
        marker_count = build_patched_entrypoint()
        result = subprocess.run(
            [sys.executable, str(PATCHED)], cwd=TEAMWORKS_DIR,
            env=build_environment(), capture_output=True, timeout=180, check=False,
        )
        output = decode_output(result.stdout) + "\n" + decode_output(result.stderr)
        REPORT.write_text(
            f"return_code={result.returncode}\nentrypoint_marker_count={marker_count}\n--- output ---\n{output}",
            encoding="utf-8",
        )
        print(output)
        if result.returncode != 0 or FAILURE_MARKER in output or READY_MARKER not in output:
            summary = " | ".join(line.strip() for line in output.splitlines()[-40:] if line.strip())
            print(f"::error title=Recruitment smoke failed::{summary}")
            return result.returncode or 1
        return 0
    except Exception:
        diagnostic = traceback.format_exc()
        REPORT.write_text(diagnostic, encoding="utf-8")
        print(diagnostic)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
