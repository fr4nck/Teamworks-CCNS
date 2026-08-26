#!/usr/bin/env python3
"""Qualifie le cycle réel des réponses Questionnaire sous Windows."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_questionnaire_lifecycle_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_questionnaire_lifecycle_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "questionnaire-lifecycle-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_QUESTIONNAIRE_LIFECYCLE_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_QUESTIONNAIRE_LIFECYCLE_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_host = None
            _smoke_host_reopen = None
            _smoke_host_edit = None
            _smoke_person_id = None
            _smoke_category_ids = []
            _smoke_question_ids = []
            try:
                import GestionDB as _smoke_gestiondb
                from Ctrl import CTRL_Page_questionnaire as _smoke_questionnaire_page

                _smoke_person_name = "__TEAMWORKS_SMOKE_QUESTIONNAIRE_PERSON__"
                _smoke_text_create = "__TEAMWORKS_SMOKE_QUESTIONNAIRE_CREATE__"
                _smoke_text_edit = "__TEAMWORKS_SMOKE_QUESTIONNAIRE_EDIT__"
                _smoke_category_labels = (
                    "__TEAMWORKS_SMOKE_QUESTIONNAIRE_CAT_A__",
                    "__TEAMWORKS_SMOKE_QUESTIONNAIRE_CAT_B__",
                )

                def _smoke_cleanup():
                    _db = _smoke_gestiondb.DB()
                    try:
                        if _smoke_person_id is not None:
                            _db.ReqDEL("questionnaire_reponses", "IDindividu", _smoke_person_id)
                        for _question_id in _smoke_question_ids:
                            _db.ReqDEL("questionnaire_choix", "IDquestion", _question_id)
                            _db.ReqDEL("questionnaire_questions", "IDquestion", _question_id)
                        for _category_id in _smoke_category_ids:
                            _db.ReqDEL("questionnaire_categories", "IDcategorie", _category_id)
                        if _smoke_person_id is not None:
                            _db.ReqDEL("personnes", "IDpersonne", _smoke_person_id)
                        _db.Commit()
                    finally:
                        _db.Close()

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:fixtures", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                try:
                    _smoke_person_id = _smoke_db.ReqInsert(
                        "personnes",
                        [
                            ("civilite", "Mr"),
                            ("nom", _smoke_person_name),
                            ("prenom", "Recette"),
                        ],
                    )
                    if _smoke_person_id in (None, 0):
                        raise RuntimeError("création de la personne Questionnaire impossible")

                    for _index, _label in enumerate(_smoke_category_labels):
                        _category_id = _smoke_db.ReqInsert(
                            "questionnaire_categories",
                            [
                                ("ordre", 9000 + _index),
                                ("visible", 1),
                                ("type", "individu"),
                                ("couleur", "(230, 230, 230)"),
                                ("label", _label),
                            ],
                        )
                        _smoke_category_ids.append(_category_id)

                    _smoke_text_question_id = _smoke_db.ReqInsert(
                        "questionnaire_questions",
                        [
                            ("IDcategorie", _smoke_category_ids[0]),
                            ("ordre", 0),
                            ("visible", 1),
                            ("label", "Réponse texte smoke"),
                            ("controle", "ligne_texte"),
                            ("defaut", None),
                            ("options", None),
                        ],
                    )
                    _smoke_checkbox_question_id = _smoke_db.ReqInsert(
                        "questionnaire_questions",
                        [
                            ("IDcategorie", _smoke_category_ids[1]),
                            ("ordre", 0),
                            ("visible", 1),
                            ("label", "Case à cocher smoke"),
                            ("controle", "case_coche"),
                            ("defaut", "0"),
                            ("options", None),
                        ],
                    )
                    _smoke_question_ids.extend(
                        [_smoke_text_question_id, _smoke_checkbox_question_id]
                    )
                    _smoke_db.Commit()
                finally:
                    _smoke_db.Close()

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:create-page", flush=True)
                _smoke_host = wx.Frame(frame, title="Smoke Questionnaire création")
                _smoke_page = _smoke_questionnaire_page.Panel(
                    _smoke_host, IDpersonne=_smoke_person_id
                )
                _smoke_sizer = wx.BoxSizer(wx.VERTICAL)
                _smoke_sizer.Add(_smoke_page, 1, wx.EXPAND)
                _smoke_host.SetSizer(_smoke_sizer)
                _smoke_host.SetSize((900, 650))
                _smoke_host.Show()
                wx.Yield()

                _smoke_ctrl = _smoke_page.ctrl_questionnaire
                _smoke_initial = _smoke_ctrl.GetValeurs()
                assert _smoke_text_question_id in _smoke_initial
                assert _smoke_checkbox_question_id in _smoke_initial

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:set-values", flush=True)
                _smoke_ctrl.SetValeurs(
                    {
                        _smoke_text_question_id: _smoke_text_create,
                        _smoke_checkbox_question_id: "1",
                    }
                )
                _smoke_values = _smoke_ctrl.GetValeurs()
                assert _smoke_values[_smoke_text_question_id] == _smoke_text_create
                assert _smoke_values[_smoke_checkbox_question_id] == "1"

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:create-save", flush=True)
                _smoke_page.Sauvegarde()

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:create-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDreponse, IDquestion, reponse FROM questionnaire_reponses "
                    "WHERE IDindividu=%d ORDER BY IDquestion" % _smoke_person_id
                )
                _smoke_created_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_created_rows) == 2
                _smoke_created_by_question = {
                    row[1]: (row[0], row[2]) for row in _smoke_created_rows
                }
                assert _smoke_created_by_question[_smoke_text_question_id][1] == _smoke_text_create
                assert _smoke_created_by_question[_smoke_checkbox_question_id][1] == "1"
                _smoke_response_ids = {
                    question_id: data[0]
                    for question_id, data in _smoke_created_by_question.items()
                }

                _smoke_host.Destroy()
                _smoke_host = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:reopen-readback", flush=True)
                _smoke_host_reopen = wx.Frame(frame, title="Smoke Questionnaire relecture")
                _smoke_reopen_page = _smoke_questionnaire_page.Panel(
                    _smoke_host_reopen, IDpersonne=_smoke_person_id
                )
                _smoke_reopen_sizer = wx.BoxSizer(wx.VERTICAL)
                _smoke_reopen_sizer.Add(_smoke_reopen_page, 1, wx.EXPAND)
                _smoke_host_reopen.SetSizer(_smoke_reopen_sizer)
                _smoke_host_reopen.SetSize((900, 650))
                _smoke_host_reopen.Show()
                wx.Yield()
                _smoke_reopened_values = _smoke_reopen_page.ctrl_questionnaire.GetValeurs()
                assert _smoke_reopened_values[_smoke_text_question_id] == _smoke_text_create
                assert _smoke_reopened_values[_smoke_checkbox_question_id] == "1"

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:edit-save", flush=True)
                _smoke_reopen_page.ctrl_questionnaire.SetValeurs(
                    {
                        _smoke_text_question_id: _smoke_text_edit,
                        _smoke_checkbox_question_id: "0",
                    }
                )
                _smoke_reopen_page.Sauvegarde()

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:edit-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDreponse, IDquestion, reponse FROM questionnaire_reponses "
                    "WHERE IDindividu=%d ORDER BY IDquestion" % _smoke_person_id
                )
                _smoke_modified_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_modified_rows) == 2
                _smoke_modified_by_question = {
                    row[1]: (row[0], row[2]) for row in _smoke_modified_rows
                }
                assert _smoke_modified_by_question[_smoke_text_question_id][0] == _smoke_response_ids[_smoke_text_question_id]
                assert _smoke_modified_by_question[_smoke_checkbox_question_id][0] == _smoke_response_ids[_smoke_checkbox_question_id]
                assert _smoke_modified_by_question[_smoke_text_question_id][1] == _smoke_text_edit
                assert _smoke_modified_by_question[_smoke_checkbox_question_id][1] == "0"

                _smoke_host_reopen.Destroy()
                _smoke_host_reopen = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:final-reopen", flush=True)
                _smoke_host_edit = wx.Frame(frame, title="Smoke Questionnaire modification")
                _smoke_edit_page = _smoke_questionnaire_page.Panel(
                    _smoke_host_edit, IDpersonne=_smoke_person_id
                )
                _smoke_edit_sizer = wx.BoxSizer(wx.VERTICAL)
                _smoke_edit_sizer.Add(_smoke_edit_page, 1, wx.EXPAND)
                _smoke_host_edit.SetSizer(_smoke_edit_sizer)
                _smoke_host_edit.SetSize((900, 650))
                _smoke_host_edit.Show()
                wx.Yield()
                _smoke_final_values = _smoke_edit_page.ctrl_questionnaire.GetValeurs()
                assert _smoke_final_values[_smoke_text_question_id] == _smoke_text_edit
                assert _smoke_final_values[_smoke_checkbox_question_id] == "0"

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:cleanup", flush=True)
                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT COUNT(*) FROM questionnaire_reponses WHERE IDindividu=%d"
                    % _smoke_person_id
                )
                assert _smoke_db.ResultatReq()[0][0] == 0
                _smoke_db.ExecuterReq(
                    "SELECT COUNT(*) FROM personnes WHERE IDpersonne=%d" % _smoke_person_id
                )
                assert _smoke_db.ResultatReq()[0][0] == 0
                _smoke_db.Close()

                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_LIFECYCLE_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                try:
                    _smoke_cleanup()
                except Exception:
                    _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_QUESTIONNAIRE_LIFECYCLE_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                for _smoke_window_name in (
                    "_smoke_host",
                    "_smoke_host_reopen",
                    "_smoke_host_edit",
                ):
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
    patched_import = "import Teamworks_core_questionnaire_lifecycle_smoke as CORE"
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
            PATCHED, root=ROOT, teamworks_dir=TEAMWORKS_DIR, timeout=240
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
            github_error_summary("Questionnaire lifecycle smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Questionnaire lifecycle smoke failed", output)
            print("marqueur de cycle Questionnaire absent", file=sys.stderr)
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
        github_error_summary("Questionnaire lifecycle smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
