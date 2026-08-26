#!/usr/bin/env python3
"""Qualifie les modèles/récurrences du planning Teamworks dans l'application Windows réelle."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_planning_models_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_planning_models_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "planning-models-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PLANNING_MODELS_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PLANNING_MODELS_FAILED"
ERROR_TITLE = "Planning models smoke failed"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_application_dialog = None
            _smoke_model_id = None
            _smoke_overlap_model_id = None
            _smoke_person_id = None
            _smoke_category_id = None
            _smoke_original_confirm_dialog = None
            _smoke_original_message_dialog = None
            try:
                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:imports", flush=True)
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Application_modele as _smoke_application
                from Dlg import DLG_Confirm_appli_modele as _smoke_confirmation

                _smoke_dates = [
                    _smoke_datetime.date(2099, 12, 21),
                    _smoke_datetime.date(2099, 12, 28),
                ]
                assert all(date.isoweekday() == 1 for date in _smoke_dates)
                _smoke_label = "__TEAMWORKS_SMOKE_WEEKLY_MODEL__"
                _smoke_overlap_label = "__TEAMWORKS_SMOKE_WEEKLY_OVERLAP__"
                _smoke_model_name = "__TEAMWORKS_SMOKE_MODELE_HEBDO__"
                _smoke_overlap_name = "__TEAMWORKS_SMOKE_MODELE_CHEVAUCHEMENT__"

                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:fixtures", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_people = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq("SELECT IDcategorie FROM cat_presences ORDER BY IDcategorie LIMIT 1")
                _smoke_categories = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_people:
                    raise RuntimeError("aucune personne disponible pour le smoke modèles planning")
                if not _smoke_categories:
                    raise RuntimeError("aucune catégorie disponible pour le smoke modèles planning")
                _smoke_person_id = _smoke_people[0][0]
                _smoke_category_id = _smoke_categories[0][0]

                def _smoke_cleanup():
                    _db = _smoke_gestiondb.DB()
                    _db.ExecuterReq(
                        "DELETE FROM presences WHERE IDpersonne=%d AND date IN ('%s','%s') "
                        "AND intitule IN ('%s','%s')"
                        % (
                            _smoke_person_id,
                            str(_smoke_dates[0]),
                            str(_smoke_dates[1]),
                            _smoke_label,
                            _smoke_overlap_label,
                        )
                    )
                    _db.ExecuterReq(
                        "DELETE FROM modeles_taches WHERE IDmodele IN "
                        "(SELECT IDmodele FROM modeles_planning WHERE nom IN ('%s','%s'))"
                        % (_smoke_model_name, _smoke_overlap_name)
                    )
                    _db.ExecuterReq(
                        "DELETE FROM modeles_planning WHERE nom IN ('%s','%s')"
                        % (_smoke_model_name, _smoke_overlap_name)
                    )
                    _db.Commit()
                    _db.Close()

                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_model_id = _smoke_db.ReqInsert(
                    "modeles_planning",
                    [
                        ("nom", _smoke_model_name),
                        ("type", "hebdo"),
                        ("description", "Smoke récurrence hebdomadaire"),
                        ("periodes", "100"),
                        ("inclureferies", 0),
                    ],
                )
                _smoke_db.ReqInsert(
                    "modeles_taches",
                    [
                        ("IDmodele", _smoke_model_id),
                        ("type", "hebdo"),
                        ("periode", 1),
                        ("jour", 1),
                        ("heure_debut", "13:30"),
                        ("heure_fin", "15:00"),
                        ("IDcategorie", _smoke_category_id),
                        ("intitule", _smoke_label),
                    ],
                )
                _smoke_overlap_model_id = _smoke_db.ReqInsert(
                    "modeles_planning",
                    [
                        ("nom", _smoke_overlap_name),
                        ("type", "hebdo"),
                        ("description", "Smoke modèle incompatible"),
                        ("periodes", "100"),
                        ("inclureferies", 0),
                    ],
                )
                _smoke_db.ReqInsert(
                    "modeles_taches",
                    [
                        ("IDmodele", _smoke_overlap_model_id),
                        ("type", "hebdo"),
                        ("periode", 1),
                        ("jour", 1),
                        ("heure_debut", "14:00"),
                        ("heure_fin", "16:00"),
                        ("IDcategorie", _smoke_category_id),
                        ("intitule", _smoke_overlap_label),
                    ],
                )
                _smoke_db.Close()
                assert _smoke_model_id and _smoke_overlap_model_id

                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:dialog", flush=True)
                _smoke_selection_lines = [
                    (_smoke_person_id, _smoke_dates[0]),
                    (_smoke_person_id, _smoke_dates[1]),
                ]
                _smoke_application_dialog = _smoke_application.Dialog(
                    frame,
                    selectionLignes=_smoke_selection_lines,
                    selectionPersonnes=[_smoke_person_id],
                    selectionDates=(_smoke_dates[0], _smoke_dates[1]),
                )
                _smoke_application_dialog.Show()
                wx.Yield()
                _smoke_panel = _smoke_application_dialog.panel
                assert _smoke_panel.radio_btn_1.GetValue() is True

                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:generate", flush=True)
                _smoke_capture = {}
                _smoke_original_confirm_dialog = _smoke_confirmation.Dialog

                class _SmokeCaptureConfirmation:
                    def __init__(self, parent, nbreTaches=0, dictTaches=None, listeCreationsTaches=None, inclureFeries=False):
                        _smoke_capture["parent"] = parent
                        _smoke_capture["count"] = nbreTaches
                        _smoke_capture["dict"] = dictTaches
                        _smoke_capture["tasks"] = list(listeCreationsTaches or [])
                        _smoke_capture["include_holidays"] = inclureFeries
                        self.etat = None

                    def ShowModal(self):
                        return wx.ID_CANCEL

                    def Destroy(self):
                        return None

                _smoke_confirmation.Dialog = _SmokeCaptureConfirmation
                _smoke_panel.list_ctrl_modeles.selections = [_smoke_model_id]
                _smoke_panel.OnBoutonOk(None)
                assert _smoke_capture.get("count") == 2
                _smoke_generated_tasks = _smoke_capture.get("tasks", [])
                assert len(_smoke_generated_tasks) == 2
                assert [task[1] for task in _smoke_generated_tasks] == _smoke_dates
                for _task in _smoke_generated_tasks:
                    assert _task[0] == _smoke_person_id
                    assert _task[2] == "13:30"
                    assert _task[3] == "15:00"
                    assert _task[4] == _smoke_category_id
                    assert _task[5] == _smoke_label
                assert _smoke_capture.get("include_holidays") is False

                _smoke_confirmation.Dialog = _smoke_original_confirm_dialog
                _smoke_original_confirm_dialog = None

                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:persist", flush=True)
                _smoke_real_confirmation = _smoke_confirmation.Dialog(
                    _smoke_panel,
                    nbreTaches=_smoke_capture["count"],
                    dictTaches=_smoke_capture["dict"],
                    listeCreationsTaches=_smoke_generated_tasks,
                    inclureFeries=False,
                )

                class _SmokeThreadState:
                    def __init__(self):
                        self.stop = False

                    def abort(self):
                        self.stop = True

                _smoke_real_confirmation.thread1 = _SmokeThreadState()
                _smoke_real_confirmation.EnregistrementTaches(_smoke_generated_tasks)
                assert _smoke_real_confirmation.etat == "termine"
                assert _smoke_real_confirmation.listeExceptions == []

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT date, heure_debut, heure_fin, IDcategorie, intitule FROM presences "
                    "WHERE IDpersonne=%d AND date IN ('%s','%s') AND intitule='%s' ORDER BY date"
                    % (
                        _smoke_person_id,
                        str(_smoke_dates[0]),
                        str(_smoke_dates[1]),
                        _smoke_label,
                    )
                )
                _smoke_inserted = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_inserted) == 2
                assert [str(row[0]) for row in _smoke_inserted] == [str(date) for date in _smoke_dates]
                assert all(str(row[1])[:5] == "13:30" for row in _smoke_inserted)
                assert all(str(row[2])[:5] == "15:00" for row in _smoke_inserted)
                assert all(row[3] == _smoke_category_id for row in _smoke_inserted)
                assert all(row[4] == _smoke_label for row in _smoke_inserted)

                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:anti-duplicate", flush=True)
                _smoke_real_confirmation.thread1 = _SmokeThreadState()
                _smoke_real_confirmation.EnregistrementTaches(_smoke_generated_tasks)
                assert len(_smoke_real_confirmation.listeExceptions) == 2
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT COUNT(*) FROM presences WHERE IDpersonne=%d AND date IN ('%s','%s') AND intitule='%s'"
                    % (
                        _smoke_person_id,
                        str(_smoke_dates[0]),
                        str(_smoke_dates[1]),
                        _smoke_label,
                    )
                )
                _smoke_count_after_second_apply = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _smoke_count_after_second_apply == 2
                _smoke_real_confirmation.Destroy()

                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:overlap", flush=True)
                _smoke_messages = []
                _smoke_confirm_calls = []
                _smoke_original_message_dialog = wx.MessageDialog

                class _SmokeMessageDialog:
                    def __init__(self, parent, message, caption, style=0, *args, **kwargs):
                        _smoke_messages.append(str(message))

                    def ShowModal(self):
                        return wx.ID_OK

                    def Destroy(self):
                        return None

                class _SmokeForbiddenConfirmation:
                    def __init__(self, *args, **kwargs):
                        _smoke_confirm_calls.append(True)
                        self.etat = None

                    def ShowModal(self):
                        return wx.ID_CANCEL

                    def Destroy(self):
                        return None

                wx.MessageDialog = _SmokeMessageDialog
                _smoke_confirmation.Dialog = _SmokeForbiddenConfirmation
                _smoke_original_confirm_dialog = _smoke_original_confirm_dialog or _smoke_confirmation.Dialog
                _smoke_panel.list_ctrl_modeles.selections = [_smoke_model_id, _smoke_overlap_model_id]
                _smoke_panel.OnBoutonOk(None)
                assert not _smoke_confirm_calls
                assert any("chevauch" in message.lower() for message in _smoke_messages)

                wx.MessageDialog = _smoke_original_message_dialog
                _smoke_original_message_dialog = None
                _smoke_confirmation.Dialog = _smoke_real_confirmation.__class__
                _smoke_original_confirm_dialog = None

                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:grid-readback", flush=True)
                _smoke_presence_page = frame.toolBook.GetPage(
                    frame.toolBook.dict_pages_by_index["presences"]
                )
                _smoke_presence_page.MAJpanel()
                _smoke_presence_page.SetSelectionDates(_smoke_dates)
                _smoke_presence_page.SetSelectionPersonnes([_smoke_person_id])
                _smoke_presence_page.MAJpanelPlanning(reinitSelectionPersonnes=False)
                _smoke_grid_records = _smoke_presence_page.panelPlanning.DCplanning.dictPresences
                _smoke_fixture_records = [
                    values for values in _smoke_grid_records.values() if values[6] == _smoke_label
                ]
                assert len(_smoke_fixture_records) == 2

                print("TEAMWORKS_SMOKE_PLANNING_MODELS_STAGE:cleanup", flush=True)
                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT COUNT(*) FROM presences WHERE IDpersonne=%d AND date IN ('%s','%s') "
                    "AND intitule IN ('%s','%s')"
                    % (
                        _smoke_person_id,
                        str(_smoke_dates[0]),
                        str(_smoke_dates[1]),
                        _smoke_label,
                        _smoke_overlap_label,
                    )
                )
                _smoke_presence_remaining = _smoke_db.ResultatReq()[0][0]
                _smoke_db.ExecuterReq(
                    "SELECT COUNT(*) FROM modeles_planning WHERE nom IN ('%s','%s')"
                    % (_smoke_model_name, _smoke_overlap_name)
                )
                _smoke_models_remaining = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _smoke_presence_remaining == 0
                assert _smoke_models_remaining == 0

                _smoke_application_dialog.Destroy()
                _smoke_application_dialog = None
                wx.Yield()
                print("TEAMWORKS_SMOKE_PLANNING_MODELS_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PLANNING_MODELS_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                try:
                    if _smoke_original_confirm_dialog is not None:
                        _smoke_confirmation.Dialog = _smoke_original_confirm_dialog
                except Exception:
                    pass
                try:
                    if _smoke_original_message_dialog is not None:
                        wx.MessageDialog = _smoke_original_message_dialog
                except Exception:
                    pass
                try:
                    if _smoke_application_dialog is not None:
                        _smoke_application_dialog.Destroy()
                except Exception:
                    pass
                try:
                    if _smoke_person_id is not None and _smoke_category_id is not None:
                        _smoke_db = _smoke_gestiondb.DB()
                        _smoke_db.ExecuterReq(
                            "DELETE FROM presences WHERE IDpersonne=%d AND date IN ('2099-12-21','2099-12-28') "
                            "AND intitule IN ('__TEAMWORKS_SMOKE_WEEKLY_MODEL__','__TEAMWORKS_SMOKE_WEEKLY_OVERLAP__')"
                            % _smoke_person_id
                        )
                        _smoke_db.ExecuterReq(
                            "DELETE FROM modeles_taches WHERE IDmodele IN "
                            "(SELECT IDmodele FROM modeles_planning WHERE nom IN "
                            "('__TEAMWORKS_SMOKE_MODELE_HEBDO__','__TEAMWORKS_SMOKE_MODELE_CHEVAUCHEMENT__'))"
                        )
                        _smoke_db.ExecuterReq(
                            "DELETE FROM modeles_planning WHERE nom IN "
                            "('__TEAMWORKS_SMOKE_MODELE_HEBDO__','__TEAMWORKS_SMOKE_MODELE_CHEVAUCHEMENT__')"
                        )
                        _smoke_db.Commit()
                        _smoke_db.Close()
                except Exception:
                    pass
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs modèles planning absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_planning_models_smoke as CORE"
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
            timeout=240,
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
            github_error_summary(ERROR_TITLE, output, max_lines=80)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary(ERROR_TITLE, output, max_lines=80)
            print("marqueur modèles planning absent", file=sys.stderr)
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
        github_error_summary(ERROR_TITLE, output, max_lines=80)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())