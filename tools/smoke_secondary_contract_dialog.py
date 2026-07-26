#!/usr/bin/env python3
"""Construit l'assistant de contrat réel sur un contrat d'exemple sous Windows."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
SOURCE = TEAMWORKS_DIR / "Teamworks.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_contract_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "contract-dialog-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:imports", flush=True)
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Creation_contrat as _smoke_contract

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDcontrat, IDpersonne FROM contrats ORDER BY IDcontrat LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucun contrat disponible pour le smoke contrat")
                _smoke_contract_id, _smoke_person_id = _smoke_rows[0]

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:dialog", flush=True)
                _smoke_dialog = _smoke_contract.Dialog(
                    frame,
                    IDcontrat=_smoke_contract_id,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_dialog.Show()
                wx.Yield()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:assertions", flush=True)
                assert _smoke_dialog.nbrePages == 6
                assert _smoke_dialog.pageVisible == 1
                assert len(_smoke_dialog.listePages) == 6
                assert all(hasattr(_smoke_dialog, "page%d" % number) for number in range(1, 7))
                assert _smoke_dialog.page1.IsShown()
                assert not _smoke_dialog.page2.IsShown()
                assert not _smoke_dialog.bouton_retour.IsEnabled()
                assert _smoke_dialog.bouton_suite.IsEnabled()
                assert _smoke_dialog.bouton_annuler.IsEnabled()
                assert _smoke_dialog.dictContrats["IDcontrat"] == _smoke_contract_id
                assert _smoke_dialog.dictContrats["IDpersonne"] == _smoke_person_id
                assert _smoke_dialog.GetTitle() == "Modification d'un contrat"
                print("TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY", flush=True)
                _smoke_dialog.Destroy()
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    source = SOURCE.read_text(encoding="iso-8859-15")
    marker_count = source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
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
    paths = [str(ROOT), str(TEAMWORKS_DIR)]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
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
            timeout=150,
            check=False,
        )
        output = decode_output(result.stdout) + "\n" + decode_output(result.stderr)
        write_diagnostic(return_code=result.returncode, marker_count=marker_count, output=output)
        if result.returncode != 0 or FAILURE_MARKER in output:
            return result.returncode or 1
        if READY_MARKER not in output:
            return 2
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(return_code=3, marker_count=marker_count, output=output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
