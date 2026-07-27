#!/usr/bin/env python3
"""Construit une fiche individuelle existante et parcourt ses pages sous wxPython."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
SOURCE = TEAMWORKS_DIR / "Teamworks.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_person_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-dialog-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_DIALOG_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_DIALOG_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                print("TEAMWORKS_SMOKE_PERSON_STAGE:imports", flush=True)
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Fiche_individuelle as _smoke_person

                print("TEAMWORKS_SMOKE_PERSON_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke fiche individuelle")
                _smoke_person_id = _smoke_rows[0][0]

                print("TEAMWORKS_SMOKE_PERSON_STAGE:dialog", flush=True)
                _smoke_dialog = _smoke_person.Dialog(frame, IDpersonne=_smoke_person_id)
                _smoke_dialog.Show()
                wx.Yield()

                print("TEAMWORKS_SMOKE_PERSON_STAGE:notebook", flush=True)
                _smoke_notebook = _smoke_dialog.notebook
                _smoke_expected_pages = (
                    "Généralités",
                    "Questionnaire",
                    "Qualifications",
                    "Contrats",
                    "Présences",
                    "Scénarios",
                    "Frais",
                    "Recrutement",
                )
                assert _smoke_dialog.IDpersonne == _smoke_person_id
                assert _smoke_dialog.GetTitle() == "Fiche individuelle"
                assert _smoke_notebook.GetPageCount() == len(_smoke_expected_pages)
                assert tuple(
                    _smoke_notebook.GetPageText(_smoke_index)
                    for _smoke_index in range(_smoke_notebook.GetPageCount())
                ) == _smoke_expected_pages

                print("TEAMWORKS_SMOKE_PERSON_STAGE:pages", flush=True)
                for _smoke_index in range(_smoke_notebook.GetPageCount()):
                    _smoke_notebook.SetSelection(_smoke_index)
                    wx.Yield()
                    assert _smoke_notebook.GetCurrentPage() is not None

                assert _smoke_notebook.pageGeneralites is not None
                assert _smoke_notebook.pageContrats is not None
                assert _smoke_notebook.pagePresences is not None
                assert _smoke_notebook.pageCandidatures is not None
                assert _smoke_dialog.bitmap_button_Ok.IsEnabled()
                # Quitter la page Généralités déclenche une sauvegarde automatique.
                # L'annulation devient alors volontairement impossible.
                assert _smoke_dialog.AnnulationImpossible is True
                assert not _smoke_dialog.bitmap_button_annuler.IsEnabled()
                print("TEAMWORKS_SMOKE_PERSON_DIALOG_READY", flush=True)
                _smoke_dialog.Destroy()
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_DIALOG_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    source = SOURCE.read_text(encoding="iso-8859-15")
    marker_count = source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(
            f"ligne marqueur du smoke principal introuvable: count={marker_count}"
        )
    patched_source = source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_source or FAILURE_MARKER not in patched_source:
        raise RuntimeError("injection des marqueurs de fiche individuelle absente")
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


def github_error_summary(output: str, max_lines: int = 40) -> None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    summary = " | ".join(lines[-max_lines:])
    summary = summary.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error title=Person dialog smoke failed::{summary}")


def write_diagnostic(*, return_code: int, marker_count: int | None, output: str) -> None:
    diagnostic = (
        f"return_code={return_code}\n"
        f"entrypoint_marker_count={marker_count}\n"
        f"ready_marker={READY_MARKER in output}\n"
        f"failure_marker={FAILURE_MARKER in output}\n"
        "--- output ---\n"
        f"{output}"
    )
    REPORT.write_text(diagnostic, encoding="utf-8")
    print(diagnostic)


def build_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["TEAMWORKS_SMOKE_MODE"] = "main-window"
    search_paths = [str(ROOT), str(TEAMWORKS_DIR)]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        search_paths.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(search_paths)
    return env


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    marker_count: int | None = None
    try:
        marker_count = build_patched_entrypoint()
        result = subprocess.run(
            [sys.executable, str(PATCHED)],
            cwd=TEAMWORKS_DIR,
            env=build_environment(),
            capture_output=True,
            timeout=180,
            check=False,
        )
        output = decode_output(result.stdout) + "\n" + decode_output(result.stderr)
        write_diagnostic(
            return_code=result.returncode,
            marker_count=marker_count,
            output=output,
        )
        if result.returncode != 0 or FAILURE_MARKER in output:
            github_error_summary(output)
            return result.returncode or 1
        if READY_MARKER not in output:
            github_error_summary(output)
            print("marqueur de fiche individuelle absent", file=sys.stderr)
            return 2
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(return_code=3, marker_count=marker_count, output=output)
        github_error_summary(output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
