#!/usr/bin/env python3
"""Compare l'ordre des opérations de fermeture de la fiche sous Windows."""

from __future__ import annotations

import argparse
from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_person_close_order_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_person_close_order_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-close-order-smoke"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_CLOSE_ORDER_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_CLOSE_ORDER_FAILED"
SCENARIOS = (
    "save-only-1",
    "save-only-2",
    "save-only-3",
    "fermer-20",
    "current-manual-20",
    "callbacks-first-20",
)


def _parts(scenario: str) -> tuple[str, int]:
    mode, count = scenario.rsplit("-", 1)
    return mode, int(count)


def build_injection(scenario: str) -> str:
    mode, cycles = _parts(scenario)
    return f'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                import wx as _smoke_wx
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Fiche_individuelle as _smoke_person
                from Dlg import DLG_Config_sauvegarde as _smoke_backup

                _smoke_mode = {mode!r}
                _smoke_cycles = {cycles}
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne FROM personnes "
                    "WHERE civilite IS NOT NULL AND civilite <> '' "
                    "AND nom IS NOT NULL AND nom <> '' "
                    "AND prenom IS NOT NULL AND prenom <> '' "
                    "ORDER BY IDpersonne LIMIT 1"
                )
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible")
                _smoke_person_id = _smoke_rows[0][0]

                def _destroy(_window):
                    if _window and not _window.IsBeingDeleted():
                        _window.Destroy()
                    _smoke_wx.Yield()

                for _index in range(_smoke_cycles):
                    print(
                        "TEAMWORKS_SMOKE_PERSON_CLOSE_ORDER_CYCLE:%s:%d/%d"
                        % (_smoke_mode, _index + 1, _smoke_cycles),
                        flush=True,
                    )
                    _dlg = _smoke_person.Dialog(frame, IDpersonne=_smoke_person_id)
                    if _smoke_mode == "fermer":
                        # Le mode non modal doit rester refuse.
                        assert not _dlg.IsModal()
                        assert _dlg.Fermer(save=True) is False

                        _errors = []
                        _memo = "TW30 cycle %d" % (_index + 1)

                        def _save_modal():
                            try:
                                assert _dlg.IsModal()

                                page = _dlg.notebook.pageGeneralites

                                assert page.combo_box_civilite.GetStringSelection()
                                assert page.text_nom.GetValue()
                                assert page.text_prenom.GetValue()

                                page.text_memo.SetValue(_memo)

                                assert _dlg.Fermer(save=True) is True

                            except Exception as exc:
                                _errors.append(exc)

                                if _dlg.IsModal():
                                    _dlg.EndModal(_smoke_wx.ID_CANCEL)

                        try:
                            _smoke_wx.CallAfter(_save_modal)
                            result = _dlg.ShowModal()

                            if _errors:
                                raise _errors[0]

                            assert result == _smoke_wx.ID_OK
                        finally:
                            _destroy(_dlg)

                        _db = _smoke_gestiondb.DB()
                        try:
                            _db.ExecuterReq(
                                "SELECT memo FROM personnes WHERE IDpersonne=%d"
                                % _smoke_person_id
                            )
                            assert _db.ResultatReq()[0][0] == _memo
                        finally:
                            _db.Close()

                        print(
                            "MODAL_SAVE_READBACK:%d/%d"
                            % (_index + 1, _smoke_cycles),
                            flush=True,
                        )
                    elif _smoke_mode == "save-only":
                        _dlg.Show()
                        _dlg.Layout()
                        _smoke_wx.Yield()
                        _dlg._sauvegarder_pages()
                        _destroy(_dlg)
                    elif _smoke_mode == "current-manual":
                        _dlg.Show()
                        _dlg.Layout()
                        _smoke_wx.Yield()
                        _dlg._sauvegarder_pages()
                        if not _dlg._arreter_callbacks_avant_fermeture():
                            raise RuntimeError("arrêt callbacks refusé")
                        _dlg._rafraichir_frame_personnes(save=True)
                        _destroy(_dlg)
                    elif _smoke_mode == "callbacks-first":
                        _dlg.Show()
                        _dlg.Layout()
                        _smoke_wx.Yield()
                        if not _dlg._arreter_callbacks_avant_fermeture():
                            raise RuntimeError("arrêt callbacks refusé")
                        _dlg._sauvegarder_pages()
                        _dlg._rafraichir_frame_personnes(save=True)
                        _destroy(_dlg)
                    else:
                        raise RuntimeError("mode inconnu: %s" % _smoke_mode)

                print(
                    "TEAMWORKS_SMOKE_PERSON_CLOSE_ORDER_BACKUP:%s" % _smoke_mode,
                    flush=True,
                )
                _probe = _smoke_backup.MyFrame(frame)
                _probe.Show()
                _probe.Layout()
                _smoke_wx.Yield()
                _destroy(_probe)
                print("TEAMWORKS_SMOKE_PERSON_CLOSE_ORDER_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_CLOSE_ORDER_FAILED", flush=True)
            _smoke_wx.CallAfter(frame.Close)
            return True
'''


def build_patched_entrypoint(scenario: str) -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(
            f"ligne marqueur du smoke principal introuvable: count={marker_count}"
        )
    patched_core = core_source.replace(MARKER_LINE, build_injection(scenario), 1)
    compile(patched_core, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core, encoding="utf-8")

    entrypoint = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_person_close_order_smoke as CORE"
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
            timeout=900,
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
                f"Person close order smoke failed ({args.scenario})",
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
            f"Person close order smoke failed ({args.scenario})",
            output,
        )
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
