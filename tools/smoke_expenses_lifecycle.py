#!/usr/bin/env python3
"""Qualifie le cycle réel déplacement -> remboursement sous Windows."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_expenses_lifecycle_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_expenses_lifecycle_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "expenses-lifecycle-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_EXPENSES_LIFECYCLE_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_EXPENSES_LIFECYCLE_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_person_id = None
            _smoke_deplacement_id = None
            _smoke_remboursement_id = None
            _smoke_create_move = None
            _smoke_edit_move = None
            _smoke_create_refund = None
            _smoke_edit_refund = None
            _smoke_manager = None
            try:
                import datetime as _smoke_datetime
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Saisie_deplacement as _smoke_move
                from Dlg import DLG_Saisie_remboursement as _smoke_refund
                from Dlg import DLG_Gestion_frais as _smoke_expenses

                def _smoke_cleanup():
                    _db = _smoke_gestiondb.DB()
                    if _smoke_deplacement_id is not None:
                        _db.ReqDEL("deplacements", "IDdeplacement", _smoke_deplacement_id)
                    if _smoke_remboursement_id is not None:
                        _db.ReqDEL("remboursements", "IDremboursement", _smoke_remboursement_id)
                    if _smoke_person_id is not None:
                        _db.ReqDEL("personnes", "IDpersonne", _smoke_person_id)
                    _db.Commit()
                    _db.Close()

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:fixture", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_person_id = _smoke_db.ReqInsert(
                    "personnes",
                    [
                        ("civilite", "Mr"),
                        ("nom", "__TEAMWORKS_SMOKE_FRAIS__"),
                        ("prenom", "Recette"),
                    ],
                )
                _smoke_db.Commit()
                _smoke_db.Close()
                assert _smoke_person_id not in (None, 0)

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:create-move-dialog", flush=True)
                _smoke_create_move = _smoke_move.SaisieDeplacement(
                    frame,
                    IDdeplacement=None,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_create_move.Show()
                wx.Yield()
                _smoke_create_move.SetDate(_smoke_datetime.date(2026, 9, 2))
                _smoke_create_move.ctrl_objet.SetValue("__TEAMWORKS_SMOKE_TRAJET_CREATE__")
                _smoke_create_move.SetVilleDepart(cp="35000", ville="RENNES")
                _smoke_create_move.SetVilleArrivee(cp="35500", ville="VITRE")
                _smoke_create_move.ctrl_distance.SetValue("42")
                _smoke_create_move.ctrl_aller_retour.SetValue(False)
                _smoke_create_move.ctrl_tarif.SetValue("0.50")

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:create-move-save", flush=True)
                _smoke_deplacement_id = _smoke_create_move.SauvegardeDeplacement()
                assert _smoke_deplacement_id not in (None, 0)

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:create-move-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne, date, objet, cp_depart, ville_depart, cp_arrivee, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement "
                    "FROM deplacements WHERE IDdeplacement=%d" % _smoke_deplacement_id
                )
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_rows) == 1
                _smoke_created = _smoke_rows[0]
                assert _smoke_created[0] == _smoke_person_id
                assert str(_smoke_created[1]) == "2026-09-02"
                assert _smoke_created[2] == "__TEAMWORKS_SMOKE_TRAJET_CREATE__"
                assert str(_smoke_created[3]).strip() == "35000"
                assert _smoke_created[4] == "RENNES"
                assert str(_smoke_created[5]).strip() == "35500"
                assert _smoke_created[6] == "VITRE"
                assert float(_smoke_created[7]) == 42.0
                assert float(_smoke_created[9]) == 0.50
                assert _smoke_created[10] in (None, 0)

                _smoke_create_move.Destroy()
                _smoke_create_move = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:edit-move-dialog", flush=True)
                _smoke_edit_move = _smoke_move.SaisieDeplacement(
                    frame,
                    IDdeplacement=_smoke_deplacement_id,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_edit_move.Show()
                wx.Yield()
                assert _smoke_edit_move.ctrl_objet.GetValue() == "__TEAMWORKS_SMOKE_TRAJET_CREATE__"
                assert float(_smoke_edit_move.ctrl_distance.GetValue()) == 42.0
                _smoke_edit_move.ctrl_objet.SetValue("__TEAMWORKS_SMOKE_TRAJET_EDIT__")
                _smoke_edit_move.ctrl_distance.SetValue("48")
                _smoke_edit_move.ctrl_tarif.SetValue("0.55")

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:edit-move-save", flush=True)
                assert _smoke_edit_move.SauvegardeDeplacement() == _smoke_deplacement_id
                _smoke_edit_move.Destroy()
                _smoke_edit_move = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:create-refund-dialog", flush=True)
                _smoke_create_refund = _smoke_refund.SaisieRemboursement(
                    frame,
                    IDremboursement=None,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_create_refund.Show()
                wx.Yield()
                _smoke_create_refund.SetDate(_smoke_datetime.date(2026, 9, 15))
                _smoke_create_refund.ctrl_montant.SetValue("26.40")
                _smoke_row_index = None
                for _index in range(_smoke_create_refund.ctrl_deplacements.GetItemCount()):
                    if int(_smoke_create_refund.ctrl_deplacements.GetItem(_index, 0).GetText()) == _smoke_deplacement_id:
                        _smoke_row_index = _index
                        break
                assert _smoke_row_index is not None
                _smoke_create_refund.ctrl_deplacements._set_checked(_smoke_row_index, True)
                _checked, _unchecked = _smoke_create_refund.ctrl_deplacements.ListeItemsCoches()
                assert _smoke_deplacement_id in _checked

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:create-refund-save", flush=True)
                _smoke_remboursement_id = _smoke_create_refund.Sauvegarde()
                assert _smoke_remboursement_id not in (None, 0)

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:refund-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne, date, montant, listeIDdeplacement FROM remboursements WHERE IDremboursement=%d"
                    % _smoke_remboursement_id
                )
                _smoke_refund_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq(
                    "SELECT objet, distance, tarif_km, IDremboursement FROM deplacements WHERE IDdeplacement=%d"
                    % _smoke_deplacement_id
                )
                _smoke_move_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_refund_rows) == 1
                assert _smoke_refund_rows[0][0] == _smoke_person_id
                assert str(_smoke_refund_rows[0][1]) == "2026-09-15"
                assert float(_smoke_refund_rows[0][2]) == 26.40
                assert str(_smoke_deplacement_id) in str(_smoke_refund_rows[0][3])
                assert len(_smoke_move_rows) == 1
                assert _smoke_move_rows[0][0] == "__TEAMWORKS_SMOKE_TRAJET_EDIT__"
                assert float(_smoke_move_rows[0][1]) == 48.0
                assert float(_smoke_move_rows[0][2]) == 0.55
                assert _smoke_move_rows[0][3] == _smoke_remboursement_id

                _smoke_create_refund.Destroy()
                _smoke_create_refund = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:edit-refund-dialog", flush=True)
                _smoke_edit_refund = _smoke_refund.SaisieRemboursement(
                    frame,
                    IDremboursement=_smoke_remboursement_id,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_edit_refund.Show()
                wx.Yield()
                assert float(_smoke_edit_refund.ctrl_montant.GetValue()) == 26.40
                _checked, _unchecked = _smoke_edit_refund.ctrl_deplacements.ListeItemsCoches()
                assert _smoke_deplacement_id in _checked
                _smoke_edit_refund.ctrl_montant.SetValue("27.00")
                assert _smoke_edit_refund.Sauvegarde() == _smoke_remboursement_id
                _smoke_edit_refund.Destroy()
                _smoke_edit_refund = None
                wx.Yield()

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:manager", flush=True)
                _smoke_manager = _smoke_expenses.Dialog(frame)
                _smoke_manager.Show()
                wx.Yield()
                assert _smoke_manager.GetName() == "frm_gestion_frais"
                _smoke_manager.ctrl_check_tous.SetValue(True)
                _smoke_manager.ctrl_check_nonRembourses.SetValue(False)
                _smoke_manager.ctrl_personnes.MAJListeCtrl()
                assert any(
                    values[0] == _smoke_person_id
                    for values in _smoke_manager.ctrl_personnes.donnees.values()
                )
                _smoke_manager.IDpersonne = _smoke_person_id
                _smoke_manager.nomPersonne = "__TEAMWORKS_SMOKE_FRAIS__ Recette"
                _smoke_manager.MAJlistes()
                wx.Yield()
                assert _smoke_manager.panel_pageFrais.ctrl_deplacements.GetItemCount() >= 1
                assert _smoke_manager.panel_pageFrais.ctrl_remboursements.GetItemCount() >= 1
                assert "__TEAMWORKS_SMOKE_FRAIS__" in _smoke_manager.panel_pageFrais.section_deplacements.titre.GetLabel()
                assert "__TEAMWORKS_SMOKE_FRAIS__" in _smoke_manager.panel_pageFrais.section_remboursements.titre.GetLabel()

                print("TEAMWORKS_SMOKE_EXPENSES_STAGE:cleanup", flush=True)
                _smoke_manager.Destroy()
                _smoke_manager = None
                wx.Yield()
                _smoke_cleanup()
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM deplacements WHERE IDdeplacement=%d" % _smoke_deplacement_id)
                assert _smoke_db.ResultatReq()[0][0] == 0
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM remboursements WHERE IDremboursement=%d" % _smoke_remboursement_id)
                assert _smoke_db.ResultatReq()[0][0] == 0
                _smoke_db.ExecuterReq("SELECT COUNT(*) FROM personnes WHERE IDpersonne=%d" % _smoke_person_id)
                assert _smoke_db.ResultatReq()[0][0] == 0
                _smoke_db.Close()

                print("TEAMWORKS_SMOKE_EXPENSES_LIFECYCLE_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                try:
                    _smoke_cleanup()
                except Exception:
                    _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_EXPENSES_LIFECYCLE_FAILED", flush=True)
                raise
            finally:
                for _window in (
                    _smoke_create_move,
                    _smoke_edit_move,
                    _smoke_create_refund,
                    _smoke_edit_refund,
                    _smoke_manager,
                ):
                    if _window is not None:
                        try:
                            _window.Destroy()
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
    patched_import = "import Teamworks_core_expenses_lifecycle_smoke as CORE"
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
            timeout=90,
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
            github_error_summary("Expenses lifecycle smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Expenses lifecycle smoke failed", output)
            print("marqueur du cycle Frais absent", file=sys.stderr)
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
        github_error_summary("Expenses lifecycle smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
