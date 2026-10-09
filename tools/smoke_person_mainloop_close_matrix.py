#!/usr/bin/env python3
"""Isole les effets de Fermer() dans le vrai MainLoop wx, un processus par cas."""

from __future__ import annotations

import argparse
from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_person_mainloop_close_matrix_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_person_mainloop_close_matrix_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-mainloop-close-matrix"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_FAILED"
SCENARIOS = (
    "bare-unbound",
    "backup-unbound",
    "bare-dialog-destroy",
    "core-destroy",
    "core-no-notebook-destroy",
    "core-no-notebook-no-ticker-destroy",
    "core-no-notebook-no-photo-destroy",
    "core-no-notebook-no-ticker-photo-destroy",
    "core-no-notebook-native-buttons-destroy",
    "wrapper-core-notebook-destroy",
    "destroy",
    "save-destroy",
    "callbacks-destroy",
    "refresh-destroy",
    "save-callbacks-destroy",
    "callbacks-save-destroy",
    "fermer-nosave",
    "fermer-save",
)


def build_injection(scenario: str) -> str:
    return f'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            import wx as _smoke_wx
            import GestionDB as _smoke_gestiondb
            from Dlg import DLG_Fiche_individuelle as _smoke_person
            from Dlg import DLG_Fiche_individuelle_core as _smoke_person_core
            from Dlg import DLG_Config_sauvegarde as _smoke_backup

            _smoke_scenario = {scenario!r}
            _smoke_state = {{"failed": False, "dialog": None, "guard": None}}

            class _SmokeTicker(_smoke_wx.Control):
                def __init__(self, parent, *args, **kwargs):
                    _smoke_wx.Control.__init__(self, parent)
                    self._text = ""
                def SetText(self, text):
                    self._text = text
                def Start(self):
                    return None
                def Stop(self):
                    return None

            class _SmokePhoto(_smoke_wx.Panel):
                def __init__(self, parent, *args, **kwargs):
                    _smoke_wx.Panel.__init__(self, parent)
                def SetPhoto(self, *args, **kwargs):
                    return None

            class _SmokePage(_smoke_wx.Panel):
                def __init__(self, parent, *args, **kwargs):
                    _smoke_wx.Panel.__init__(self, parent)

            class _SmokeNotebook(_smoke_wx.Notebook):
                def __init__(self, parent, *args, **kwargs):
                    _smoke_wx.Notebook.__init__(self, parent)
                def AfficheAutresPages(self, etat=True):
                    return None

            class _SmokeButton(_smoke_wx.Button):
                def __init__(
                    self, parent, id=-1, texte="", cheminImage=None, *args, **kwargs
                ):
                    _smoke_wx.Button.__init__(self, parent, id=id, label=texte)

            def _cancel_guard():
                _guard = _smoke_state.get("guard")
                if _guard is not None:
                    try:
                        if _guard.IsRunning():
                            _guard.Stop()
                    except Exception:
                        pass
                    _smoke_state["guard"] = None

            def _fail():
                _cancel_guard()
                if _smoke_state["failed"]:
                    return
                _smoke_state["failed"] = True
                import traceback as _traceback
                _traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_FAILED", flush=True)
                _smoke_wx.CallAfter(self.ExitMainLoop)

            def _destroyed(_event, _dialog):
                try:
                    if _event.GetEventObject() is not _dialog:
                        _event.Skip()
                        return
                    _event.Skip()
                    _cancel_guard()
                    print(
                        "TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_DESTROYED:%s"
                        % _smoke_scenario,
                        flush=True,
                    )
                    print("TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_READY", flush=True)
                    _smoke_wx.CallAfter(self.ExitMainLoop)
                except Exception:
                    _fail()

            def _finish_unbound():
                print("TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_READY", flush=True)
                self.ExitMainLoop()

            def _operate(_dialog):
                try:
                    print(
                        "TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_OPERATE:%s"
                        % _smoke_scenario,
                        flush=True,
                    )
                    if _smoke_scenario in ("bare-unbound", "backup-unbound"):
                        _dialog.Destroy()
                        print(
                            "TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_REQUESTED:%s"
                            % _smoke_scenario,
                            flush=True,
                        )
                        _smoke_wx.CallLater(500, _finish_unbound)
                        return
                    if _smoke_scenario in (
                        "destroy",
                        "bare-dialog-destroy",
                        "core-destroy",
                        "core-no-notebook-destroy",
                        "core-no-notebook-no-ticker-destroy",
                        "core-no-notebook-no-photo-destroy",
                        "core-no-notebook-no-ticker-photo-destroy",
                        "core-no-notebook-native-buttons-destroy",
                        "wrapper-core-notebook-destroy",
                    ):
                        _dialog.Destroy()
                    elif _smoke_scenario == "save-destroy":
                        _dialog._sauvegarder_pages()
                        _dialog.Destroy()
                    elif _smoke_scenario == "callbacks-destroy":
                        if not _dialog._arreter_callbacks_avant_fermeture():
                            raise RuntimeError("arrêt callbacks refusé")
                        _dialog.Destroy()
                    elif _smoke_scenario == "refresh-destroy":
                        _dialog._rafraichir_frame_personnes(save=True)
                        _dialog.Destroy()
                    elif _smoke_scenario == "save-callbacks-destroy":
                        _dialog._sauvegarder_pages()
                        if not _dialog._arreter_callbacks_avant_fermeture():
                            raise RuntimeError("arrêt callbacks refusé")
                        _dialog.Destroy()
                    elif _smoke_scenario == "callbacks-save-destroy":
                        if not _dialog._arreter_callbacks_avant_fermeture():
                            raise RuntimeError("arrêt callbacks refusé")
                        _dialog._sauvegarder_pages()
                        _dialog.Destroy()
                    elif _smoke_scenario == "fermer-nosave":
                        if _dialog.Fermer(save=False) is not True:
                            raise RuntimeError("Fermer(save=False) a échoué")
                    elif _smoke_scenario == "fermer-save":
                        if _dialog.Fermer(save=True) is not True:
                            raise RuntimeError("Fermer(save=True) a échoué")
                    else:
                        raise RuntimeError("scénario inconnu")
                    print(
                        "TEAMWORKS_SMOKE_PERSON_CLOSE_MATRIX_REQUESTED:%s"
                        % _smoke_scenario,
                        flush=True,
                    )
                except Exception:
                    _fail()

            def _start():
                try:
                    _db = _smoke_gestiondb.DB()
                    _db.ExecuterReq(
                        "SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1"
                    )
                    _rows = _db.ResultatReq()
                    _db.Close()
                    if not _rows:
                        raise RuntimeError("aucune personne disponible")
                    if _smoke_scenario == "bare-unbound":
                        _dialog = _smoke_wx.Dialog(frame)
                    elif _smoke_scenario == "backup-unbound":
                        _dialog = _smoke_backup.MyFrame(frame)
                    elif _smoke_scenario == "bare-dialog-destroy":
                        _dialog = _smoke_wx.Dialog(
                            frame,
                            style=(
                                _smoke_wx.DEFAULT_DIALOG_STYLE
                                | _smoke_wx.RESIZE_BORDER
                                | _smoke_wx.MAXIMIZE_BOX
                                | _smoke_wx.MINIMIZE_BOX
                            ),
                        )
                    elif _smoke_scenario.startswith("core-") and _smoke_scenario.endswith("-destroy"):
                        if "no-notebook" in _smoke_scenario:
                            _smoke_person_core.Notebook = _SmokeNotebook
                        if "no-ticker" in _smoke_scenario:
                            _smoke_person_core.Ticker = _SmokeTicker
                        if "no-photo" in _smoke_scenario:
                            _smoke_person_core.CTRL_Photo.CTRL_Photo = _SmokePhoto
                        if "native-buttons" in _smoke_scenario:
                            _smoke_person_core.CTRL_Bouton_image.CTRL = _SmokeButton
                        _dialog = _smoke_person_core.Dialog(
                            frame, IDpersonne=_rows[0][0]
                        )
                    elif _smoke_scenario == "wrapper-core-notebook-destroy":
                        _original_notebook = _smoke_person.Notebook
                        try:
                            _smoke_person.Notebook = _smoke_person_core.Notebook
                            _dialog = _smoke_person.Dialog(
                                frame, IDpersonne=_rows[0][0]
                            )
                        finally:
                            _smoke_person.Notebook = _original_notebook
                    else:
                        _dialog = _smoke_person.Dialog(
                            frame, IDpersonne=_rows[0][0]
                        )
                    _smoke_state["dialog"] = _dialog
                    if _smoke_scenario not in ("bare-unbound", "backup-unbound"):
                        _dialog.Bind(
                            _smoke_wx.EVT_WINDOW_DESTROY,
                            lambda _event, _dlg=_dialog: _destroyed(_event, _dlg),
                        )
                    _dialog.Show()
                    _dialog.Layout()
                    _smoke_state["guard"] = _smoke_wx.CallLater(
                        15000,
                        _fail,
                    )
                    _smoke_wx.CallAfter(_operate, _dialog)
                except Exception:
                    _fail()

            _smoke_wx.CallAfter(_start)
            return True
'''


def build_patched_entrypoint(scenario: str) -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"ligne marqueur introuvable: count={marker_count}")
    patched_core = core_source.replace(MARKER_LINE, build_injection(scenario), 1)
    compile(patched_core, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core, encoding="utf-8")

    entrypoint = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_person_mainloop_close_matrix_smoke as CORE"
    if import_line not in entrypoint:
        raise RuntimeError("import du cœur Teamworks introuvable")
    patched_entrypoint = entrypoint.replace(import_line, patched_import, 1)
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
            timeout=600,
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
                f"Person close matrix failed ({args.scenario})", output
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
            f"Person close matrix failed ({args.scenario})", output
        )
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
