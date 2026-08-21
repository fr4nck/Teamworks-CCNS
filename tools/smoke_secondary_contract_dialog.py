#!/usr/bin/env python3
"""Construit l'assistant de contrat réel et parcourt ses six étapes sous Windows."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_contract_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_contract_smoke.py"
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
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs du contrat absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_secondary_contract_smoke as CORE"
    if import_line not in entrypoint_source:
        raise RuntimeError("import du cœur Teamworks introuvable dans la coque active")
    patched_entrypoint = entrypoint_source.replace(import_line, patched_import, 1)
    compile(patched_entrypoint, str(PATCHED), "exec")
    PATCHED.write_text(patched_entrypoint, encoding="utf-8")
    return marker_count


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    marker_count: int | None = None
    try:
        marker_count = build_patched_entrypoint()
        return_code, output = run_entrypoint(
            PATCHED,
            root=ROOT,
            teamworks_dir=TEAMWORKS_DIR,
            timeout=180,
        )
        write_diagnostic(
            REPORT,
            return_code=return_code,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("Contract dialog smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Contract dialog smoke failed", output)
            print("marqueur du contrat absent", file=sys.stderr)
            return 2
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(
            REPORT,
            return_code=3,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        github_error_summary("Contract dialog smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())