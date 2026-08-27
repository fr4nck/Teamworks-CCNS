#!/usr/bin/env python3
"""Construit les dialogues critiques individu/paramétrage et refuse les fenêtres vides."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_person_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_person_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "person-dialog-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PERSON_DIALOG_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PERSON_DIALOG_FAILED"
STATICBOX_PARENT_WARNING = "of wxStaticBoxSizer should be created as child of its wxStaticBox"
# Le smoke doit instancier les vraies factories publiques utilisées par l'interface.

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                print("TEAMWORKS_SMOKE_PERSON_STAGE:imports", flush=True)
                import os as _smoke_os
                import tempfile as _smoke_tempfile
                import zipfile as _smoke_zipfile
                import GestionDB as _smoke_gestiondb
                from Utils import UTILS_Rapport_bugs as _smoke_bug_reports
                from Dlg import DLG_Fiche_individuelle as _smoke_person
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
                from Dlg import DLG_Config_gadgets
                from Dlg import DLG_Config_password
                from Dlg import DLG_Config_sauvegarde
                from Dlg import DLG_Saisie_password
                from Dlg import DLG_Saisie_procedure_sauvegarde
                from Dlg import DLG_Emails_exp
                from Dlg import DLG_Liste_contrats
                from Dlg import DLG_Preferences
                from Dlg import DLG_Vacances
                from Dlg import DLG_Feries

                def _smoke_descendants(_smoke_window):
                    _smoke_items = []
                    _smoke_stack = list(_smoke_window.GetChildren())
                    while _smoke_stack:
                        _smoke_child = _smoke_stack.pop()
                        _smoke_items.append(_smoke_child)
                        _smoke_stack.extend(_smoke_child.GetChildren())
                    return _smoke_items

                def _smoke_assert_populated(_smoke_dialog, _smoke_label):
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

                print("TEAMWORKS_SMOKE_PERSON_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucune personne disponible pour le smoke fiche individuelle")
                _smoke_person_id = _smoke_rows[0][0]

                print("TEAMWORKS_SMOKE_PERSON_STAGE:dialog", flush=True)
                _smoke_dialog = _smoke_person.Dialog(frame, IDpersonne=_smoke_person_id)
                _smoke_assert_populated(_smoke_dialog, "Fiche individuelle")

                print("TEAMWORKS_SMOKE_PERSON_STAGE:notebook", flush=True)
                _smoke_notebook = _smoke_dialog.notebook
                _smoke_expected_pages = (
                    "Généralités", "Questionnaire", "Qualifications", "Contrats",
                    "Présences", "Scénarios", "Frais", "Recrutement",
                )
                assert _smoke_dialog.IDpersonne == _smoke_person_id
                assert _smoke_dialog.GetTitle() == "Fiche individuelle"
                assert _smoke_notebook.GetPageCount() == len(_smoke_expected_pages)
                assert tuple(_smoke_notebook.GetPageText(_smoke_index) for _smoke_index in range(_smoke_notebook.GetPageCount())) == _smoke_expected_pages

                print("TEAMWORKS_SMOKE_PERSON_STAGE:pages", flush=True)
                for _smoke_index in range(_smoke_notebook.GetPageCount()):
                    _smoke_notebook.SetSelection(_smoke_index)
                    _smoke_dialog.Layout()
                    wx.Yield()
                    _smoke_page = _smoke_notebook.GetCurrentPage()
                    assert _smoke_page is not None
                    assert _smoke_page.GetSize().GetWidth() > 0
                    assert _smoke_page.GetSize().GetHeight() > 0
                    assert len(_smoke_descendants(_smoke_page)) >= 1

                assert _smoke_notebook.pageGeneralites is not None
                assert _smoke_notebook.pageContrats is not None
                assert _smoke_notebook.pagePresences is not None
                assert _smoke_notebook.pageCandidatures is not None
                assert _smoke_dialog.bitmap_button_Ok.IsEnabled()
                assert _smoke_dialog.AnnulationImpossible is True
                assert not _smoke_dialog.bitmap_button_annuler.IsEnabled()
                _smoke_dialog.Destroy()
                wx.Yield()

                print("TEAMWORKS_SMOKE_PERSON_STAGE:bug-report", flush=True)
                _smoke_crash_dir = _smoke_tempfile.mkdtemp(prefix="teamworks-crash-dialog-")
                _smoke_crash_path = _smoke_os.path.join(_smoke_crash_dir, "crash-smoke.txt")
                with open(_smoke_crash_path, "w", encoding="utf-8") as _smoke_file:
                    _smoke_file.write("rapport technique smoke")
                _smoke_crash_dialog = _smoke_bug_reports.DLG_Rapport(
                    frame,
                    texte="rapport technique smoke",
                    chemin_rapport=_smoke_crash_path,
                )
                _smoke_assert_populated(_smoke_crash_dialog, "Rapport de crash")
                assert _smoke_crash_dialog.bouton_envoyer.GetLabel() == "Envoyer le rapport"
                assert _smoke_crash_dialog.bouton_envoyer.IsEnabled()
                _smoke_crash_dialog.Destroy()
                _smoke_os.remove(_smoke_crash_path)
                _smoke_os.rmdir(_smoke_crash_dir)
                wx.Yield()

                print("TEAMWORKS_SMOKE_PERSON_STAGE:parametrage", flush=True)
                _smoke_parameter_dialogs = (
                    ("Préférences d'affichage", DLG_Preferences.Dialog),
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
                    ("Gadgets", DLG_Config_gadgets.Dialog),
                    ("Protection par mot de passe", DLG_Config_password.Dialog),
                    ("Sauvegardes automatiques", DLG_Config_sauvegarde.MyFrame),
                    ("Adresses d'expédition", DLG_Emails_exp.Dialog),
                    ("Registre des contrats", DLG_Liste_contrats.Dialog),
                    ("Vacances", DLG_Vacances.Dialog),
                    ("Jours fériés", DLG_Feries.Dialog),
                )
                for _smoke_label, _smoke_factory in _smoke_parameter_dialogs:
                    print("TEAMWORKS_SMOKE_PARAMETER_OPEN:%s" % _smoke_label, flush=True)
                    _smoke_parameter_dialog = _smoke_factory(frame)
                    _smoke_assert_populated(_smoke_parameter_dialog, _smoke_label)
                    _smoke_parameter_dialog.Destroy()
                    wx.Yield()
                    print("TEAMWORKS_SMOKE_PARAMETER_OK:%s" % _smoke_label, flush=True)

                print("TEAMWORKS_SMOKE_PERSON_STAGE:subdialogs", flush=True)
                _smoke_subdialogs = (
                    ("Saisie code de déverrouillage", DLG_Config_verrouillage_entretien.SaisiePassword),
                    ("Saisie mot de passe", DLG_Saisie_password.Dialog),
                    ("Paramètres sauvegarde automatique", DLG_Config_sauvegarde.Saisie_sauvegarde_auto),
                    ("Sauvegarde occasionnelle", DLG_Config_sauvegarde.Saisie_sauvegarde_occasionnelle),
                    ("Procédure de sauvegarde", lambda _smoke_parent: DLG_Saisie_procedure_sauvegarde.Dialog(_smoke_parent, IDsauvegarde=None)),
                )
                for _smoke_label, _smoke_factory in _smoke_subdialogs:
                    print("TEAMWORKS_SMOKE_SUBDIALOG_OPEN:%s" % _smoke_label, flush=True)
                    _smoke_subdialog = _smoke_factory(frame)
                    _smoke_assert_populated(_smoke_subdialog, _smoke_label)
                    _smoke_subdialog.Destroy()
                    wx.Yield()
                    print("TEAMWORKS_SMOKE_SUBDIALOG_OK:%s" % _smoke_label, flush=True)

                print("TEAMWORKS_SMOKE_PERSON_STAGE:restore", flush=True)
                _smoke_restore_dir = _smoke_tempfile.mkdtemp(prefix="teamworks-restore-")
                _smoke_restore_zip = _smoke_os.path.join(_smoke_restore_dir, "smoke.twz")
                with _smoke_zipfile.ZipFile(_smoke_restore_zip, "w") as _smoke_archive:
                    _smoke_archive.writestr("data===smoke.dat", b"smoke")
                _smoke_restore = DLG_Config_sauvegarde.Restauration(frame, fichierRestauration=_smoke_restore_zip)
                _smoke_assert_populated(_smoke_restore, "Restauration")
                _smoke_restore.Destroy()
                wx.Yield()
                print("TEAMWORKS_SMOKE_RESTORE_OK", flush=True)

                print("TEAMWORKS_SMOKE_PERSON_DIALOG_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PERSON_DIALOG_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"ligne marqueur du smoke principal introuvable: count={marker_count}")
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs de fiche individuelle absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_secondary_person_smoke as CORE"
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
        write_diagnostic(REPORT, return_code=return_code, marker_count=marker_count, ready_marker=READY_MARKER, failure_marker=FAILURE_MARKER, output=output)
        if STATICBOX_PARENT_WARNING in output:
            github_error_summary("Person dialog StaticBox parentage failed", output)
            return 4
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("Person dialog smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Person dialog smoke failed", output)
            print("marqueur de fiche individuelle absent", file=sys.stderr)
            return 2
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(REPORT, return_code=3, marker_count=marker_count, ready_marker=READY_MARKER, failure_marker=FAILURE_MARKER, output=output)
        github_error_summary("Person dialog smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
