#!/usr/bin/env python3
"""Qualifie création, modification et persistance d'un entretien Recrutement sous Windows."""

from __future__ import annotations

from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_recruitment_interview_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_recruitment_interview_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "recruitment-interview-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_create_dialog = None
            _smoke_edit_dialog = None
            _smoke_host = None
            _smoke_entretien_id = None
            _smoke_person_id = None
            try:
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Ctrl import CTRL_Page_candidatures as _smoke_recruitment
                from Dlg import DLG_Saisie_entretien as _smoke_interview

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke entretien")
                _smoke_person_id = _smoke_rows[0][0]
                _smoke_create_date = _smoke_datetime.date(2099, 10, 1)
                _smoke_edit_date = _smoke_datetime.date(2099, 10, 2)
                _smoke_create_marker = "__TEAMWORKS_SMOKE_ENTRETIEN_CREATE__"
                _smoke_edit_marker = "__TEAMWORKS_SMOKE_ENTRETIEN_EDIT__"

                def _smoke_cleanup():
                    if _smoke_entretien_id is None:
                        return
                    _db = _smoke_gestiondb.DB()
                    _db.ReqDEL("entretiens", "IDentretien", _smoke_entretien_id)
                    _db.Commit()
                    _db.Close()

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:create-dialog", flush=True)
                _smoke_create_dialog = _smoke_interview.Dialog(
                    frame,
                    IDentretien=None,
                    IDcandidat=None,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_create_dialog.Show()
                wx.Yield()
                _smoke_create_dialog.SetDatePicker(_smoke_create_dialog.ctrl_date, _smoke_create_date)
                _smoke_create_dialog.ctrl_heure.SetValue("09:30")
                _smoke_create_dialog.ctrl_avis.SetSelection(3)
                _smoke_create_dialog.ctrl_remarques.SetValue(_smoke_create_marker)

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:create-save", flush=True)
                _smoke_entretien_id = _smoke_create_dialog.Sauvegarde()
                assert _smoke_entretien_id is not None

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:create-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne, date, heure, avis, remarques FROM entretiens WHERE IDentretien=%d"
                    % _smoke_entretien_id
                )
                _smoke_created_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_created_rows) == 1
                _smoke_created = _smoke_created_rows[0]
                assert _smoke_created[0] == _smoke_person_id
                assert str(_smoke_created[1]) == str(_smoke_create_date)
                assert str(_smoke_created[2])[:5] == "09:30"
                assert _smoke_created[3] == 3
                assert _smoke_created[4] == _smoke_create_marker

                _smoke_create_dialog.Destroy()
                _smoke_create_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:edit-dialog", flush=True)
                _smoke_edit_dialog = _smoke_interview.Dialog(
                    frame,
                    IDentretien=_smoke_entretien_id,
                    IDcandidat=None,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_edit_dialog.Show()
                wx.Yield()
                assert _smoke_edit_dialog.ctrl_heure.GetValue() == "09:30"
                assert _smoke_edit_dialog.ctrl_avis.GetSelection() == 3
                assert _smoke_edit_dialog.ctrl_remarques.GetValue() == _smoke_create_marker
                _smoke_edit_dialog.SetDatePicker(_smoke_edit_dialog.ctrl_date, _smoke_edit_date)
                _smoke_edit_dialog.ctrl_heure.SetValue("14:15")
                _smoke_edit_dialog.ctrl_avis.SetSelection(4)
                _smoke_edit_dialog.ctrl_remarques.SetValue(_smoke_edit_marker)

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:edit-save", flush=True)
                assert _smoke_edit_dialog.Sauvegarde() == _smoke_entretien_id

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:edit-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne, date, heure, avis, remarques FROM entretiens WHERE IDentretien=%d"
                    % _smoke_entretien_id
                )
                _smoke_modified_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_modified_rows) == 1
                _smoke_modified = _smoke_modified_rows[0]
                assert _smoke_modified[0] == _smoke_person_id
                assert str(_smoke_modified[1]) == str(_smoke_edit_date)
                assert str(_smoke_modified[2])[:5] == "14:15"
                assert _smoke_modified[3] == 4
                assert _smoke_modified[4] == _smoke_edit_marker

                _smoke_edit_dialog.Destroy()
                _smoke_edit_dialog = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:list-readback", flush=True)
                _smoke_host = wx.Frame(frame, title="Smoke entretien recrutement")
                _smoke_panel = _smoke_recruitment.Panel(_smoke_host, IDpersonne=_smoke_person_id)
                _smoke_panel.Show()
                _smoke_host.Show()
                wx.Yield()
                _smoke_panel.ctrl_entretiens.MAJ()
                wx.Yield()
                assert any(
                    getattr(track, "IDentretien", None) == _smoke_entretien_id
                    for track in _smoke_panel.ctrl_entretiens.donnees
                )

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_STAGE:cleanup", flush=True)
                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM entretiens WHERE IDentretien=%d" % _smoke_entretien_id)
                _smoke_remaining = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _smoke_remaining == 0
                _smoke_entretien_id = None

                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_READY", flush=True)
                _smoke_host.Destroy()
                _smoke_host = None
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_FAILED", flush=True)
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
                    if _smoke_entretien_id is not None:
                        _db = _smoke_gestiondb.DB()
                        _db.ReqDEL("entretiens", "IDentretien", _smoke_entretien_id)
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
        raise RuntimeError("injection des marqueurs Entretien absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_secondary_recruitment_interview_smoke as CORE"
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
            github_error_summary("Recruitment interview smoke failed", output, max_lines=48)
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
        github_error_summary("Recruitment interview smoke failed", output, max_lines=48)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())