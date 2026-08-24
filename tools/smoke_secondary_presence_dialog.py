#!/usr/bin/env python3
"""Exécute le smoke principal avec construction réelle du formulaire de présence."""

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
            try:
                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:imports", flush=True)
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Saisie_presence as _smoke_presence

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke présence")

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:panel", flush=True)
                _smoke_dialog = wx.Dialog(frame, title="Smoke présence")
                _smoke_panel = _smoke_presence.Panel(
                    _smoke_dialog,
                    listeDonnees=[(_smoke_rows[0][0], _smoke_datetime.date.today())],
                    mode="planning",
                )
                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:fields", flush=True)
                _smoke_panel.text_heure_debut.SetValue("09:00")
                _smoke_panel.text_heure_fin.SetValue("10:00")
                _smoke_panel.text_intitule.SetValue("Recette automatisée")
                _smoke_dialog.SetSizer(wx.BoxSizer(wx.VERTICAL))
                _smoke_dialog.GetSizer().Add(_smoke_panel, 1, wx.EXPAND)
                _smoke_dialog.GetSizer().Fit(_smoke_dialog)
                _smoke_dialog.Layout()
                _smoke_dialog.Show()
                wx.Yield()

                print("TEAMWORKS_SMOKE_PRESENCE_STAGE:assertions", flush=True)
                assert _smoke_panel.text_heure_debut.GetValue() == "09:00"
                assert _smoke_panel.text_heure_fin.GetValue() == "10:00"
                assert _smoke_panel.text_intitule.GetValue() == "Recette automatisée"
                assert _smoke_panel.listCtrl_donnees.GetItemCount() >= 1
                assert _smoke_panel.treeCtrl_categories.GetCount() >= 1
                assert _smoke_panel.bouton_ok.IsEnabled()
                assert _smoke_panel.bouton_annuler.IsEnabled()
                print("TEAMWORKS_SMOKE_PRESENCE_DIALOG_READY", flush=True)
                _smoke_dialog.Destroy()
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PRESENCE_DIALOG_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
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
            timeout=120,
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
            github_error_summary(ERROR_TITLE, output, max_lines=32)
            return return_code or 1
        if SECONDARY_MARKER not in output:
            github_error_summary(ERROR_TITLE, output, max_lines=32)
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
        github_error_summary(ERROR_TITLE, output, max_lines=32)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())