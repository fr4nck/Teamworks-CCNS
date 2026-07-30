#!/usr/bin/env python3
"""Construit la page Recrutement et exerce ses listes, filtres et tris sous Windows."""

from __future__ import annotations

from pathlib import Path
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
SOURCE = TEAMWORKS_DIR / "Teamworks.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_recruitment_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "recruitment-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                import GestionDB as _smoke_gestiondb
                from Ctrl import CTRL_Page_candidatures as _smoke_recruitment
                from Ol import OL_candidatures as _smoke_candidates

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke recrutement")
                _smoke_person_id = _smoke_rows[0][0]

                _smoke_host = wx.Frame(frame, title="Smoke recrutement")
                _smoke_panel = _smoke_recruitment.Panel(_smoke_host, IDpersonne=_smoke_person_id)
                _smoke_panel.Show()
                _smoke_host.Show()
                wx.Yield()

                assert _smoke_panel.ctrl_candidatures is not None
                assert _smoke_panel.ctrl_entretiens is not None
                assert _smoke_panel.ctrl_candidatures.GetColumnCount() >= 7
                assert _smoke_panel.ctrl_entretiens.GetColumnCount() >= 1
                assert isinstance(_smoke_panel.ctrl_candidatures.donnees, list)
                assert isinstance(_smoke_panel.ctrl_entretiens.donnees, list)

                _smoke_panel.ctrl_candidatures.MAJ()
                _smoke_panel.ctrl_entretiens.MAJ()
                wx.Yield()

                _smoke_candidates.DICT_DISPONIBILITES = {
                    1: [(1, __import__('datetime').date(2026, 1, 1), __import__('datetime').date(2026, 12, 31))],
                    2: [(2, __import__('datetime').date(2026, 1, 1), __import__('datetime').date(2026, 12, 31))],
                }
                _smoke_candidates.DICT_CAND_FONCTIONS = {1: [10], 2: [20]}
                _smoke_candidates.DICT_CAND_AFFECTATIONS = {1: [30], 2: [30]}
                _smoke_filters = [
                    {"nomControle": "candidature_dispo", "valeur": (__import__('datetime').date(2026, 6, 1), __import__('datetime').date(2026, 6, 30)), "sql": ""},
                    {"nomControle": "candidature_fonctions", "valeur": [(10, "Animation")], "sql": ""},
                    {"nomControle": "candidature_affectations", "valeur": [(30, "ALSH")], "sql": ""},
                ]
                _smoke_ids, _smoke_sql = _smoke_panel.ctrl_candidatures.GetListeFiltres(_smoke_filters)
                assert _smoke_ids == [1]
                assert _smoke_sql == ""

                if _smoke_panel.ctrl_candidatures.GetColumnCount() > 1:
                    _smoke_panel.ctrl_candidatures.SortBy(1)
                    wx.Yield()

                assert _smoke_panel.bouton_candidatures_ajouter.IsEnabled()
                assert _smoke_panel.bouton_entretiens_ajouter.IsEnabled()
                print("TEAMWORKS_SMOKE_RECRUITMENT_READY", flush=True)
                _smoke_host.Destroy()
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_RECRUITMENT_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    marker_count = source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur du smoke principal introuvable: {marker_count}")
    patched_source = source.replace(MARKER_LINE, INJECTION, 1)
    compile(patched_source, str(PATCHED), "exec")
    PATCHED.write_text(patched_source, encoding="utf-8")
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
            github_error_summary("Recruitment smoke failed", output)
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
        github_error_summary("Recruitment smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
