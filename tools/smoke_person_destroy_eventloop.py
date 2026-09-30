#!/usr/bin/env python3
"""Valide la fermeture non modale dans une vraie boucle wx imbriquée."""

from __future__ import annotations

from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_person_destroy_eventloop_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_person_destroy_eventloop_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-destroy-eventloop-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_DESTROY_EVENTLOOP_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_DESTROY_EVENTLOOP_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                import wx as _smoke_wx
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Fiche_individuelle as _smoke_person
                from Dlg import DLG_Config_sauvegarde as _smoke_backup

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1"
                )
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible")
                _smoke_person_id = _smoke_rows[0][0]

                def _smoke_close_and_wait(_dialog, _cycle):
                    _state = {"destroyed": False, "timed_out": False}
                    _loop = _smoke_wx.GUIEventLoop()

                    def _on_destroy(_event):
                        if _event.GetEventObject() is _dialog:
                            _state["destroyed"] = True
                            if _loop.IsRunning():
                                _loop.Exit()
                        _event.Skip()

                    def _on_timeout():
                        if not _state["destroyed"]:
                            _state["timed_out"] = True
                            if _loop.IsRunning():
                                _loop.Exit()

                    _dialog.Bind(_smoke_wx.EVT_WINDOW_DESTROY, _on_destroy)
                    if _dialog.Fermer(save=True) is not True:
                        raise RuntimeError("Fermer(save=True) a échoué")
                    print(
                        "TEAMWORKS_SMOKE_PERSON_EVENTLOOP_AFTER_FERMER:%d:being_deleted=%s:destroyed=%s"
                        % (_cycle, _dialog.IsBeingDeleted(), _state["destroyed"]),
                        flush=True,
                    )
                    if not _state["destroyed"]:
                        _guard = _smoke_wx.CallLater(5000, _on_timeout)
                        _activator = _smoke_wx.EventLoopActivator(_loop)
                        try:
                            _loop.Run()
                        finally:
                            if _guard.IsRunning():
                                _guard.Stop()
                            del _activator
                    if _state["timed_out"] or not _state["destroyed"]:
                        raise RuntimeError("destruction native non confirmée")
                    print(
                        "TEAMWORKS_SMOKE_PERSON_EVENTLOOP_DESTROYED:%d" % _cycle,
                        flush=True,
                    )

                for _cycle in range(1, 21):
                    _dialog = _smoke_person.Dialog(frame, IDpersonne=_smoke_person_id)
                    _dialog.Show()
                    _dialog.Layout()
                    _smoke_wx.Yield()
                    _smoke_close_and_wait(_dialog, _cycle)

                _probe = _smoke_backup.MyFrame(frame)
                _probe.Show()
                _probe.Layout()
                _smoke_wx.Yield()
                _probe.Destroy()
                _smoke_wx.Yield()
                print("TEAMWORKS_SMOKE_PERSON_DESTROY_EVENTLOOP_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_DESTROY_EVENTLOOP_FAILED", flush=True)
            _smoke_wx.CallAfter(self.ExitMainLoop)
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
    patched_import = "import Teamworks_core_person_destroy_eventloop_smoke as CORE"
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
            github_error_summary("Person destroy eventloop smoke failed", output)
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
        github_error_summary("Person destroy eventloop smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
