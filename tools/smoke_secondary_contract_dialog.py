#!/usr/bin/env python3
"""Construit l'assistant de contrat réel et teste affichage + sauvegarde sous Windows."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
SOURCE = TEAMWORKS_DIR / "Teamworks.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_contract_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "contract-dialog-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:imports", flush=True)
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Creation_contrat as _smoke_contract
                from Utils import UTILS_CEE_baremes as _smoke_cee_rates

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:database", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDcontrat, IDpersonne FROM contrats ORDER BY IDcontrat LIMIT 1")
                _smoke_rows = _smoke_db.ResultatReq()
                _smoke_db.ExecuterReq("SELECT IDtype, nom, nom_abrege FROM contrats_types ORDER BY IDtype")
                _smoke_types = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_rows:
                    raise RuntimeError("aucun contrat disponible pour le smoke contrat")
                _smoke_contract_id, _smoke_person_id = _smoke_rows[0]
                _smoke_non_cee_type = None
                _smoke_cee_type = None
                for _type_id, _type_name, _type_short in _smoke_types:
                    _short = (_type_short or "").strip().upper()
                    _name = (_type_name or "").strip().lower()
                    _is_cee = _short == "CEE" or "engagement educatif" in _name or "engagement éducatif" in _name
                    if _is_cee and _smoke_cee_type is None:
                        _smoke_cee_type = _type_id
                    if not _is_cee and _smoke_non_cee_type is None:
                        _smoke_non_cee_type = _type_id
                if _smoke_non_cee_type is None:
                    raise RuntimeError("aucun type de contrat non CEE disponible")
                if _smoke_cee_type is None:
                    raise RuntimeError("aucun type CEE disponible")

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:dialog", flush=True)
                _smoke_dialog = _smoke_contract.Dialog(
                    frame,
                    IDcontrat=_smoke_contract_id,
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
                assert _smoke_dialog.dictContrats["IDcontrat"] == _smoke_contract_id
                assert _smoke_dialog.dictContrats["IDpersonne"] == _smoke_person_id
                assert _smoke_dialog.GetTitle() == "Modification d'un contrat"

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:forward", flush=True)
                for _smoke_target_page in range(2, 7):
                    _smoke_dialog.Onbouton_suite(None)
                    wx.Yield()
                    assert _smoke_dialog.pageVisible == _smoke_target_page
                    assert getattr(_smoke_dialog, "page%d" % _smoke_target_page).IsShown()
                    assert _smoke_dialog.bouton_retour.IsEnabled()

                assert _smoke_dialog.pageVisible == 6
                assert _smoke_dialog.page6.IsShown()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:backward", flush=True)
                for _smoke_target_page in range(5, 0, -1):
                    _smoke_dialog.Onbouton_retour(None)
                    wx.Yield()
                    assert _smoke_dialog.pageVisible == _smoke_target_page
                    assert getattr(_smoke_dialog, "page%d" % _smoke_target_page).IsShown()

                assert _smoke_dialog.pageVisible == 1
                assert _smoke_dialog.page1.IsShown()
                assert not _smoke_dialog.bouton_retour.IsEnabled()
                assert _smoke_dialog.bouton_suite.IsEnabled()
                _smoke_dialog.Destroy()
                wx.Yield()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:new-ccns", flush=True)
                _smoke_new = _smoke_contract.Dialog(
                    frame,
                    IDcontrat=0,
                    IDpersonne=_smoke_person_id,
                )
                _smoke_new.Show()
                wx.Yield()
                _smoke_page3 = _smoke_new.page3
                assert _smoke_new.dictContrats["convention_code"] == "CCNS"
                assert _smoke_page3.GetChoiceData(_smoke_page3.choice_convention) == "CCNS"
                assert _smoke_page3.choice_ccns_group.GetCount() == 8
                assert _smoke_page3.choice_ccns_group.IsShown()
                assert not _smoke_page3.choice_class.IsShown()
                assert not _smoke_page3.choice_valpoint.IsShown()
                assert _smoke_page3.sizer_ccns.GetStaticBox().IsShown()
                assert not _smoke_page3.sizer_cee.GetStaticBox().IsShown()
                assert _smoke_page3.weekly_hours.GetValue() == 35.0

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:save-ccns", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COALESCE(MAX(IDcontrat), 0) FROM contrats")
                _before_max = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()

                _smoke_new.dictChamps = {}
                _smoke_new.dictContrats.update({
                    "IDcontrat": 0,
                    "IDpersonne": _smoke_person_id,
                    "IDclassification": None,
                    "IDtype": _smoke_non_cee_type,
                    "valeur_point": None,
                    "cee_qualification": None,
                    "convention_code": "CCNS",
                    "ccns_group": "G1",
                    "weekly_hours": 35.0,
                    "gross_monthly_salary": 1900.0,
                    "date_debut": "2026-08-19",
                    "date_fin": "2999-01-01",
                    "date_rupture": "",
                    "essai": 30,
                })
                assert _smoke_new.page6.Validation() is True

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COALESCE(MAX(IDcontrat), 0) FROM contrats")
                _after_compliant = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _after_compliant > _before_max

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:block-noncompliant", flush=True)
                _old_message_box = wx.MessageBox
                try:
                    wx.MessageBox = lambda *args, **kwargs: wx.OK
                    _smoke_new.dictContrats["gross_monthly_salary"] = 1800.0
                    assert _smoke_new.page6.Validation() is False
                finally:
                    wx.MessageBox = _old_message_box

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COALESCE(MAX(IDcontrat), 0) FROM contrats")
                _after_blocked = _smoke_db.ResultatReq()[0][0]
                assert _after_blocked == _after_compliant
                _smoke_db.ReqDEL("contrats", "IDcontrat", _after_compliant)
                _smoke_db.Commit()
                _smoke_db.Close()

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:save-cee", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COALESCE(MAX(IDcontrat), 0) FROM contrats")
                _cee_before_max = _smoke_db.ResultatReq()[0][0]
                _cee_rate_id = _smoke_cee_rates.SaveRate(
                    _smoke_db,
                    "BAFA_HOLDER",
                    65.0,
                    "2099-12-31",
                )
                _smoke_db.Commit()
                _smoke_db.Close()

                _smoke_new.dictContrats.update({
                    "IDcontrat": 0,
                    "IDpersonne": _smoke_person_id,
                    "IDclassification": None,
                    "IDtype": _smoke_cee_type,
                    "valeur_point": None,
                    "cee_qualification": "BAFA_HOLDER",
                    "convention_code": "CCNS",
                    "ccns_group": None,
                    "weekly_hours": None,
                    "gross_monthly_salary": None,
                    "date_debut": "2099-12-31",
                    "date_fin": "2099-12-31",
                    "date_rupture": "",
                    "essai": 0,
                })
                assert _smoke_new.page6.Validation() is True

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COALESCE(MAX(IDcontrat), 0) FROM contrats")
                _cee_after_compliant = _smoke_db.ResultatReq()[0][0]
                _smoke_db.Close()
                assert _cee_after_compliant > _cee_before_max

                print("TEAMWORKS_SMOKE_CONTRACT_STAGE:block-cee-under-minimum", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_cee_rates.SaveRate(
                    _smoke_db,
                    "BAFA_HOLDER",
                    50.0,
                    "2099-12-31",
                )
                _smoke_db.Commit()
                _smoke_db.Close()
                _old_message_box = wx.MessageBox
                try:
                    wx.MessageBox = lambda *args, **kwargs: wx.OK
                    assert _smoke_new.page6.Validation() is False
                finally:
                    wx.MessageBox = _old_message_box

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT COALESCE(MAX(IDcontrat), 0) FROM contrats")
                _cee_after_blocked = _smoke_db.ResultatReq()[0][0]
                assert _cee_after_blocked == _cee_after_compliant
                _smoke_db.ReqDEL("contrats", "IDcontrat", _cee_after_compliant)
                _smoke_db.ReqDEL("contrats_cee_baremes", "IDbareme", _cee_rate_id)
                _smoke_db.Commit()
                _smoke_db.Close()

                _smoke_new.Destroy()
                wx.Yield()

                print("TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    marker_count = source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched_source = source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_source or FAILURE_MARKER not in patched_source:
        raise RuntimeError("injection des marqueurs du contrat absente")
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


if __name__ == "__main__":
    raise SystemExit(main())
