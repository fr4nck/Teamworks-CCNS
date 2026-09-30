#!/usr/bin/env python3
"""Exécute les close/reopen après OnInit, dans le vrai MainLoop wx."""

from __future__ import annotations

from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_person_mainloop_lifecycle_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_person_mainloop_lifecycle_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-mainloop-lifecycle-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_MAINLOOP_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_MAINLOOP_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            import wx as _smoke_wx
            import GestionDB as _smoke_gestiondb
            from Dlg import DLG_Fiche_individuelle as _smoke_person
            from Dlg import DLG_Config_sauvegarde as _smoke_backup

            _smoke_state = {
                "cycle": 0,
                "cycles": 20,
                "person_id": None,
                "dialog": None,
                "failed": False,
            }

            def _smoke_fail():
                if _smoke_state["failed"]:
                    return
                _smoke_state["failed"] = True
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_MAINLOOP_FAILED", flush=True)
                _smoke_wx.CallAfter(self.ExitMainLoop)

            def _smoke_finish_backup(_event=None):
                try:
                    if _event is not None:
                        _event.Skip()
                    print("TEAMWORKS_SMOKE_PERSON_MAINLOOP_READY", flush=True)
                    _smoke_wx.CallAfter(self.ExitMainLoop)
                except Exception:
                    _smoke_fail()

            def _smoke_open_backup():
                try:
                    print("TEAMWORKS_SMOKE_PERSON_MAINLOOP_BACKUP", flush=True)
                    _probe = _smoke_backup.MyFrame(frame)
                    _probe.Bind(
                        _smoke_wx.EVT_WINDOW_DESTROY,
                        lambda _event: _smoke_finish_backup(_event)
                        if _event.GetEventObject() is _probe
                        else _event.Skip(),
                    )
                    _probe.Show()
                    _probe.Layout()
                    _probe.Destroy()
                except Exception:
                    _smoke_fail()

            def _smoke_on_person_destroy(_event, _dialog):
                try:
                    if _event.GetEventObject() is not _dialog:
                        _event.Skip()
                        return
                    _event.Skip()
                    _smoke_state["cycle"] += 1
                    print(
                        "TEAMWORKS_SMOKE_PERSON_MAINLOOP_DESTROYED:%d/%d"
                        % (_smoke_state["cycle"], _smoke_state["cycles"]),
                        flush=True,
                    )
                    _smoke_state["dialog"] = None
                    if _smoke_state["cycle"] >= _smoke_state["cycles"]:
                        _smoke_wx.CallAfter(_smoke_open_backup)
                    else:
                        _smoke_wx.CallAfter(_smoke_open_person)
                except Exception:
                    _smoke_fail()

            def _smoke_close_person(_dialog):
                try:
                    if _dialog.Fermer(save=True) is not True:
                        raise RuntimeError("Fermer(save=True) a échoué")
                    print(
                        "TEAMWORKS_SMOKE_PERSON_MAINLOOP_CLOSE_REQUESTED:%d/%d"
                        % (_smoke_state["cycle"] + 1, _smoke_state["cycles"]),
                        flush=True,
                    )
                except Exception:
                    _smoke_fail()

            def _smoke_open_person():
                try:
                    _dialog = _smoke_person.Dialog(
                        frame,
                        IDpersonne=_smoke_state["person_id"],
                    )
                    _smoke_state["dialog"] = _dialog
                    _dialog.Bind(
                        _smoke_wx.EVT_WINDOW_DESTROY,
                        lambda _event, _dlg=_dialog: _smoke_on_person_destroy(
                            _event, _dlg
                        ),
                    )
                    _dialog.Show()
                    _dialog.Layout()
                    print(
                        "TEAMWORKS_SMOKE_PERSON_MAINLOOP_OPEN:%d/%d"
                        % (_smoke_state["cycle"] + 1, _smoke_state["cycles"]),
                        flush=True,
                    )
                    # Une itération de la vraie boucle sépare l'affichage de la
                    # fermeture, comme pour une interaction utilisateur.
                    _smoke_wx.CallAfter(_smoke_close_person, _dialog)
                except Exception:
                    _smoke_fail()

            def _smoke_start():
                try:
                    _db = _smoke_gestiondb.DB()
                    _db.ExecuterReq(
                        "SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1"
                    )
                    _rows = _db.ResultatReq()
                    _db.Close()
                    if not _rows:
                        raise RuntimeError("aucune personne disponible")
                    _smoke_state["person_id"] = _rows[0][0]
                    print("TEAMWORKS_SMOKE_PERSON_MAINLOOP_STARTED", flush=True)
                    _smoke_open_person()
                except Exception:
                    _smoke_fail()

            # La différence essentielle avec l'ancien smoke : OnInit se termine
            # d'abord. Les fenêtres sont ensuite créées/détruites par le vrai
            # MainLoop, qui traite la PendingDeleteList de wxWidgets.
            _smoke_wx.CallAfter(_smoke_start)
            return True
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"ligne marqueur introuvable: count={marker_count}")
    patched_core = core_source.replace(MARKER_LINE, INJECTION, 1)
    compile(patched_core, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core, encoding="utf-8")

    entrypoint = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_person_mainloop_lifecycle_smoke as CORE"
    if import_line not in entrypoint:
        raise RuntimeError("import du cœur Teamworks introuvable")
    patched_entrypoint = entrypoint.replace(import_line, patched_import, 1)
    compile(patched_entrypoint, str(PATCHED), "exec")
    PATCHED.write_text(patched_entrypoint, encoding="utf-8")
    return marker_count


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    marker_count = None
    try:
        marker_count = build_patched_entrypoint()
        return_code, output = run_entrypoint(
            PATCHED,
            root=ROOT,
            teamworks_dir=TEAMWORKS_DIR,
            timeout=1200,
        )
        write_diagnostic(
            REPORT,
            return_code=return_code,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        if return_code != 0 or FAILURE_MARKER in output or READY_MARKER not in output:
            github_error_summary("Person mainloop lifecycle smoke failed", output)
            return return_code or 1
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
        github_error_summary("Person mainloop lifecycle smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
