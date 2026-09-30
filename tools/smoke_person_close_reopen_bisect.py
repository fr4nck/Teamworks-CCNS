#!/usr/bin/env python3
"""Isole quel effet de Fermer() rend le prochain contrôle natif instable sous MSW."""

from __future__ import annotations

import argparse
from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_person_close_bisect_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_person_close_bisect_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-close-reopen-bisect-smoke"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_CLOSE_BISECT_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_CLOSE_BISECT_FAILED"

SCENARIOS = (
    "fermer-1",
    "fermer-2",
    "fermer-3",
    "save-only-3",
    "callbacks-only-3",
    "refresh-only-3",
    "save-callbacks-3",
    "save-refresh-3",
    "callbacks-refresh-3",
)


def _scenario_parts(scenario: str) -> tuple[str, int]:
    mode, count = scenario.rsplit("-", 1)
    return mode, int(count)


def build_injection(scenario: str) -> str:
    mode, close_cycles = _scenario_parts(scenario)
    return f'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                import wx as _smoke_wx
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Fiche_individuelle as _smoke_person
                from Dlg import DLG_Config_sauvegarde as _smoke_backup

                _smoke_mode = {mode!r}
                _smoke_close_cycles = {close_cycles}

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1"
                )
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible")
                _smoke_person_id = _smoke_rows[0][0]

                def _smoke_destroy(_window):
                    if _window and not _window.IsBeingDeleted():
                        _window.Destroy()
                    _smoke_wx.Yield()

                for _smoke_cycle in range(_smoke_close_cycles):
                    print(
                        "TEAMWORKS_SMOKE_PERSON_CLOSE_BISECT_CYCLE:%s:%d/%d"
                        % (_smoke_mode, _smoke_cycle + 1, _smoke_close_cycles),
                        flush=True,
                    )
                    _smoke_dialog = _smoke_person.Dialog(
                        frame,
                        IDpersonne=_smoke_person_id,
                    )
                    _smoke_dialog.Show()
                    _smoke_dialog.Layout()
                    _smoke_wx.Yield()

                    if _smoke_mode == "fermer":
                        if _smoke_dialog.Fermer(save=True) is not True:
                            raise RuntimeError("Fermer(save=True) a échoué")
                        _smoke_wx.Yield()
                    else:
                        if "save" in _smoke_mode:
                            _smoke_dialog._sauvegarder_pages()
                        if "callbacks" in _smoke_mode:
                            if not _smoke_dialog._arreter_callbacks_avant_fermeture():
                                raise RuntimeError("arrêt callbacks refusé")
                        if "refresh" in _smoke_mode:
                            _smoke_dialog._rafraichir_frame_personnes(save=True)
                        _smoke_destroy(_smoke_dialog)

                print(
                    "TEAMWORKS_SMOKE_PERSON_CLOSE_BISECT_BACKUP:%s"
                    % _smoke_mode,
                    flush=True,
                )
                _smoke_probe = _smoke_backup.MyFrame(frame)
                _smoke_probe.Show()
                _smoke_probe.Layout()
                _smoke_wx.Yield()
                _smoke_destroy(_smoke_probe)

                print("TEAMWORKS_SMOKE_PERSON_CLOSE_BISECT_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_CLOSE_BISECT_FAILED", flush=True)
            _smoke_wx.CallAfter(self.ExitMainLoop)
            return True
'''


def build_patched_entrypoint(scenario: str) -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(
            f"ligne marqueur du smoke principal introuvable: count={marker_count}"
        )
    patched_core_source = core_source.replace(
        MARKER_LINE,
        build_injection(scenario),
        1,
    )
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_person_close_bisect_smoke as CORE"
    if import_line not in entrypoint_source:
        raise RuntimeError("import du cœur Teamworks introuvable")
    patched_entrypoint = entrypoint_source.replace(import_line, patched_import, 1)
    compile(patched_entrypoint, str(PATCHED), "exec")
    PATCHED.write_text(patched_entrypoint, encoding="utf-8")
    return marker_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / f"diagnostic-{args.scenario}.txt"
    marker_count = None
    try:
        marker_count = build_patched_entrypoint(args.scenario)
        return_code, output = run_entrypoint(
            PATCHED,
            root=ROOT,
            teamworks_dir=TEAMWORKS_DIR,
            timeout=300,
        )
        write_diagnostic(
            report,
            return_code=return_code,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        if return_code != 0 or FAILURE_MARKER in output or READY_MARKER not in output:
            github_error_summary(
                f"Person close/reopen bisect failed ({args.scenario})",
                output,
            )
            return return_code or 1
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(
            report,
            return_code=3,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        github_error_summary(
            f"Person close/reopen bisect failed ({args.scenario})",
            output,
        )
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
