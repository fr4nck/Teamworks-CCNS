#!/usr/bin/env python3
"""Qualifie les trois impressions PDF du vrai planning Teamworks sous Windows."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_planning_pdf_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_planning_pdf_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "planning-pdf-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PLANNING_PDF_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PLANNING_PDF_FAILED"
ERROR_TITLE = "Planning PDF smoke failed"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_person_id = None
            _smoke_presence_id = None
            _smoke_fixture_date = None
            _smoke_original_selection_dialog = None
            _smoke_temp_pdf = None
            try:
                print("TEAMWORKS_SMOKE_PLANNING_PDF_STAGE:imports", flush=True)
                import datetime as _smoke_datetime
                import shutil as _smoke_shutil
                from pathlib import Path as _SmokePath
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Selection_type_document as _smoke_selection_module

                _smoke_report_dir = _SmokePath(__file__).resolve().parents[1] / "artifacts" / "planning-pdf-smoke"
                _smoke_report_dir.mkdir(parents=True, exist_ok=True)
                for _old_pdf in _smoke_report_dir.glob("planning-*.pdf"):
                    _old_pdf.unlink(missing_ok=True)

                print("TEAMWORKS_SMOKE_PLANNING_PDF_STAGE:fixture", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_people = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq("SELECT IDcategorie FROM cat_presences ORDER BY IDcategorie LIMIT 1")
                _smoke_categories = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_people:
                    raise RuntimeError("aucune personne disponible pour le smoke PDF planning")
                if not _smoke_categories:
                    raise RuntimeError("aucune catégorie disponible pour le smoke PDF planning")

                _smoke_person_id = _smoke_people[0][0]
                _smoke_category_id = _smoke_categories[0][0]
                _smoke_fixture_date = _smoke_datetime.date(2099, 12, 29)
                _smoke_label = "__TEAMWORKS_SMOKE_PLANNING_PDF__"

                def _smoke_cleanup_fixture():
                    _db = _smoke_gestiondb.DB()
                    _db.ExecuterReq(
                        "DELETE FROM presences WHERE IDpersonne=%d AND date='%s' AND intitule='%s'"
                        % (_smoke_person_id, str(_smoke_fixture_date), _smoke_label)
                    )
                    _db.Commit()
                    _db.Close()

                _smoke_cleanup_fixture()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_presence_id = _smoke_db.ReqInsert(
                    "presences",
                    [
                        ("IDpersonne", _smoke_person_id),
                        ("date", str(_smoke_fixture_date)),
                        ("heure_debut", "08:30"),
                        ("heure_fin", "12:00"),
                        ("IDcategorie", _smoke_category_id),
                        ("intitule", _smoke_label),
                    ],
                )
                _smoke_db.Commit()
                _smoke_db.Close()
                assert _smoke_presence_id

                print("TEAMWORKS_SMOKE_PLANNING_PDF_STAGE:grid", flush=True)
                _smoke_presence_page = frame.toolBook.GetPage(
                    frame.toolBook.dict_pages_by_index["presences"]
                )
                _smoke_presence_page.MAJpanel()
                _smoke_presence_page.SetSelectionDates([_smoke_fixture_date])
                _smoke_presence_page.SetSelectionPersonnes([_smoke_person_id])
                _smoke_presence_page.MAJpanelPlanning(reinitSelectionPersonnes=False)
                _smoke_grid = _smoke_presence_page.panelPlanning.DCplanning
                assert _smoke_presence_id in _smoke_grid.dictPresences
                assert len(_smoke_grid.listePresences) == 1

                print("TEAMWORKS_SMOKE_PLANNING_PDF_STAGE:render", flush=True)
                _smoke_original_selection_dialog = _smoke_selection_module.Dialog

                class _SmokeSelectionDialog:
                    choice = 1

                    def __init__(self, *args, **kwargs):
                        pass

                    def ShowModal(self):
                        return wx.ID_OK

                    def GetChoix(self):
                        return self.choice

                    def Destroy(self):
                        return None

                _smoke_selection_module.Dialog = _SmokeSelectionDialog
                _smoke_outputs = []
                for _choice, _name in (
                    (1, "planning-texte.pdf"),
                    (2, "planning-portrait.pdf"),
                    (3, "planning-paysage.pdf"),
                ):
                    print("TEAMWORKS_SMOKE_PLANNING_PDF_STAGE:format:%d" % _choice, flush=True)
                    _SmokeSelectionDialog.choice = _choice
                    _generated = _smoke_grid.Impression(afficher=False)
                    if not _generated:
                        raise RuntimeError("impression planning annulée pour le format %d" % _choice)
                    _smoke_temp_pdf = _SmokePath(_generated)
                    if not _smoke_temp_pdf.is_file():
                        raise RuntimeError("PDF planning absent pour le format %d" % _choice)
                    _payload = _smoke_temp_pdf.read_bytes()
                    assert _payload.startswith(b"%PDF-")
                    assert _payload.rstrip().endswith(b"%%EOF")
                    assert len(_payload) > 1000
                    _target = _smoke_report_dir / _name
                    _smoke_shutil.copyfile(_smoke_temp_pdf, _target)
                    _copied = _target.read_bytes()
                    assert _copied == _payload
                    _smoke_outputs.append((_name, len(_payload)))

                assert [name for name, size in _smoke_outputs] == [
                    "planning-texte.pdf",
                    "planning-portrait.pdf",
                    "planning-paysage.pdf",
                ]
                assert all(size > 1000 for name, size in _smoke_outputs)

                print("TEAMWORKS_SMOKE_PLANNING_PDF_STAGE:cleanup", flush=True)
                _smoke_cleanup_fixture()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM presences WHERE IDpresence=%d" % _smoke_presence_id)
                _smoke_remaining = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _smoke_remaining == 0

                for _name, _size in _smoke_outputs:
                    print("TEAMWORKS_SMOKE_PLANNING_PDF_OUTPUT:%s:%d" % (_name, _size), flush=True)
                print("TEAMWORKS_SMOKE_PLANNING_PDF_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PLANNING_PDF_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                try:
                    if _smoke_original_selection_dialog is not None:
                        _smoke_selection_module.Dialog = _smoke_original_selection_dialog
                except Exception:
                    pass
                try:
                    if _smoke_person_id is not None and _smoke_fixture_date is not None:
                        _smoke_db = _smoke_gestiondb.DB()
                        _smoke_db.ExecuterReq(
                            "DELETE FROM presences WHERE IDpersonne=%d AND date='%s' AND intitule='__TEAMWORKS_SMOKE_PLANNING_PDF__'"
                            % (_smoke_person_id, str(_smoke_fixture_date))
                        )
                        _smoke_db.Commit()
                        _smoke_db.Close()
                except Exception:
                    pass
                try:
                    if _smoke_temp_pdf is not None:
                        _smoke_temp_pdf.unlink(missing_ok=True)
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
        raise RuntimeError("injection des marqueurs PDF planning absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_planning_pdf_smoke as CORE"
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
            github_error_summary(ERROR_TITLE, output, max_lines=64)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary(ERROR_TITLE, output, max_lines=64)
            print("marqueur PDF planning absent", file=sys.stderr)
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
        github_error_summary(ERROR_TITLE, output, max_lines=64)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())