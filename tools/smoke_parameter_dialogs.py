#!/usr/bin/env python3
"""Ouvre les dialogues de paramétrage réellement exposés et refuse les fenêtres vides/bloquées."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_parameter_dialogs_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_parameter_dialogs_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "parameter-dialogs-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PARAMETER_DIALOGS_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PARAMETER_DIALOGS_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                print("TEAMWORKS_SMOKE_PARAMETER_STAGE:imports", flush=True)
                from Dlg import DLG_Enregistrement
                from Dlg import DLG_Config_questionnaires
                from Dlg import DLG_Config_types_diplomes
                from Dlg import DLG_Config_types_pieces
                from Dlg import DLG_Config_situations
                from Dlg import DLG_Config_pays
                from Dlg import DLG_Config_categories_presences
                from Dlg import DLG_Config_classifications
                from Dlg import DLG_Config_champs_contrats
                from Dlg import DLG_Config_modeles_contrats
                from Dlg import DLG_Config_types_contrats
                from Dlg import DLG_Config_val_point
                from Dlg import DLG_Config_verrouillage_entretien
                from Dlg import DLG_Config_fonctions
                from Dlg import DLG_Config_affectations
                from Dlg import DLG_Config_diffuseurs
                from Dlg import DLG_Config_emplois
                from Dlg import DLG_Vacances
                from Dlg import DLG_Feries

                _smoke_dialogs = (
                    ("Enregistrement", DLG_Enregistrement.Dialog),
                    ("Questionnaires", DLG_Config_questionnaires.Dialog),
                    ("Qualifications", DLG_Config_types_diplomes.Dialog),
                    ("Types de pièces", DLG_Config_types_pieces.Dialog),
                    ("Situations", DLG_Config_situations.Dialog),
                    ("Pays", DLG_Config_pays.Dialog),
                    ("Catégories de présences", DLG_Config_categories_presences.Dialog),
                    ("Classifications", DLG_Config_classifications.Dialog),
                    ("Champs de contrats", DLG_Config_champs_contrats.Dialog),
                    ("Modèles de contrats", DLG_Config_modeles_contrats.Dialog),
                    ("Types de contrats", DLG_Config_types_contrats.Dialog),
                    ("Valeurs de points", DLG_Config_val_point.Dialog),
                    ("Protection des entretiens", DLG_Config_verrouillage_entretien.Dialog),
                    ("Fonctions", DLG_Config_fonctions.Dialog),
                    ("Affectations", DLG_Config_affectations.Dialog),
                    ("Diffuseurs", DLG_Config_diffuseurs.Dialog),
                    ("Offres d'emploi", DLG_Config_emplois.Dialog),
                    ("Vacances", DLG_Vacances.Dialog),
                    ("Jours fériés", DLG_Feries.Dialog),
                )

                def _smoke_descendants(window):
                    _items = []
                    _stack = list(window.GetChildren())
                    while _stack:
                        _child = _stack.pop()
                        _items.append(_child)
                        _stack.extend(_child.GetChildren())
                    return _items

                print("TEAMWORKS_SMOKE_PARAMETER_STAGE:dialogs", flush=True)
                for _smoke_label, _smoke_factory in _smoke_dialogs:
                    print("TEAMWORKS_SMOKE_PARAMETER_OPEN:%s" % _smoke_label, flush=True)
                    _smoke_dialog = _smoke_factory(frame)
                    _smoke_dialog.Show()
                    _smoke_dialog.Layout()
                    wx.Yield()

                    _smoke_size = _smoke_dialog.GetClientSize()
                    _smoke_desc = _smoke_descendants(_smoke_dialog)
                    _smoke_visible = [
                        _smoke_child for _smoke_child in _smoke_desc
                        if _smoke_child.IsShownOnScreen()
                        and _smoke_child.GetSize().GetWidth() > 0
                        and _smoke_child.GetSize().GetHeight() > 0
                    ]

                    assert _smoke_dialog.IsShown(), "%s: dialogue non affiché" % _smoke_label
                    assert _smoke_size.GetWidth() >= 100, "%s: largeur vide" % _smoke_label
                    assert _smoke_size.GetHeight() >= 80, "%s: hauteur vide" % _smoke_label
                    assert len(_smoke_desc) >= 2, "%s: contenu non construit" % _smoke_label
                    assert len(_smoke_visible) >= 1, "%s: aucun contrôle visible" % _smoke_label

                    _smoke_dialog.Destroy()
                    wx.Yield()
                    print("TEAMWORKS_SMOKE_PARAMETER_OK:%s" % _smoke_label, flush=True)

                print("TEAMWORKS_SMOKE_PARAMETER_DIALOGS_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PARAMETER_DIALOGS_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur du smoke principal introuvable: {marker_count}")

    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs de paramétrage absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_parameter_dialogs_smoke as CORE"
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
            github_error_summary("Parameter dialogs smoke failed", output)
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
        github_error_summary("Parameter dialogs smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
