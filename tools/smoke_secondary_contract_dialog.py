#!/usr/bin/env python3
"""Crée, valide et relit un nouveau contrat CCNS dans l'application Windows."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_contract_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_contract_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "contract-dialog-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED"
STATICBOX_PARENT_WARNING = "of wxStaticBoxSizer should be created as child of its wxStaticBox"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_created_contract_id = None
            try:
                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:imports", flush=True)
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Creation_contrat as _smoke_contract

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:employee", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT p.IDpersonne FROM personnes p "
                    "LEFT JOIN contrats c ON c.IDpersonne=p.IDpersonne "
                    "GROUP BY p.IDpersonne HAVING COUNT(c.IDcontrat)=0 "
                    "ORDER BY p.IDpersonne LIMIT 1"
                )
                _smoke_rows = _smoke_db.ResultatReq()
                if not _smoke_rows:
                    _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                    _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq("SELECT COALESCE(MAX(IDcontrat), 0) FROM contrats")
                _smoke_contract_baseline = int(_smoke_db.ResultatReq()[0][0])
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucun salarié disponible pour le smoke contrat")
                _smoke_person_id = int(_smoke_rows[0][0])

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:dialog", flush=True)
                _smoke_dialog = _smoke_contract.Dialog(
                    frame,
                    IDcontrat=0,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_dialog.Show()
                wx.Yield()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:initial", flush=True)
                assert _smoke_dialog.nbrePages == 6
                assert _smoke_dialog.pageVisible == 1
                assert len(_smoke_dialog.listePages) == 6
                assert all(hasattr(_smoke_dialog, "page%d" % number) for number in range(1, 7))
                assert _smoke_dialog.page1.IsShown()
                assert not _smoke_dialog.page2.IsShown()
                assert not _smoke_dialog.bouton_retour.IsEnabled()
                assert _smoke_dialog.bouton_suite.IsEnabled()
                assert _smoke_dialog.bouton_annuler.IsEnabled()
                assert _smoke_dialog.dictContrats["IDcontrat"] == 0
                assert _smoke_dialog.dictContrats["IDpersonne"] == _smoke_person_id
                assert _smoke_dialog.GetTitle() == "Création d'un contrat"

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:new-contract", flush=True)
                _smoke_dialog.Onbouton_suite(None)
                wx.Yield()
                assert _smoke_dialog.pageVisible == 2
                assert _smoke_dialog.page2.radio_non.GetValue()

                _smoke_dialog.Onbouton_suite(None)
                wx.Yield()
                assert _smoke_dialog.pageVisible == 3

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:ccns", flush=True)
                assert _smoke_dialog.page3._SelectContractTypeCode("CDI")
                _smoke_dialog.page3.OnChoiceType(None)
                _smoke_dialog.page3._SelectConvention("CCNS")
                _smoke_dialog.page3.OnChoiceConvention(None)
                assert _smoke_dialog.page3.IsCCNSSelected()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:group", flush=True)
                _smoke_dialog.page3.SelectChoice(_smoke_dialog.page3.choice_ccns_group, "G1")
                assert _smoke_dialog.page3.GetChoiceData(_smoke_dialog.page3.choice_ccns_group) == "G1"
                _smoke_dialog.page3.OnCCNSFieldChanged(None)
                _smoke_dialog.page3.RefreshTrialProposal(force=True)
                assert _smoke_dialog.page3.check_trial.GetValue()
                assert _smoke_dialog.page3.trial_value.GetValue() > 0

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:salary", flush=True)
                _smoke_salary = _smoke_dialog.page3._MonthlySalaryDecimal()
                assert _smoke_salary is not None and _smoke_salary > 0
                assert _smoke_dialog.page3.last_ccns_preview is not None
                assert _smoke_dialog.page3.last_ccns_preview.compliant

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:validation", flush=True)
                _smoke_dialog.Onbouton_suite(None)
                wx.Yield()
                assert _smoke_dialog.pageVisible == 4
                assert _smoke_dialog.dictContrats["convention_code"] == "CCNS"
                assert _smoke_dialog.dictContrats["ccns_group"] == "G1"
                assert _smoke_dialog.dictContrats["gross_monthly_salary"] == float(_smoke_salary)

                _smoke_dialog.Onbouton_suite(None)
                wx.Yield()
                assert _smoke_dialog.pageVisible == 6
                assert _smoke_dialog.page6.IsShown()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:save", flush=True)
                assert _smoke_dialog.ValidationPages()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:database-readback", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq(
                    "SELECT IDcontrat, convention_code, ccns_group, gross_monthly_salary "
                    "FROM contrats WHERE IDpersonne=%d AND IDcontrat>%d "
                    "ORDER BY IDcontrat DESC LIMIT 1"
                    % (_smoke_person_id, _smoke_contract_baseline)
                )
                _smoke_saved_rows = _smoke_db.ResultatReq()
                _smoke_db.Close()
                assert len(_smoke_saved_rows) == 1
                _smoke_created_contract_id, _smoke_convention, _smoke_group, _smoke_saved_salary = _smoke_saved_rows[0]
                assert _smoke_convention == "CCNS"
                assert _smoke_group == "G1"
                assert abs(float(_smoke_saved_salary) - float(_smoke_salary)) < 0.01

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:document-selector", flush=True)
                import Chemins as _smoke_paths
                from Dlg import DLG_Selection_type_document as _smoke_document_selector
                _smoke_document_buttons = [
                    (
                        _smoke_paths.GetStaticPath("Images/BoutonsImages/Imprimer_doc_DUE.png"),
                        "DUE",
                    ),
                    (
                        _smoke_paths.GetStaticPath("Images/BoutonsImages/Imprimer_doc_contrat.png"),
                        "Contrat",
                    ),
                ]
                _smoke_selector = _smoke_document_selector.Dialog(
                    frame,
                    size=(450, 335),
                    listeBoutons=_smoke_document_buttons,
                    type="contrats",
                )
                _smoke_selector.Show()
                wx.Yield()
                assert _smoke_selector.GetSize().GetWidth() >= 450
                assert _smoke_selector.GetSize().GetHeight() >= 335
                for _smoke_button_index in range(1, 3):
                    _smoke_button = getattr(_smoke_selector, "bouton_%d" % _smoke_button_index)
                    assert _smoke_button.GetSize().GetHeight() >= 200
                _smoke_selector.Destroy()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:mailmerge", flush=True)
                from Utils import UTILS_Publipostage_donnees as _smoke_mailmerge_data
                from Dlg import DLG_Publiposteur_contrat as _smoke_mailmerge
                _smoke_print_data = _smoke_mailmerge_data.GetDictDonnees(
                    categorie="contrat",
                    listeID=[_smoke_created_contract_id],
                )
                _smoke_mailmerge_dialog = _smoke_mailmerge.Dialog(
                    frame,
                    "",
                    dictDonnees=_smoke_print_data,
                )
                assert _smoke_mailmerge_dialog.page4.listCtrl.parent is _smoke_mailmerge_dialog.page4
                _smoke_mailmerge_dialog.page3.numChoix = 1
                _smoke_mailmerge_dialog.page4.MAJaffichage()
                assert _smoke_mailmerge_dialog.page4.choixLogiciel == 1
                _smoke_mailmerge_dialog.Destroy()

                print("TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY", flush=True)
                _smoke_dialog.Destroy()
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                if _smoke_created_contract_id is not None:
                    _smoke_cleanup = _smoke_gestiondb.DB()
                    _smoke_cleanup.ReqDEL("contrats_valchamps", "IDcontrat", _smoke_created_contract_id)
                    _smoke_cleanup.ReqDEL("contrats", "IDcontrat", _smoke_created_contract_id)
                    _smoke_cleanup.Commit()
                    _smoke_cleanup.Close()
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs du contrat absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_secondary_contract_smoke as CORE"
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
        if STATICBOX_PARENT_WARNING in output:
            github_error_summary("Contract dialog StaticBox parentage failed", output)
            return 4
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("Contract dialog smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Contract dialog smoke failed", output)
            print("marqueur du contrat absent", file=sys.stderr)
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
        github_error_summary("Contract dialog smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
