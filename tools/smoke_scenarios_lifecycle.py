#!/usr/bin/env python3
"""Qualifie le cycle réel création/modification d'un scénario sous Windows."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_scenarios_lifecycle_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_scenarios_lifecycle_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "scenarios-lifecycle-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_SCENARIOS_LIFECYCLE_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_SCENARIOS_LIFECYCLE_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_person_id = None
            _smoke_scenario_id = None
            _smoke_create_dialog = None
            _smoke_edit_dialog = None
            _smoke_host = None
            try:
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Scenario as _smoke_scenario
                from Dlg import DLG_Scenario_gestion as _smoke_management

                def _smoke_cleanup():
                    _db = _smoke_gestiondb.DB()
                    if _smoke_scenario_id is not None:
                        _db.ReqDEL("scenarios_cat", "IDscenario", _smoke_scenario_id)
                        _db.ReqDEL("scenarios", "IDscenario", _smoke_scenario_id)
                    if _smoke_person_id is not None:
                        _db.ReqDEL("personnes", "IDpersonne", _smoke_person_id)
                    _db.Commit()
                    _db.Close()

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:fixture", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_person_id = _smoke_db.ReqInsert(
                    "personnes",
                    [
                        ("civilite", "Mme"),
                        ("nom", "__TEAMWORKS_SMOKE_SCENARIO__"),
                        ("prenom", "Recette"),
                    ],
                )
                _smoke_db.Commit()
                _smoke_db.Close()
                assert _smoke_person_id not in (None, 0)

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:create-dialog", flush=True)
                _smoke_create_dialog = _smoke_scenario.Dialog(
                    frame,
                    IDscenario=None,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_create_dialog.Show()
                wx.Yield()
                assert _smoke_create_dialog.GetIDpersonne() == _smoke_person_id
                assert _smoke_create_dialog.GetTitle() == "Création d'un scénario"
                _smoke_create_dialog.ctrl_nom.SetValue("__TEAMWORKS_SMOKE_SCENARIO_CREATE__")
                _smoke_create_dialog.ctrl_description.SetValue("Création UAT scénario")
                _smoke_create_dialog.SetDatePicker(
                    _smoke_create_dialog.ctrl_date_debut,
                    _smoke_datetime.date(2026, 9, 1),
                )
                _smoke_create_dialog.SetDatePicker(
                    _smoke_create_dialog.ctrl_date_fin,
                    _smoke_datetime.date(2026, 12, 31),
                )
                _smoke_create_dialog.ctrl_modeHeure.SetSelection(1)
                _smoke_create_dialog.ctrl_detail.SetSelection(2)
                _smoke_create_dialog.ctrl_toutes_categories.SetValue(False)

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:create-save", flush=True)
                _smoke_scenario_id = _smoke_create_dialog.Sauvegarde()
                assert _smoke_scenario_id not in (None, 0)

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:create-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne, nom, description, mode_heure, detail_mois, date_debut, date_fin, toutes_categories "
                    "FROM scenarios WHERE IDscenario=%d" % _smoke_scenario_id
                )
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_rows) == 1
                _smoke_created = _smoke_rows[0]
                assert _smoke_created[0] == _smoke_person_id
                assert _smoke_created[1] == "__TEAMWORKS_SMOKE_SCENARIO_CREATE__"
                assert _smoke_created[2] == "Création UAT scénario"
                assert _smoke_created[3] == 1
                assert _smoke_created[4] == 2
                assert str(_smoke_created[5]) == "2026-09-01"
                assert str(_smoke_created[6]) == "2026-12-31"
                assert int(_smoke_created[7]) == 0

                _smoke_create_dialog.Destroy()
                _smoke_create_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:edit-dialog", flush=True)
                _smoke_edit_dialog = _smoke_scenario.Dialog(
                    frame,
                    IDscenario=_smoke_scenario_id,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_edit_dialog.Show()
                wx.Yield()
                assert _smoke_edit_dialog.GetTitle() == "Modification d'un scénario"
                assert _smoke_edit_dialog.ctrl_nom.GetValue() == "__TEAMWORKS_SMOKE_SCENARIO_CREATE__"
                assert _smoke_edit_dialog.ctrl_description.GetValue() == "Création UAT scénario"
                assert _smoke_edit_dialog.ctrl_modeHeure.GetSelection() == 1
                assert _smoke_edit_dialog.ctrl_detail.GetSelection() == 2
                assert _smoke_edit_dialog.GetDatesPeriode() == (
                    _smoke_datetime.date(2026, 9, 1),
                    _smoke_datetime.date(2026, 12, 31),
                )

                _smoke_edit_dialog.ctrl_nom.SetValue("__TEAMWORKS_SMOKE_SCENARIO_EDIT__")
                _smoke_edit_dialog.ctrl_description.SetValue("Modification UAT scénario")
                _smoke_edit_dialog.SetDatePicker(
                    _smoke_edit_dialog.ctrl_date_fin,
                    _smoke_datetime.date(2027, 6, 30),
                )
                _smoke_edit_dialog.ctrl_modeHeure.SetSelection(0)
                _smoke_edit_dialog.ctrl_detail.SetSelection(3)
                _smoke_edit_dialog.ctrl_toutes_categories.SetValue(True)

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:edit-save", flush=True)
                assert _smoke_edit_dialog.Sauvegarde() == _smoke_scenario_id

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:edit-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT nom, description, mode_heure, detail_mois, date_fin, toutes_categories "
                    "FROM scenarios WHERE IDscenario=%d" % _smoke_scenario_id
                )
                _smoke_modified_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_modified_rows) == 1
                _smoke_modified = _smoke_modified_rows[0]
                assert _smoke_modified[0] == "__TEAMWORKS_SMOKE_SCENARIO_EDIT__"
                assert _smoke_modified[1] == "Modification UAT scénario"
                assert _smoke_modified[2] == 0
                assert _smoke_modified[3] == 3
                assert str(_smoke_modified[4]) == "2027-06-30"
                assert int(_smoke_modified[5]) == 1

                _smoke_edit_dialog.Destroy()
                _smoke_edit_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:management-readback", flush=True)
                _smoke_host = wx.Frame(frame, title="Smoke scénarios")
                _smoke_panel = _smoke_management.Panel(
                    _smoke_host,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_panel.Show()
                _smoke_host.Show()
                wx.Yield()
                _smoke_panel.listCtrl.MAJ(_smoke_scenario_id)
                wx.Yield()
                assert _smoke_person_id in _smoke_panel.listCtrl.dictScenarios
                _smoke_scenarios = _smoke_panel.listCtrl.dictScenarios[_smoke_person_id]
                assert any(
                    item[0] == _smoke_scenario_id
                    and item[1] == "__TEAMWORKS_SMOKE_SCENARIO_EDIT__"
                    and item[2] == "Modification UAT scénario"
                    for item in _smoke_scenarios
                )

                print("TEAMWORKS_SMOKE_SCENARIOS_STAGE:cleanup", flush=True)
                _smoke_host.Destroy()
                _smoke_host = None
                wx.Yield()
                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM scenarios WHERE IDscenario=%d" % _smoke_scenario_id)
                assert _smoke_db.ResultatReq()[0][0] == 0
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM scenarios_cat WHERE IDscenario=%d" % _smoke_scenario_id)
                assert _smoke_db.ResultatReq()[0][0] == 0
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM personnes WHERE IDpersonne=%d" % _smoke_person_id)
                assert _smoke_db.ResultatReq()[0][0] == 0
                _smoke_db.Close()

                print("TEAMWORKS_SMOKE_SCENARIOS_LIFECYCLE_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                try:
                    _smoke_cleanup()
                except Exception:
                    _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_SCENARIOS_LIFECYCLE_FAILED", flush=True)
                return False
            finally:
                for _window in (_smoke_create_dialog, _smoke_edit_dialog, _smoke_host):
                    if _window is not None:
                        try:
                            _window.Destroy()
                        except Exception:
                            pass
                wx.Yield()
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"ligne marqueur du smoke principal introuvable: count={marker_count}")
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_scenarios_lifecycle_smoke as CORE"
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
            timeout=90,
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
            github_error_summary("Scenarios lifecycle smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Scenarios lifecycle smoke failed", output)
            print("marqueur du cycle Scénarios absent", file=sys.stderr)
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
        github_error_summary("Scenarios lifecycle smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
