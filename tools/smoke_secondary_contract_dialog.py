#!/usr/bin/env python3
"""Construit l'assistant de contrat réel et parcourt ses six étapes sous Windows."""

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

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:initial", flush=True)
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

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:forward", flush=True)
                for _smoke_target_page in range(2, 7):
                    _smoke_dialog.Onbouton_suite(None)
                    wx.Yield()
                    assert _smoke_dialog.pageVisible == _smoke_target_page
                    assert getattr(_smoke_dialog, "page%d" % _smoke_target_page).IsShown()
                    assert _smoke_dialog.bouton_retour.IsEnabled()

                assert _smoke_dialog.pageVisible == 6
                assert _smoke_dialog.page6.IsShown()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:backward", flush=True)
                for _smoke_target_page in range(5, 0, -1):
                    _smoke_dialog.Onbouton_retour(None)
                    wx.Yield()
                    assert _smoke_dialog.pageVisible == _smoke_target_page
                    assert getattr(_smoke_dialog, "page%d" % _smoke_target_page).IsShown()

                assert _smoke_dialog.pageVisible == 1
                assert _smoke_dialog.page1.IsShown()
                assert not _smoke_dialog.bouton_retour.IsEnabled()
                assert _smoke_dialog.bouton_suite.IsEnabled()
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
    if READY_MARKER not in patched_source or FAILURE_MARKER not in patched_source:
        raise RuntimeError("injection des marqueurs du contrat absente")
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
    print(f"::error title=Contract dialog smoke failed::{summary}")


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
        write_diagnostic(return_code=result.returncode, marker_count=marker_count, output=output)
        if result.returncode != 0 or FAILURE_MARKER in output:
            github_error_summary(output)
            return result.returncode or 1
        if READY_MARKER not in output:
            github_error_summary(output)
            print("marqueur du contrat absent", file=sys.stderr)
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
