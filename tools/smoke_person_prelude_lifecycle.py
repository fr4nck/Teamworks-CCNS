#!/usr/bin/env python3
"""Isole les blocs précédant le crash SearchCtrl du smoke Fiche personne."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_person_prelude_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_person_prelude_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-prelude-lifecycle-smoke"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_PRELUDE_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_PRELUDE_FAILED"
SCENARIOS = (
    "pages-backup",
    "close-backup",
    "bug-report-backup",
    "prelude-backup",
    "prelude-params10-backup",
    "prelude-params20-backup",
)


def build_injection(scenario: str, cycles: int) -> str:
    return f'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                import os as _smoke_os
                import tempfile as _smoke_tempfile
                import wx as _smoke_wx
                import GestionDB as _smoke_gestiondb
                from Utils import UTILS_Rapport_bugs as _smoke_bug_reports
                from Dlg import DLG_Fiche_individuelle as _smoke_person
                from Dlg import DLG_Preferences as _smoke_preferences
                from Dlg import DLG_Enregistrement as _smoke_registration
                from Dlg import DLG_Config_questionnaires as _smoke_questionnaires
                from Dlg import DLG_Config_types_diplomes as _smoke_diplomas
                from Dlg import DLG_Config_types_pieces as _smoke_pieces
                from Dlg import DLG_Config_situations as _smoke_situations
                from Dlg import DLG_Config_pays as _smoke_countries
                from Dlg import DLG_Config_categories_presences as _smoke_presence_categories
                from Dlg import DLG_Config_classifications as _smoke_classifications
                from Dlg import DLG_Config_champs_contrats as _smoke_contract_fields
                from Dlg import DLG_Config_modeles_contrats as _smoke_contract_models
                from Dlg import DLG_Config_types_contrats as _smoke_contract_types
                from Dlg import DLG_Config_val_point as _smoke_point_values
                from Dlg import DLG_Config_verrouillage_entretien as _smoke_interview_lock
                from Dlg import DLG_Config_fonctions as _smoke_functions
                from Dlg import DLG_Config_affectations as _smoke_assignments
                from Dlg import DLG_Config_diffuseurs as _smoke_broadcasters
                from Dlg import DLG_Config_emplois as _smoke_jobs
                from Dlg import DLG_Config_gadgets as _smoke_gadgets
                from Dlg import DLG_Config_password as _smoke_password
                from Dlg import DLG_Config_sauvegarde as _smoke_backup

                _smoke_scenario = {scenario!r}
                _smoke_cycles = {cycles}
                _smoke_parameter_factories = (
                    ("Préférences d'affichage", _smoke_preferences.Dialog),
                    ("Enregistrement", _smoke_registration.Dialog),
                    ("Questionnaires", _smoke_questionnaires.Dialog),
                    ("Qualifications", _smoke_diplomas.Dialog),
                    ("Types de pièces", _smoke_pieces.Dialog),
                    ("Situations", _smoke_situations.Dialog),
                    ("Pays", _smoke_countries.Dialog),
                    ("Catégories de présences", _smoke_presence_categories.Dialog),
                    ("Classifications", _smoke_classifications.Dialog),
                    ("Champs de contrats", _smoke_contract_fields.Dialog),
                    ("Modèles de contrats", _smoke_contract_models.Dialog),
                    ("Types de contrats", _smoke_contract_types.Dialog),
                    ("Valeurs de points", _smoke_point_values.Dialog),
                    ("Protection des entretiens", _smoke_interview_lock.Dialog),
                    ("Fonctions", _smoke_functions.Dialog),
                    ("Affectations", _smoke_assignments.Dialog),
                    ("Diffuseurs", _smoke_broadcasters.Dialog),
                    ("Offres d'emploi", _smoke_jobs.Dialog),
                    ("Gadgets", _smoke_gadgets.Dialog),
                    ("Protection par mot de passe", _smoke_password.Dialog),
                )

                def _smoke_show_destroy(_smoke_window):
                    _smoke_window.Show()
                    _smoke_window.Layout()
                    _smoke_wx.Yield()
                    _smoke_window.Destroy()
                    _smoke_wx.Yield()

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1"
                )
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible")
                _smoke_person_id = _smoke_rows[0][0]

                def _smoke_pages():
                    _smoke_dialog = _smoke_person.Dialog(
                        frame,
                        IDpersonne=_smoke_person_id,
                    )
                    _smoke_dialog.Show()
                    _smoke_dialog.SetSize((900, 700))
                    _smoke_dialog.Layout()
                    _smoke_wx.Yield()
                    _smoke_notebook = _smoke_dialog.notebook
                    _smoke_notebook.SetSelection(0)
                    _smoke_dialog.Layout()
                    _smoke_wx.Yield()
                    _smoke_generalites = _smoke_notebook.pageGeneralites
                    _smoke_generalites.Layout()
                    _smoke_wx.Yield()
                    _smoke_scroll = _smoke_generalites._scroll_host
                    _smoke_target_y = max(
                        0,
                        _smoke_generalites.section_adresse.GetPosition().y // 12,
                    )
                    _smoke_scroll.Scroll(-1, _smoke_target_y)
                    _smoke_scroll.Layout()
                    _smoke_wx.Yield()
                    for _smoke_index in range(_smoke_notebook.GetPageCount()):
                        _smoke_notebook.SetSelection(_smoke_index)
                        _smoke_dialog.Layout()
                        _smoke_wx.Yield()
                    _smoke_dialog.Destroy()
                    _smoke_wx.Yield()

                def _smoke_close_reopen():
                    for _smoke_close_cycle in range(3):
                        _smoke_dialog = _smoke_person.Dialog(
                            frame,
                            IDpersonne=_smoke_person_id,
                        )
                        _smoke_dialog.Show()
                        _smoke_dialog.Layout()
                        _smoke_wx.Yield()
                        if _smoke_dialog.Fermer(save=True) is not True:
                            raise RuntimeError("Fermer(save=True) a échoué")
                        _smoke_wx.Yield()

                def _smoke_bug_report():
                    _smoke_dir = _smoke_tempfile.mkdtemp(prefix="tw-prelude-")
                    _smoke_path = _smoke_os.path.join(_smoke_dir, "crash-smoke.txt")
                    with open(_smoke_path, "w", encoding="utf-8") as _smoke_file:
                        _smoke_file.write("rapport technique smoke")
                    _smoke_dialog = _smoke_bug_reports.DLG_Rapport(
                        frame,
                        texte="rapport technique smoke",
                        chemin_rapport=_smoke_path,
                    )
                    _smoke_show_destroy(_smoke_dialog)
                    _smoke_os.remove(_smoke_path)
                    _smoke_os.rmdir(_smoke_dir)

                def _smoke_parameters(_smoke_count):
                    for _smoke_label, _smoke_factory in _smoke_parameter_factories[:_smoke_count]:
                        print(
                            "TEAMWORKS_SMOKE_PERSON_PRELUDE_PARAMETER:%s"
                            % _smoke_label,
                            flush=True,
                        )
                        _smoke_show_destroy(_smoke_factory(frame))

                def _smoke_backup_probe():
                    _smoke_dialog = _smoke_backup.MyFrame(frame)
                    _smoke_show_destroy(_smoke_dialog)

                for _smoke_cycle in range(_smoke_cycles):
                    print(
                        "TEAMWORKS_SMOKE_PERSON_PRELUDE_CYCLE:%s:%d/%d"
                        % (_smoke_scenario, _smoke_cycle + 1, _smoke_cycles),
                        flush=True,
                    )
                    if _smoke_scenario == "pages-backup":
                        _smoke_pages()
                    elif _smoke_scenario == "close-backup":
                        _smoke_close_reopen()
                    elif _smoke_scenario == "bug-report-backup":
                        _smoke_bug_report()
                    elif _smoke_scenario.startswith("prelude"):
                        _smoke_pages()
                        _smoke_close_reopen()
                        _smoke_bug_report()
                        if "params10" in _smoke_scenario:
                            _smoke_parameters(10)
                        elif "params20" in _smoke_scenario:
                            _smoke_parameters(20)
                    else:
                        raise RuntimeError(
                            "scénario préambule inconnu: %s" % _smoke_scenario
                        )
                    _smoke_backup_probe()

                print("TEAMWORKS_SMOKE_PERSON_PRELUDE_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_PRELUDE_FAILED", flush=True)
            _smoke_wx.CallAfter(self.ExitMainLoop)
            return True
'''


def build_patched_entrypoint(scenario: str, cycles: int) -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(
            f"ligne marqueur du smoke principal introuvable: count={marker_count}"
        )
    injection = build_injection(scenario, cycles)
    patched_core_source = core_source.replace(MARKER_LINE, injection, 1)
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_person_prelude_smoke as CORE"
    if import_line not in entrypoint_source:
        raise RuntimeError("import du cœur Teamworks introuvable")
    patched_entrypoint = entrypoint_source.replace(import_line, patched_import, 1)
    compile(patched_entrypoint, str(PATCHED), "exec")
    PATCHED.write_text(patched_entrypoint, encoding="utf-8")
    return marker_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    parser.add_argument("--cycles", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cycles < 1 or args.cycles > 20:
        raise SystemExit("--cycles doit être compris entre 1 et 20")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / f"diagnostic-{args.scenario}.txt"
    marker_count = None
    try:
        marker_count = build_patched_entrypoint(args.scenario, args.cycles)
        return_code, output = run_entrypoint(
            PATCHED,
            root=ROOT,
            teamworks_dir=TEAMWORKS_DIR,
            timeout=max(240, args.cycles * 120),
        )
        write_diagnostic(
            report,
            return_code=return_code,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        if return_code != 0 or FAILURE_MARKER in output or READY_MARKER not in output:
            github_error_summary(
                f"Person prelude lifecycle smoke failed ({args.scenario})",
                output,
            )
            return return_code or 1
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(
            report,
            return_code=3,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        github_error_summary(
            f"Person prelude lifecycle smoke failed ({args.scenario})",
            output,
        )
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
