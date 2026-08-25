#!/usr/bin/env python3
"""Qualifie le cycle réel création/modification d'une fiche Individu sous Windows."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_person_lifecycle_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_person_lifecycle_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-lifecycle-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_LIFECYCLE_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_LIFECYCLE_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_create_dialog = None
            _smoke_edit_dialog = None
            _smoke_list_host = None
            _smoke_person_id = None
            try:
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Fiche_individuelle as _smoke_person_dialog
                from Ol import OL_personnes as _smoke_person_list

                _smoke_create_name = "__TEAMWORKS_SMOKE_PERSON_CREATE__"
                _smoke_edit_name = "__TEAMWORKS_SMOKE_PERSON_EDIT__"

                def _smoke_cleanup():
                    if _smoke_person_id is None:
                        return
                    _db = _smoke_gestiondb.DB()
                    for _table in (
                        "coordonnees", "diplomes", "questionnaires_reponses",
                        "presences", "frais", "candidatures", "contrats",
                    ):
                        try:
                            _db.ReqDEL(_table, "IDpersonne", _smoke_person_id)
                        except Exception:
                            pass
                    _db.ReqDEL("personnes", "IDpersonne", _smoke_person_id)
                    _db.Commit()
                    _db.Close()

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:reference", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpays FROM pays ORDER BY IDpays LIMIT 1")
                _smoke_country_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_country_rows:
                    raise RuntimeError("aucun pays disponible pour le smoke Individu")
                _smoke_country_id = _smoke_country_rows[0][0]

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:create-dialog", flush=True)
                _smoke_create_dialog = _smoke_person_dialog.Dialog(frame, IDpersonne=0)
                _smoke_create_dialog.Show()
                wx.Yield()
                _smoke_page = _smoke_create_dialog.notebook.pageGeneralites
                _smoke_person_id = _smoke_create_dialog.IDpersonne
                assert _smoke_person_id not in (None, 0)
                _smoke_page.autoComplete = False
                _smoke_page.combo_box_civilite.SetStringSelection("Mme")
                _smoke_page.text_nom.SetValue(_smoke_create_name)
                _smoke_page.text_prenom.SetValue("Recette")
                _smoke_page.text_date_naiss.SetValue("15/04/1990")
                _smoke_page.text_cp_naiss.SetValue("35000")
                _smoke_page.text_ville_naiss.SetValue("RENNES")
                _smoke_page.IDpays_naiss = _smoke_country_id
                _smoke_page.IDpays_nation = _smoke_country_id
                _smoke_page.text_adresse.SetValue("1 rue de la Recette")
                _smoke_page.text_cp.SetValue("35000")
                _smoke_page.text_ville.SetValue("RENNES")
                _smoke_page.text_memo.SetValue("Création UAT Individu")

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:create-save", flush=True)
                _smoke_page.Sauvegarde()

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:create-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT civilite, nom, prenom, date_naiss, cp_naiss, ville_naiss, pays_naiss, nationalite, adresse_resid, cp_resid, ville_resid, memo "
                    "FROM personnes WHERE IDpersonne=%d" % _smoke_person_id
                )
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_rows) == 1
                _smoke_created = _smoke_rows[0]
                assert _smoke_created[0] == "Mme"
                assert _smoke_created[1] == _smoke_create_name
                assert _smoke_created[2] == "Recette"
                assert str(_smoke_created[3]) == "1990-04-15"
                assert str(_smoke_created[4]) == "35000"
                assert _smoke_created[5] == "RENNES"
                assert _smoke_created[6] == _smoke_country_id
                assert _smoke_created[7] == _smoke_country_id
                assert _smoke_created[8] == "1 rue de la Recette"
                assert str(_smoke_created[9]) == "35000"
                assert _smoke_created[10] == "RENNES"
                assert _smoke_created[11] == "Création UAT Individu"

                _smoke_create_dialog.Destroy()
                _smoke_create_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:edit-dialog", flush=True)
                _smoke_edit_dialog = _smoke_person_dialog.Dialog(frame, IDpersonne=_smoke_person_id)
                _smoke_edit_dialog.Show()
                wx.Yield()
                _smoke_edit_page = _smoke_edit_dialog.notebook.pageGeneralites
                _smoke_edit_page.autoComplete = False
                assert _smoke_edit_page.text_nom.GetValue() == _smoke_create_name
                assert _smoke_edit_page.text_prenom.GetValue() == "Recette"
                assert _smoke_edit_page.text_memo.GetValue() == "Création UAT Individu"
                _smoke_edit_page.text_nom.SetValue(_smoke_edit_name)
                _smoke_edit_page.text_prenom.SetValue("Validée")
                _smoke_edit_page.text_adresse.SetValue("2 avenue du Contrôle")
                _smoke_edit_page.text_cp.SetValue("35500")
                _smoke_edit_page.text_ville.SetValue("VITRE")
                _smoke_edit_page.text_memo.SetValue("Modification UAT Individu")

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:edit-save", flush=True)
                _smoke_edit_page.Sauvegarde()

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:edit-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT nom, prenom, adresse_resid, cp_resid, ville_resid, memo FROM personnes WHERE IDpersonne=%d" % _smoke_person_id
                )
                _smoke_modified_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_modified_rows) == 1
                _smoke_modified = _smoke_modified_rows[0]
                assert _smoke_modified[0] == _smoke_edit_name
                assert _smoke_modified[1] == "Validée"
                assert _smoke_modified[2] == "2 avenue du Contrôle"
                assert str(_smoke_modified[3]) == "35500"
                assert _smoke_modified[4] == "VITRE"
                assert _smoke_modified[5] == "Modification UAT Individu"

                _smoke_edit_dialog.Destroy()
                _smoke_edit_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:list-readback", flush=True)
                _smoke_list_host = wx.Frame(frame, title="Smoke Individus")
                _smoke_list_panel = wx.Panel(_smoke_list_host)
                _smoke_list = _smoke_person_list.ListView(
                    _smoke_list_panel,
                    id=-1,
                    name="OL_personnes_smoke",
                    style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
                    activeDoubleClic=False,
                    activeMenuContextuel=False,
                )
                _smoke_list.MAJ(IDpersonne=_smoke_person_id)
                _smoke_tracks = [track for track in _smoke_list.donnees if track.IDpersonne == _smoke_person_id]
                assert len(_smoke_tracks) == 1
                _smoke_track = _smoke_tracks[0]
                assert _smoke_track.nom == _smoke_edit_name
                assert _smoke_track.prenom == "Validée"
                assert _smoke_track.ville_resid == "VITRE"
                assert _smoke_list.GetColumnCount() >= 10

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_STAGE:cleanup", flush=True)
                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM personnes WHERE IDpersonne=%d" % _smoke_person_id)
                _smoke_remaining = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _smoke_remaining == 0

                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                try:
                    _smoke_cleanup()
                except Exception:
                    _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_LIFECYCLE_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                for _smoke_window_name in ("_smoke_create_dialog", "_smoke_edit_dialog", "_smoke_list_host"):
                    _smoke_window = locals().get(_smoke_window_name)
                    if _smoke_window is not None:
                        try:
                            _smoke_window.Destroy()
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
    patched_import = "import Teamworks_core_person_lifecycle_smoke as CORE"
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
        return_code, output = run_entrypoint(PATCHED, root=ROOT, teamworks_dir=TEAMWORKS_DIR, timeout=240)
        write_diagnostic(
            REPORT,
            return_code=return_code,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("Person lifecycle smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Person lifecycle smoke failed", output)
            print("marqueur de cycle Individu absent", file=sys.stderr)
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
        github_error_summary("Person lifecycle smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
