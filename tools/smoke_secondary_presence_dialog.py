#!/usr/bin/env python3
"""Exécute un cycle planning réel dans Teamworks : création, modification et relecture."""

from __future__ import annotations

from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_presence_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_presence_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "presence-dialog-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
SECONDARY_MARKER = "TEAMWORKS_SMOKE_PRESENCE_DIALOG_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PRESENCE_DIALOG_FAILED"
ERROR_TITLE = "Presence dialog smoke failed"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_create_dialog = None
            _smoke_edit_dialog = None
            _smoke_presence_id = None
            _smoke_person_id = None
            _smoke_fixture_date = None
            _smoke_label_new = "__TEAMWORKS_SMOKE_PLANNING_CREATE__"
            _smoke_label_edit = "__TEAMWORKS_SMOKE_PLANNING_EDIT__"
            try:
                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:imports", flush=True)
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Saisie_presence as _smoke_presence

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_person_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq("SELECT IDcategorie FROM cat_presences ORDER BY IDcategorie LIMIT 1")
                _smoke_category_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_person_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke planning")
                if not _smoke_category_rows:
                    raise RuntimeError("aucune catégorie de présence disponible pour le smoke planning")
                _smoke_person_id = _smoke_person_rows[0][0]
                _smoke_category_id = _smoke_category_rows[0][0]
                _smoke_fixture_date = _smoke_datetime.date(2099, 12, 30)

                def _smoke_cleanup_fixture():
                    _db = _smoke_gestiondb.DB()
                    _db.ExecuterReq(
                        "DELETE FROM presences WHERE IDpersonne=%d AND date='%s' AND intitule IN ('%s', '%s')"
                        % (
                            _smoke_person_id,
                            str(_smoke_fixture_date),
                            _smoke_label_new,
                            _smoke_label_edit,
                        )
                    )
                    _db.Commit()
                    _db.Close()

                def _smoke_select_category(tree, wanted):
                    def _walk(parent):
                        child, cookie = tree.GetFirstChild(parent)
                        while child.IsOk():
                            if tree.GetItemData(child) == wanted:
                                tree.SelectItem(child)
                                return True
                            if _walk(child):
                                return True
                            child, cookie = tree.GetNextChild(parent, cookie)
                        return False
                    return _walk(tree.GetRootItem())

                _smoke_cleanup_fixture()

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:create-dialog", flush=True)
                _smoke_create_dialog = _smoke_presence.Dialog(
                    frame,
                    listeDonnees=[(_smoke_person_id, _smoke_fixture_date)],
                    mode="planning",
                )
                _smoke_create_dialog.Show()
                wx.Yield()
                _smoke_panel = _smoke_create_dialog.panel
                assert _smoke_select_category(_smoke_panel.treeCtrl_categories, _smoke_category_id)
                _smoke_panel.text_heure_debut.SetValue("09:00")
                _smoke_panel.text_heure_fin.SetValue("10:00")
                _smoke_panel.text_intitule.SetValue(_smoke_label_new)

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:create-validation", flush=True)
                assert _smoke_panel.ValidationDonnees() is True
                assert _smoke_panel.SauvegardeNouveau() == "Ok"

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:create-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpresence, IDpersonne, date, heure_debut, heure_fin, IDcategorie, intitule "
                    "FROM presences WHERE IDpersonne=%d AND date='%s' AND intitule='%s' "
                    "ORDER BY IDpresence DESC LIMIT 1"
                    % (_smoke_person_id, str(_smoke_fixture_date), _smoke_label_new)
                )
                _smoke_created_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_created_rows) == 1
                _smoke_created = _smoke_created_rows[0]
                _smoke_presence_id = _smoke_created[0]
                assert _smoke_created[1] == _smoke_person_id
                assert str(_smoke_created[2]) == str(_smoke_fixture_date)
                assert str(_smoke_created[3])[:5] == "09:00"
                assert str(_smoke_created[4])[:5] == "10:00"
                assert _smoke_created[5] == _smoke_category_id
                assert _smoke_created[6] == _smoke_label_new

                _smoke_create_dialog.Destroy()
                _smoke_create_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:edit-dialog", flush=True)
                _smoke_edit_dialog = _smoke_presence.Dialog(
                    frame,
                    IDmodif=_smoke_presence_id,
                    mode="planning",
                )
                _smoke_edit_dialog.Show()
                wx.Yield()
                _smoke_edit_panel = _smoke_edit_dialog.panel
                assert _smoke_edit_panel.treeCtrl_categories.GetDataSelection() == _smoke_category_id
                _smoke_edit_panel.text_heure_debut.SetValue("10:15")
                _smoke_edit_panel.text_heure_fin.SetValue("11:45")
                _smoke_edit_panel.text_intitule.SetValue(_smoke_label_edit)

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:edit-validation", flush=True)
                assert _smoke_edit_panel.ValidationDonnees() is True
                assert _smoke_edit_panel.SauvegardeModif() == _smoke_presence_id

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:edit-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne, date, heure_debut, heure_fin, IDcategorie, intitule "
                    "FROM presences WHERE IDpresence=%d" % _smoke_presence_id
                )
                _smoke_modified_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_modified_rows) == 1
                _smoke_modified = _smoke_modified_rows[0]
                assert _smoke_modified[0] == _smoke_person_id
                assert str(_smoke_modified[1]) == str(_smoke_fixture_date)
                assert str(_smoke_modified[2])[:5] == "10:15"
                assert str(_smoke_modified[3])[:5] == "11:45"
                assert _smoke_modified[4] == _smoke_category_id
                assert _smoke_modified[5] == _smoke_label_edit

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:grid-readback", flush=True)
                _smoke_presence_page = frame.toolBook.GetPage(
                    frame.toolBook.dict_pages_by_index["presences"]
                )
                _smoke_presence_page.MAJpanel()
                _smoke_presence_page.SetSelectionDates([_smoke_fixture_date])
                _smoke_presence_page.SetSelectionPersonnes([_smoke_person_id])
                _smoke_presence_page.MAJpanelPlanning(reinitSelectionPersonnes=False)
                assert _smoke_presence_id in _smoke_presence_page.panelPlanning.DCplanning.dictPresences
                _smoke_grid_record = _smoke_presence_page.panelPlanning.DCplanning.dictPresences[_smoke_presence_id]
                assert _smoke_label_edit in [str(value) for value in _smoke_grid_record]

                _smoke_edit_dialog.Destroy()
                _smoke_edit_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:cleanup", flush=True)
                _smoke_cleanup_fixture()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM presences WHERE IDpresence=%d" % _smoke_presence_id)
                _smoke_remaining = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _smoke_remaining == 0

                print("TEAMWORKS_SMOKE_PRESENCE_DIALOG_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PRESENCE_DIALOG_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                try:
                    if _smoke_create_dialog is not None:
                        _smoke_create_dialog.Destroy()
                except Exception:
                    pass
                try:
                    if _smoke_edit_dialog is not None:
                        _smoke_edit_dialog.Destroy()
                except Exception:
                    pass
                try:
                    if _smoke_person_id is not None and _smoke_fixture_date is not None:
                        _smoke_db = _smoke_gestiondb.DB()
                        _smoke_db.ExecuterReq(
                            "DELETE FROM presences WHERE IDpersonne=%d AND date='%s' AND intitule IN ('%s', '%s')"
                            % (
                                _smoke_person_id,
                                str(_smoke_fixture_date),
                                _smoke_label_new,
                                _smoke_label_edit,
                            )
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
        raise RuntimeError(
            f"ligne marqueur du smoke principal introuvable: count={marker_count}"
        )
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if SECONDARY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs du formulaire absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_secondary_presence_smoke as CORE"
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
            ready_marker=SECONDARY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
            ready_label="secondary_marker",
        )
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary(ERROR_TITLE, output, max_lines=48)
            return return_code or 1
        if SECONDARY_MARKER not in output:
            github_error_summary(ERROR_TITLE, output, max_lines=48)
            return 2
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(
            REPORT,
            return_code=3,
            marker_count=marker_count,
            ready_marker=SECONDARY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
            ready_label="secondary_marker",
        )
        github_error_summary(ERROR_TITLE, output, max_lines=48)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())