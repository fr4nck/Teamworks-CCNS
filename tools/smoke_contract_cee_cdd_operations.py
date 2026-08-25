#!/usr/bin/env python3
"""Qualifie en UI Windows le CEE, le renouvellement CDD et le passage CDD vers CDI."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_contract_operations_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_contract_operations_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "contract-operations-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_CONTRACT_OPERATIONS_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_CONTRACT_OPERATIONS_FAILED"
STATICBOX_PARENT_WARNING = "of wxStaticBoxSizer should be created as child of its wxStaticBox"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_created_contract_ids = []
            _smoke_previous_contract_id = None
            _smoke_rate_id = None
            _smoke_rate_previous = None
            try:
                print("TEAMWORKS_SMOKE_CONTRACT_OP_STAGE:imports", flush=True)
                import datetime as _smoke_datetime
                from decimal import Decimal as _smoke_decimal
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Creation_contrat as _smoke_contract
                from Utils import UTILS_CEE_baremes as _smoke_cee_baremes
                from Utils import UTILS_Contrats_schema as _smoke_contract_schema

                print("TEAMWORKS_SMOKE_CONTRACT_OP_STAGE:fixtures", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_contract_schema.EnsureContractEngineColumns(_smoke_db)
                _smoke_cee_baremes.EnsureTable(_smoke_db)

                _smoke_db.ExecuterReq(
                    "SELECT IDpersonne FROM personnes "
                    "WHERE date_naiss IS NOT NULL AND date_naiss<>'' AND date_naiss<='2000-01-01' "
                    "ORDER BY IDpersonne LIMIT 1"
                )
                _smoke_people = _smoke_db.ResultatReq()
                if not _smoke_people:
                    raise RuntimeError("aucun salarié adulte disponible pour le smoke contrats")
                _smoke_person_id = int(_smoke_people[0][0])

                _smoke_db.ExecuterReq(
                    "SELECT IDtype FROM contrats_types "
                    "WHERE UPPER(COALESCE(nom_abrege, ''))='CDD' ORDER BY IDtype LIMIT 1"
                )
                _smoke_cdd_rows = _smoke_db.ResultatReq()
                if not _smoke_cdd_rows:
                    raise RuntimeError("type CDD introuvable dans la base de smoke")
                _smoke_cdd_type_id = int(_smoke_cdd_rows[0][0])

                _smoke_rate_date = "2026-08-25"
                _smoke_db.ExecuterReq(
                    "SELECT IDbareme, montant_journalier FROM contrats_cee_baremes "
                    "WHERE qualification='BAFA_HOLDER' AND date_debut='%s' ORDER BY IDbareme DESC LIMIT 1"
                    % _smoke_rate_date
                )
                _smoke_rate_rows = _smoke_db.ResultatReq()
                if _smoke_rate_rows:
                    _smoke_rate_previous = (_smoke_rate_rows[0][0], _smoke_rate_rows[0][1])
                _smoke_rate_id = _smoke_cee_baremes.SaveRate(
                    _smoke_db,
                    "BAFA_HOLDER",
                    _smoke_decimal("100.00"),
                    _smoke_rate_date,
                )

                _smoke_previous_contract_id = _smoke_db.ReqInsert(
                    "contrats",
                    [
                        ("IDpersonne", _smoke_person_id),
                        ("IDtype", _smoke_cdd_type_id),
                        ("date_debut", "2026-01-01"),
                        ("date_fin", "2026-03-31"),
                        ("date_rupture", ""),
                        ("essai", 0),
                        ("operation_type", "NEW"),
                        ("previous_contract_id", None),
                        ("signature", ""),
                        ("due", ""),
                    ],
                )
                _smoke_db.Commit()
                _smoke_db.Close()

                def _smoke_open_dialog():
                    dialog = _smoke_contract.Dialog(frame, IDcontrat=0, IDpersonne=_smoke_person_id)
                    dialog.Show()
                    wx.Yield()
                    assert dialog.pageVisible == 1
                    dialog.Onbouton_suite(None)
                    wx.Yield()
                    assert dialog.pageVisible == 2
                    dialog.Onbouton_suite(None)
                    wx.Yield()
                    assert dialog.pageVisible == 3
                    return dialog

                def _smoke_finish_and_read(dialog):
                    probe = _smoke_gestiondb.DB()
                    probe.ExecuterReq("SELECT COALESCE(MAX(IDcontrat), 0) FROM contrats")
                    baseline = int(probe.ResultatReq()[0][0])
                    probe.Close()

                    dialog.Onbouton_suite(None)
                    wx.Yield()
                    assert dialog.pageVisible == 4
                    dialog.Onbouton_suite(None)
                    wx.Yield()
                    assert dialog.pageVisible == 6
                    assert dialog.ValidationPages()

                    probe = _smoke_gestiondb.DB()
                    probe.ExecuterReq(
                        "SELECT c.IDcontrat, t.nom_abrege, c.cee_qualification, c.ccns_group, "
                        "c.operation_type, c.previous_contract_id, c.trial_period_value, "
                        "c.trial_period_unit, c.date_debut, c.date_fin "
                        "FROM contrats c LEFT JOIN contrats_types t ON t.IDtype=c.IDtype "
                        "WHERE c.IDpersonne=%d AND c.IDcontrat>%d ORDER BY c.IDcontrat DESC LIMIT 1"
                        % (_smoke_person_id, baseline)
                    )
                    rows = probe.ResultatReq()
                    probe.Close()
                    assert len(rows) == 1
                    created_id = int(rows[0][0])
                    _smoke_created_contract_ids.append(created_id)
                    dialog.Destroy()
                    wx.Yield()
                    return rows[0]

                def _smoke_prepare_ccns_operation(dialog, operation, start_date, end_date=None):
                    page = dialog.page3
                    page.SelectChoice(page.choice_operation, operation)
                    page.OnOperationChanged(None)
                    page.SelectChoice(page.choice_previous_contract, _smoke_previous_contract_id)
                    assert page.GetChoiceData(page.choice_previous_contract) == _smoke_previous_contract_id
                    page.SetDatePicker(page.datepicker_date_debut, start_date)
                    if end_date is not None:
                        page.SetDatePicker(page.datepicker_date_fin, end_date)
                    page.OnContractDateChanged(None)
                    page._SelectConvention("CCNS")
                    page.OnChoiceConvention(None)
                    page.RefreshCCNSGroups(preserve="G1")
                    page.SelectChoice(page.choice_ccns_group, "G1")
                    assert page.GetChoiceData(page.choice_ccns_group) == "G1"
                    page.OnCCNSFieldChanged(None)
                    page.RefreshTrialProposal(force=True)
                    salary = page._MonthlySalaryDecimal()
                    assert salary is not None and salary > 0
                    assert page.last_ccns_preview is not None
                    assert page.last_ccns_preview.compliant
                    return page

                print("TEAMWORKS_SMOKE_CONTRACT_OP_STAGE:cee", flush=True)
                _smoke_cee = _smoke_open_dialog()
                assert _smoke_cee.page3._SelectContractTypeCode("CEE")
                _smoke_cee.page3.OnChoiceType(None)
                assert _smoke_cee.page3.IsCEESelected()
                _smoke_cee.page3.SelectChoice(_smoke_cee.page3.choice_cee_qualification, "BAFA_HOLDER")
                _smoke_cee.page3.SetDatePicker(_smoke_cee.page3.datepicker_date_debut, "2026-08-25")
                _smoke_cee.page3.SetDatePicker(_smoke_cee.page3.datepicker_date_fin, "2026-08-31")
                _smoke_cee.page3.OnContractDateChanged(None)
                _smoke_cee.page3.OnCEEFieldChanged(None)
                assert "CONFORME" in _smoke_cee.page3.label_cee_preview.GetLabel()
                _smoke_cee.dictContrats["cee_days_rolling_12_months"] = 7
                _smoke_cee.dictContrats["cee_average_weekly_hours_6m"] = _smoke_decimal("20.00")
                _smoke_cee.dictContrats["cee_planned_max_daily_hours"] = _smoke_decimal("8.00")
                _smoke_cee.dictContrats["cee_planned_max_weekly_hours"] = _smoke_decimal("35.00")
                _smoke_cee_row = _smoke_finish_and_read(_smoke_cee)
                assert (_smoke_cee_row[1] or "").upper() == "CEE"
                assert _smoke_cee_row[2] == "BAFA_HOLDER"
                assert _smoke_cee_row[3] is None
                assert _smoke_cee_row[4] == "NEW"
                assert _smoke_cee_row[5] is None
                assert int(_smoke_cee_row[6] or 0) == 0

                print("TEAMWORKS_SMOKE_CONTRACT_OP_STAGE:cdd-renewal", flush=True)
                _smoke_renewal = _smoke_open_dialog()
                _smoke_renewal_page = _smoke_prepare_ccns_operation(
                    _smoke_renewal,
                    "CDD_RENEWAL",
                    "2026-04-01",
                    "2026-06-30",
                )
                assert _smoke_renewal_page._CurrentContractType().value == "CDD"
                assert not _smoke_renewal_page.check_trial.GetValue()
                assert _smoke_renewal_page.trial_value.GetValue() == 0
                _smoke_renewal_row = _smoke_finish_and_read(_smoke_renewal)
                assert (_smoke_renewal_row[1] or "").upper() == "CDD"
                assert _smoke_renewal_row[3] == "G1"
                assert _smoke_renewal_row[4] == "CDD_RENEWAL"
                assert int(_smoke_renewal_row[5]) == _smoke_previous_contract_id
                assert int(_smoke_renewal_row[6] or 0) == 0
                assert _smoke_renewal_row[8] == "2026-04-01"
                assert _smoke_renewal_row[9] == "2026-06-30"

                print("TEAMWORKS_SMOKE_CONTRACT_OP_STAGE:cdd-to-cdi", flush=True)
                _smoke_cdi = _smoke_open_dialog()
                _smoke_cdi_page = _smoke_prepare_ccns_operation(
                    _smoke_cdi,
                    "CDD_TO_CDI",
                    "2026-04-01",
                )
                assert _smoke_cdi_page._CurrentContractType().value == "CDI"
                assert not _smoke_cdi_page.check_trial.GetValue()
                assert _smoke_cdi_page.trial_value.GetValue() == 0
                _smoke_cdi_row = _smoke_finish_and_read(_smoke_cdi)
                assert (_smoke_cdi_row[1] or "").upper() == "CDI"
                assert _smoke_cdi_row[3] == "G1"
                assert _smoke_cdi_row[4] == "CDD_TO_CDI"
                assert int(_smoke_cdi_row[5]) == _smoke_previous_contract_id
                assert int(_smoke_cdi_row[6] or 0) == 0
                assert _smoke_cdi_row[8] == "2026-04-01"
                assert _smoke_cdi_row[9] == "2999-01-01"

                print("TEAMWORKS_SMOKE_CONTRACT_OPERATIONS_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_CONTRACT_OPERATIONS_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                try:
                    _smoke_cleanup = _smoke_gestiondb.DB()
                    for _smoke_contract_id in reversed(_smoke_created_contract_ids):
                        _smoke_cleanup.ReqDEL("contrats_valchamps", "IDcontrat", _smoke_contract_id)
                        _smoke_cleanup.ReqDEL("contrats", "IDcontrat", _smoke_contract_id)
                    if _smoke_previous_contract_id is not None:
                        _smoke_cleanup.ReqDEL("contrats_valchamps", "IDcontrat", _smoke_previous_contract_id)
                        _smoke_cleanup.ReqDEL("contrats", "IDcontrat", _smoke_previous_contract_id)
                    if _smoke_rate_id is not None:
                        if _smoke_rate_previous is None:
                            _smoke_cleanup.ReqDEL("contrats_cee_baremes", "IDbareme", _smoke_rate_id)
                        else:
                            _smoke_cleanup.ReqMAJ(
                                "contrats_cee_baremes",
                                [("montant_journalier", _smoke_rate_previous[1])],
                                "IDbareme",
                                _smoke_rate_previous[0],
                            )
                    _smoke_cleanup.Commit()
                    _smoke_cleanup.Close()
                except Exception:
                    _smoke_traceback.print_exc()
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs des opérations contrat absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_contract_operations_smoke as CORE"
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
            github_error_summary("Contract operations StaticBox parentage failed", output)
            return 4
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("Contract operations smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Contract operations smoke failed", output)
            print("marqueur des opérations contrat absent", file=sys.stderr)
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
        github_error_summary("Contract operations smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
