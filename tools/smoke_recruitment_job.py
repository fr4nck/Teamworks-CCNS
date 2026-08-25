#!/usr/bin/env python3
"""Qualifie création, modification et persistance d'une offre d'emploi Recrutement."""

from __future__ import annotations

from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_recruitment_job_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_recruitment_job_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "recruitment-job-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_JOB_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_JOB_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_create_dialog = None
            _smoke_edit_dialog = None
            _smoke_emploi_id = None
            try:
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Saisie_emploi as _smoke_job

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDfonction FROM fonctions ORDER BY IDfonction LIMIT 2")
                _smoke_function_ids = [row[0] for row in _smoke_db.ResultatReq()]
                _smoke_db.ExecuterReq("SELECT IDaffectation FROM affectations ORDER BY IDaffectation LIMIT 2")
                _smoke_affectation_ids = [row[0] for row in _smoke_db.ResultatReq()]
                _smoke_db.ExecuterReq("SELECT IDdiffuseur FROM diffuseurs ORDER BY IDdiffuseur LIMIT 2")
                _smoke_diffuseur_ids = [row[0] for row in _smoke_db.ResultatReq()]
                _smoke_db.Close()

                _smoke_start = _smoke_datetime.date(2099, 9, 1)
                _smoke_end = _smoke_datetime.date(2099, 9, 30)
                _smoke_dispo_start = _smoke_datetime.date(2099, 10, 1)
                _smoke_dispo_end = _smoke_datetime.date(2099, 10, 31)
                _smoke_edit_start = _smoke_datetime.date(2099, 9, 2)
                _smoke_edit_end = _smoke_datetime.date(2099, 10, 5)
                _smoke_edit_dispo_start = _smoke_datetime.date(2099, 10, 3)
                _smoke_edit_dispo_end = _smoke_datetime.date(2099, 11, 7)
                _smoke_create_title = "__TEAMWORKS_SMOKE_EMPLOI_CREATE__"
                _smoke_edit_title = "__TEAMWORKS_SMOKE_EMPLOI_EDIT__"

                def _smoke_cleanup():
                    if _smoke_emploi_id is None:
                        return
                    _db = _smoke_gestiondb.DB()
                    for _table in (
                        "emplois_dispo",
                        "emplois_fonctions",
                        "emplois_affectations",
                        "emplois_diffuseurs",
                    ):
                        _db.ReqDEL(_table, "IDemploi", _smoke_emploi_id)
                    _db.ReqDEL("emplois", "IDemploi", _smoke_emploi_id)
                    _db.Commit()
                    _db.Close()

                def _smoke_read_children():
                    _db = _smoke_gestiondb.DB()
                    _db.ExecuterReq(
                        "SELECT IDdisponibilite, date_debut, date_fin FROM emplois_dispo "
                        "WHERE IDemploi=%d ORDER BY IDdisponibilite" % _smoke_emploi_id
                    )
                    _dispo = _db.ResultatReq()
                    _db.ExecuterReq(
                        "SELECT IDfonction FROM emplois_fonctions WHERE IDemploi=%d ORDER BY IDfonction"
                        % _smoke_emploi_id
                    )
                    _fonctions = [row[0] for row in _db.ResultatReq()]
                    _db.ExecuterReq(
                        "SELECT IDaffectation FROM emplois_affectations WHERE IDemploi=%d ORDER BY IDaffectation"
                        % _smoke_emploi_id
                    )
                    _affectations = [row[0] for row in _db.ResultatReq()]
                    _db.ExecuterReq(
                        "SELECT IDdiffuseur FROM emplois_diffuseurs WHERE IDemploi=%d ORDER BY IDdiffuseur"
                        % _smoke_emploi_id
                    )
                    _diffuseurs = [row[0] for row in _db.ResultatReq()]
                    _db.Close()
                    return _dispo, _fonctions, _affectations, _diffuseurs

                def _smoke_edit_selection(ids):
                    if len(ids) > 1:
                        return [ids[1]]
                    return []

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:create-dialog", flush=True)
                _smoke_create_dialog = _smoke_job.Dialog(frame, IDemploi=None)
                _smoke_create_dialog.Show()
                wx.Yield()
                _smoke_panel = _smoke_create_dialog.panel
                _smoke_panel.SetDatePicker(_smoke_panel.ctrl_date_debut, _smoke_start)
                _smoke_panel.SetDatePicker(_smoke_panel.ctrl_date_fin, _smoke_end)
                _smoke_panel.ctrl_intitule.SetValue(_smoke_create_title)
                _smoke_panel.ctrl_detail.SetValue("Offre de recrutement recette automatisée")
                _smoke_panel.ctrl_reference.SetValue("SMOKE-2099-A")
                _smoke_panel.ctrl_periodes_remarques.SetValue("Période initiale")
                _smoke_panel.ctrl_poste_remarques.SetValue("Poste initial")
                _smoke_panel.listeDisponibilites = [(None, _smoke_dispo_start, _smoke_dispo_end)]
                _smoke_panel.ctrl_periodes.Remplissage(_smoke_panel.listeDisponibilites)
                if _smoke_function_ids:
                    _smoke_panel.ctrl_fonction.CocheListe([_smoke_function_ids[0]])
                if _smoke_affectation_ids:
                    _smoke_panel.ctrl_affectations.CocheListe([_smoke_affectation_ids[0]])
                if _smoke_diffuseur_ids:
                    _smoke_panel.ctrl_diffuseurs.CocheListe([_smoke_diffuseur_ids[0]])

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:create-save", flush=True)
                _smoke_panel.Sauvegarde()
                _smoke_emploi_id = _smoke_panel.IDemploi
                assert _smoke_emploi_id is not None

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:create-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT date_debut, date_fin, intitule, detail, reference_anpe, periodes_remarques, poste_remarques "
                    "FROM emplois WHERE IDemploi=%d" % _smoke_emploi_id
                )
                _smoke_created_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_created_rows) == 1
                _smoke_created = _smoke_created_rows[0]
                assert str(_smoke_created[0]) == str(_smoke_start)
                assert str(_smoke_created[1]) == str(_smoke_end)
                assert _smoke_created[2] == _smoke_create_title
                assert _smoke_created[3] == "Offre de recrutement recette automatisée"
                assert _smoke_created[4] == "SMOKE-2099-A"
                assert _smoke_created[5] == "Période initiale"
                assert _smoke_created[6] == "Poste initial"
                _smoke_dispo, _smoke_functions, _smoke_affectations, _smoke_diffuseurs = _smoke_read_children()
                assert len(_smoke_dispo) == 1
                assert str(_smoke_dispo[0][1]) == str(_smoke_dispo_start)
                assert str(_smoke_dispo[0][2]) == str(_smoke_dispo_end)
                if _smoke_function_ids:
                    assert _smoke_functions == [_smoke_function_ids[0]]
                if _smoke_affectation_ids:
                    assert _smoke_affectations == [_smoke_affectation_ids[0]]
                if _smoke_diffuseur_ids:
                    assert _smoke_diffuseurs == [_smoke_diffuseur_ids[0]]
                _smoke_dispo_id = _smoke_dispo[0][0]

                _smoke_create_dialog.Destroy()
                _smoke_create_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:edit-dialog", flush=True)
                _smoke_edit_dialog = _smoke_job.Dialog(frame, IDemploi=_smoke_emploi_id)
                _smoke_edit_dialog.Show()
                wx.Yield()
                _smoke_edit_panel = _smoke_edit_dialog.panel
                assert _smoke_edit_panel.ctrl_intitule.GetValue() == _smoke_create_title
                assert _smoke_edit_panel.ctrl_reference.GetValue() == "SMOKE-2099-A"
                assert len(_smoke_edit_panel.listeDisponibilites) == 1
                assert _smoke_edit_panel.listeDisponibilites[0][0] == _smoke_dispo_id

                _smoke_edit_panel.SetDatePicker(_smoke_edit_panel.ctrl_date_debut, _smoke_edit_start)
                _smoke_edit_panel.SetDatePicker(_smoke_edit_panel.ctrl_date_fin, _smoke_edit_end)
                _smoke_edit_panel.ctrl_intitule.SetValue(_smoke_edit_title)
                _smoke_edit_panel.ctrl_detail.SetValue("Offre modifiée par la recette")
                _smoke_edit_panel.ctrl_reference.SetValue("SMOKE-2099-B")
                _smoke_edit_panel.ctrl_periodes_remarques.SetValue("Période modifiée")
                _smoke_edit_panel.ctrl_poste_remarques.SetValue("Poste modifié")
                _smoke_edit_panel.listeDisponibilites = [
                    (_smoke_dispo_id, _smoke_edit_dispo_start, _smoke_edit_dispo_end)
                ]
                _smoke_edit_panel.ctrl_periodes.Remplissage(_smoke_edit_panel.listeDisponibilites)
                _smoke_edit_panel.ctrl_fonction.CocheListe(_smoke_edit_selection(_smoke_function_ids))
                _smoke_edit_panel.ctrl_affectations.CocheListe(_smoke_edit_selection(_smoke_affectation_ids))
                _smoke_edit_panel.ctrl_diffuseurs.CocheListe(_smoke_edit_selection(_smoke_diffuseur_ids))

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:edit-save", flush=True)
                _smoke_edit_panel.Sauvegarde()

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:edit-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT date_debut, date_fin, intitule, detail, reference_anpe, periodes_remarques, poste_remarques "
                    "FROM emplois WHERE IDemploi=%d" % _smoke_emploi_id
                )
                _smoke_modified_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_modified_rows) == 1
                _smoke_modified = _smoke_modified_rows[0]
                assert str(_smoke_modified[0]) == str(_smoke_edit_start)
                assert str(_smoke_modified[1]) == str(_smoke_edit_end)
                assert _smoke_modified[2] == _smoke_edit_title
                assert _smoke_modified[3] == "Offre modifiée par la recette"
                assert _smoke_modified[4] == "SMOKE-2099-B"
                assert _smoke_modified[5] == "Période modifiée"
                assert _smoke_modified[6] == "Poste modifié"
                _smoke_dispo2, _smoke_functions2, _smoke_affectations2, _smoke_diffuseurs2 = _smoke_read_children()
                assert len(_smoke_dispo2) == 1
                assert _smoke_dispo2[0][0] == _smoke_dispo_id
                assert str(_smoke_dispo2[0][1]) == str(_smoke_edit_dispo_start)
                assert str(_smoke_dispo2[0][2]) == str(_smoke_edit_dispo_end)
                assert _smoke_functions2 == _smoke_edit_selection(_smoke_function_ids)
                assert _smoke_affectations2 == _smoke_edit_selection(_smoke_affectation_ids)
                assert _smoke_diffuseurs2 == _smoke_edit_selection(_smoke_diffuseur_ids)

                _smoke_edit_dialog.Destroy()
                _smoke_edit_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:list-readback", flush=True)
                _smoke_recruitment_page = frame.toolBook.GetPage(
                    frame.toolBook.dict_pages_by_index["recrutement"]
                )
                _smoke_recruitment_page.MAJpanel()
                _smoke_recruitment_page.ChangerMode("emplois")
                _smoke_recruitment_page.listCtrl_emplois.MAJ()
                wx.Yield()
                assert any(
                    getattr(track, "IDemploi", None) == _smoke_emploi_id
                    for track in _smoke_recruitment_page.listCtrl_emplois.donnees
                )
                _smoke_track = next(
                    track
                    for track in _smoke_recruitment_page.listCtrl_emplois.donnees
                    if getattr(track, "IDemploi", None) == _smoke_emploi_id
                )
                assert _smoke_track.intitule == _smoke_edit_title

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_STAGE:cleanup", flush=True)
                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM emplois WHERE IDemploi=%d" % _smoke_emploi_id)
                _smoke_remaining = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _smoke_remaining == 0
                _smoke_emploi_id = None

                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_RECRUITMENT_JOB_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                for _dialog in (_smoke_create_dialog, _smoke_edit_dialog):
                    try:
                        if _dialog is not None:
                            _dialog.Destroy()
                    except Exception:
                        pass
                try:
                    if _smoke_emploi_id is not None:
                        _db = _smoke_gestiondb.DB()
                        for _table in (
                            "emplois_dispo",
                            "emplois_fonctions",
                            "emplois_affectations",
                            "emplois_diffuseurs",
                        ):
                            _db.ReqDEL(_table, "IDemploi", _smoke_emploi_id)
                        _db.ReqDEL("emplois", "IDemploi", _smoke_emploi_id)
                        _db.Commit()
                        _db.Close()
                except Exception:
                    pass
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur du smoke principal introuvable: {marker_count}")

    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs Offre d'emploi absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_secondary_recruitment_job_smoke as CORE"
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
        if return_code != 0 or FAILURE_MARKER in output or READY_MARKER not in output:
            github_error_summary("Recruitment job smoke failed", output, max_lines=64)
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
        github_error_summary("Recruitment job smoke failed", output, max_lines=64)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())