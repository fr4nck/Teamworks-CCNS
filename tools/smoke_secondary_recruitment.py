#!/usr/bin/env python3
"""Exerce le parcours Recrutement réel sous Windows, y compris la persistance."""

from __future__ import annotations

from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_recruitment_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_recruitment_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "recruitment-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_host = None
            _smoke_create_dialog = None
            _smoke_edit_dialog = None
            _smoke_candidature_id = None
            _smoke_person_id = None
            try:
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Ctrl import CTRL_Page_candidatures as _smoke_recruitment
                from Dlg import DLG_Saisie_candidature as _smoke_candidate_dialog
                from Ol import OL_candidatures_core as _smoke_candidates_core

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq("SELECT IDfonction FROM fonctions ORDER BY IDfonction LIMIT 2")
                _smoke_function_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq("SELECT IDaffectation FROM affectations ORDER BY IDaffectation LIMIT 2")
                _smoke_affectation_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke recrutement")
                _smoke_person_id = _smoke_rows[0][0]
                _smoke_function_ids = [row[0] for row in _smoke_function_rows]
                _smoke_affectation_ids = [row[0] for row in _smoke_affectation_rows]
                _smoke_date_start = _smoke_datetime.date(2099, 11, 1)
                _smoke_date_end = _smoke_datetime.date(2099, 11, 15)
                _smoke_date_edit_start = _smoke_datetime.date(2099, 11, 3)
                _smoke_date_edit_end = _smoke_datetime.date(2099, 11, 20)
                _smoke_create_marker = "__TEAMWORKS_SMOKE_RECRUTEMENT_CREATE__"
                _smoke_edit_marker = "__TEAMWORKS_SMOKE_RECRUTEMENT_EDIT__"

                def _smoke_cleanup():
                    if _smoke_candidature_id is None:
                        return
                    _db = _smoke_gestiondb.DB()
                    _db.ReqDEL("disponibilites", "IDcandidature", _smoke_candidature_id)
                    _db.ReqDEL("cand_fonctions", "IDcandidature", _smoke_candidature_id)
                    _db.ReqDEL("cand_affectations", "IDcandidature", _smoke_candidature_id)
                    _db.ReqDEL("candidatures", "IDcandidature", _smoke_candidature_id)
                    _db.Commit()
                    _db.Close()

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:create-dialog", flush=True)
                _smoke_create_dialog = _smoke_candidate_dialog.Dialog(
                    frame,
                    IDcandidat=None,
                    IDpersonne=_smoke_person_id,
                    IDcandidature=None,
                )
                _smoke_create_dialog.Show()
                wx.Yield()
                _smoke_create_panel = _smoke_create_dialog.panel
                _smoke_create_panel.SetDatePicker(_smoke_create_panel.ctrl_date, _smoke_date_start)
                _smoke_create_panel.ctrl_type.SetSelection(4)  # Email
                _smoke_create_panel.ctrl_acte_remarques.SetValue(_smoke_create_marker)
                _smoke_create_panel.ctrl_periodes_remarques.SetValue("Disponibilité recette")
                _smoke_create_panel.ctrl_poste_remarques.SetValue("Poste recette")
                _smoke_create_panel.ctrl_decision.SetSelection(0)
                _smoke_create_panel.ctrl_reponse_remarques.SetValue("Décision à venir")
                _smoke_create_panel.listeDisponibilites = [
                    (None, _smoke_date_start, _smoke_date_end),
                ]
                _smoke_create_panel.ctrl_periodes.Remplissage(_smoke_create_panel.listeDisponibilites)
                if _smoke_function_ids:
                    _smoke_create_panel.ctrl_fonction.CocheListe([_smoke_function_ids[0]])
                if _smoke_affectation_ids:
                    _smoke_create_panel.ctrl_affectations.CocheListe([_smoke_affectation_ids[0]])

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:create-save", flush=True)
                _smoke_create_panel.Sauvegarde()
                _smoke_candidature_id = _smoke_create_panel.IDcandidature
                assert _smoke_candidature_id is not None

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:create-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne, date_depot, IDtype, acte_remarques, periodes_remarques, poste_remarques, IDdecision "
                    "FROM candidatures WHERE IDcandidature=%d" % _smoke_candidature_id
                )
                _smoke_created_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq(
                    "SELECT IDdisponibilite, date_debut, date_fin FROM disponibilites "
                    "WHERE IDcandidature=%d ORDER BY IDdisponibilite" % _smoke_candidature_id
                )
                _smoke_dispo_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq(
                    "SELECT IDfonction FROM cand_fonctions WHERE IDcandidature=%d ORDER BY IDfonction" % _smoke_candidature_id
                )
                _smoke_saved_functions = [row[0] for row in _smoke_db.ResultatReq()]
                _smoke_db.ExecuterReq(
                    "SELECT IDaffectation FROM cand_affectations WHERE IDcandidature=%d ORDER BY IDaffectation" % _smoke_candidature_id
                )
                _smoke_saved_affectations = [row[0] for row in _smoke_db.ResultatReq()]
                _smoke_db.Close()
                assert len(_smoke_created_rows) == 1
                _smoke_created = _smoke_created_rows[0]
                assert _smoke_created[0] == _smoke_person_id
                assert str(_smoke_created[1]) == str(_smoke_date_start)
                assert _smoke_created[2] == 4
                assert _smoke_created[3] == _smoke_create_marker
                assert _smoke_created[4] == "Disponibilité recette"
                assert _smoke_created[5] == "Poste recette"
                assert _smoke_created[6] == 0
                assert len(_smoke_dispo_rows) == 1
                assert str(_smoke_dispo_rows[0][1]) == str(_smoke_date_start)
                assert str(_smoke_dispo_rows[0][2]) == str(_smoke_date_end)
                if _smoke_function_ids:
                    assert _smoke_saved_functions == [_smoke_function_ids[0]]
                if _smoke_affectation_ids:
                    assert _smoke_saved_affectations == [_smoke_affectation_ids[0]]

                _smoke_create_dialog.Destroy()
                _smoke_create_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:edit-dialog", flush=True)
                _smoke_edit_dialog = _smoke_candidate_dialog.Dialog(
                    frame,
                    IDcandidat=None,
                    IDpersonne=_smoke_person_id,
                    IDcandidature=_smoke_candidature_id,
                )
                _smoke_edit_dialog.Show()
                wx.Yield()
                _smoke_edit_panel = _smoke_edit_dialog.panel
                assert _smoke_edit_panel.ctrl_acte_remarques.GetValue() == _smoke_create_marker
                assert len(_smoke_edit_panel.listeDisponibilites) == 1
                _smoke_existing_dispo_id = _smoke_edit_panel.listeDisponibilites[0][0]
                _smoke_edit_panel.ctrl_type.SetSelection(5)  # France Travail
                _smoke_edit_panel.ctrl_acte_remarques.SetValue(_smoke_edit_marker)
                _smoke_edit_panel.ctrl_periodes_remarques.SetValue("Disponibilité modifiée")
                _smoke_edit_panel.ctrl_poste_remarques.SetValue("Poste modifié")
                _smoke_edit_panel.ctrl_decision.SetSelection(1)
                _smoke_edit_panel.ctrl_reponse_remarques.SetValue("Candidature retenue")
                _smoke_edit_panel.listeDisponibilites = [
                    (_smoke_existing_dispo_id, _smoke_date_edit_start, _smoke_date_edit_end),
                ]
                _smoke_edit_panel.ctrl_periodes.Remplissage(_smoke_edit_panel.listeDisponibilites)
                if len(_smoke_function_ids) > 1:
                    _smoke_edit_panel.ctrl_fonction.CocheListe([_smoke_function_ids[1]])
                if len(_smoke_affectation_ids) > 1:
                    _smoke_edit_panel.ctrl_affectations.CocheListe([_smoke_affectation_ids[1]])

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:edit-save", flush=True)
                _smoke_edit_panel.Sauvegarde()

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:edit-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne, IDtype, acte_remarques, periodes_remarques, poste_remarques, IDdecision, decision_remarques "
                    "FROM candidatures WHERE IDcandidature=%d" % _smoke_candidature_id
                )
                _smoke_modified_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq(
                    "SELECT IDdisponibilite, date_debut, date_fin FROM disponibilites "
                    "WHERE IDcandidature=%d ORDER BY IDdisponibilite" % _smoke_candidature_id
                )
                _smoke_modified_dispo = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq(
                    "SELECT IDfonction FROM cand_fonctions WHERE IDcandidature=%d ORDER BY IDfonction" % _smoke_candidature_id
                )
                _smoke_modified_functions = [row[0] for row in _smoke_db.ResultatReq()]
                _smoke_db.ExecuterReq(
                    "SELECT IDaffectation FROM cand_affectations WHERE IDcandidature=%d ORDER BY IDaffectation" % _smoke_candidature_id
                )
                _smoke_modified_affectations = [row[0] for row in _smoke_db.ResultatReq()]
                _smoke_db.Close()
                assert len(_smoke_modified_rows) == 1
                _smoke_modified = _smoke_modified_rows[0]
                assert _smoke_modified[0] == _smoke_person_id
                assert _smoke_modified[1] == 5
                assert _smoke_modified[2] == _smoke_edit_marker
                assert _smoke_modified[3] == "Disponibilité modifiée"
                assert _smoke_modified[4] == "Poste modifié"
                assert _smoke_modified[5] == 1
                assert _smoke_modified[6] == "Candidature retenue"
                assert len(_smoke_modified_dispo) == 1
                assert _smoke_modified_dispo[0][0] == _smoke_existing_dispo_id
                assert str(_smoke_modified_dispo[0][1]) == str(_smoke_date_edit_start)
                assert str(_smoke_modified_dispo[0][2]) == str(_smoke_date_edit_end)
                if len(_smoke_function_ids) > 1:
                    assert _smoke_modified_functions == [_smoke_function_ids[1]]
                if len(_smoke_affectation_ids) > 1:
                    assert _smoke_modified_affectations == [_smoke_affectation_ids[1]]

                _smoke_edit_dialog.Destroy()
                _smoke_edit_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:list-readback", flush=True)
                _smoke_host = wx.Frame(frame, title="Smoke recrutement")
                _smoke_panel = _smoke_recruitment.Panel(_smoke_host, IDpersonne=_smoke_person_id)
                _smoke_panel.Show()
                _smoke_host.Show()
                wx.Yield()
                _smoke_panel.ctrl_candidatures.MAJ()
                _smoke_panel.ctrl_entretiens.MAJ()
                wx.Yield()
                assert any(
                    getattr(track, "IDcandidature", None) == _smoke_candidature_id
                    for track in _smoke_panel.ctrl_candidatures.donnees
                )
                assert _smoke_panel.ctrl_candidatures.GetColumnCount() >= 7
                assert _smoke_panel.ctrl_entretiens.GetColumnCount() >= 1

                # Conserve aussi la couverture historique des filtres combinés.
                _smoke_candidates_core.DICT_DISPONIBILITES.clear()
                _smoke_candidates_core.DICT_DISPONIBILITES.update({
                    1: [(1, _smoke_datetime.date(2026, 1, 1), _smoke_datetime.date(2026, 12, 31))],
                    2: [(2, _smoke_datetime.date(2026, 1, 1), _smoke_datetime.date(2026, 12, 31))],
                })
                _smoke_candidates_core.DICT_CAND_FONCTIONS.clear()
                _smoke_candidates_core.DICT_CAND_FONCTIONS.update({1: [10], 2: [20]})
                _smoke_candidates_core.DICT_CAND_AFFECTATIONS.clear()
                _smoke_candidates_core.DICT_CAND_AFFECTATIONS.update({1: [30], 2: [30]})
                _smoke_filters = [
                    {"nomControle": "candidature_dispo", "valeur": (_smoke_datetime.date(2026, 6, 1), _smoke_datetime.date(2026, 6, 30)), "sql": ""},
                    {"nomControle": "candidature_fonctions", "valeur": [(10, "Animation")], "sql": ""},
                    {"nomControle": "candidature_affectations", "valeur": [(30, "ALSH")], "sql": ""},
                ]
                _smoke_ids, _smoke_sql = _smoke_panel.ctrl_candidatures.GetListeFiltres(_smoke_filters)
                assert _smoke_ids == [1], _smoke_ids
                assert _smoke_sql == ""
                if _smoke_panel.ctrl_candidatures.GetColumnCount() > 1:
                    _smoke_panel.ctrl_candidatures.SortBy(1)
                    wx.Yield()
                assert _smoke_panel.bouton_candidatures_ajouter.IsEnabled()
                assert _smoke_panel.bouton_entretiens_ajouter.IsEnabled()

                print("TEAMWORKS_SMOKE_RECRUITMENT_STAGE:cleanup", flush=True)
                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM candidatures WHERE IDcandidature=%d" % _smoke_candidature_id)
                _smoke_remaining = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _smoke_remaining == 0
                _smoke_candidature_id = None

                print("TEAMWORKS_SMOKE_RECRUITMENT_READY", flush=True)
                _smoke_host.Destroy()
                _smoke_host = None
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_RECRUITMENT_FAILED", flush=True)
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
                    if _smoke_host is not None:
                        _smoke_host.Destroy()
                except Exception:
                    pass
                try:
                    if _smoke_candidature_id is not None:
                        _db = _smoke_gestiondb.DB()
                        _db.ReqDEL("disponibilites", "IDcandidature", _smoke_candidature_id)
                        _db.ReqDEL("cand_fonctions", "IDcandidature", _smoke_candidature_id)
                        _db.ReqDEL("cand_affectations", "IDcandidature", _smoke_candidature_id)
                        _db.ReqDEL("candidatures", "IDcandidature", _smoke_candidature_id)
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
        raise RuntimeError("injection des marqueurs Recrutement absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_secondary_recruitment_smoke as CORE"
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
        if return_code != 0 or FAILURE_MARKER in output or READY_MARKER not in output:
            github_error_summary("Recruitment smoke failed", output, max_lines=64)
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
        github_error_summary("Recruitment smoke failed", output, max_lines=64)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())