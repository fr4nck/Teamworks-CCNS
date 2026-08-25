#!/usr/bin/env python3
"""Qualifie dans l'application Windows les contrats PMSL prioritaires à 21 h."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_pmsl_contracts_21h_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_pmsl_contracts_21h_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "pmsl-contracts-21h-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_PMSL_CONTRACTS_21H_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_PMSL_CONTRACTS_21H_FAILED"
STATICBOX_PARENT_WARNING = "of wxStaticBoxSizer should be created as child of its wxStaticBox"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_created_contract_ids = []
            _smoke_previous_contract_id = None
            try:
                print("TEAMWORKS_SMOKE_PMSL_21H_STAGE:fixtures", flush=True)
                from decimal import Decimal as _smoke_decimal
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Creation_contrat as _smoke_contract
                from Utils import UTILS_Contrats_schema as _smoke_contract_schema

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_contract_schema.EnsureContractEngineColumns(_smoke_db)
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 3")
                _smoke_people = [int(row[0]) for row in _smoke_db.ResultatReq()]
                if len(_smoke_people) < 3:
                    raise RuntimeError("au moins trois salariés sont nécessaires au smoke PMSL 21 h")
                _smoke_db.ExecuterReq(
                    "SELECT IDtype FROM contrats_types "
                    "WHERE UPPER(COALESCE(nom_abrege, ''))='CDD' ORDER BY IDtype LIMIT 1"
                )
                _smoke_cdd_rows = _smoke_db.ResultatReq()
                if not _smoke_cdd_rows:
                    raise RuntimeError("type CDD introuvable dans la base de smoke")
                _smoke_cdd_type_id = int(_smoke_cdd_rows[0][0])

                # Contrat antérieur du troisième salarié pour tester la continuité CDD -> CDI.
                _smoke_previous_contract_id = _smoke_db.ReqInsert(
                    "contrats",
                    [
                        ("IDpersonne", _smoke_people[2]),
                        ("IDtype", _smoke_cdd_type_id),
                        ("date_debut", "2026-01-01"),
                        ("date_fin", "2026-08-31"),
                        ("date_rupture", ""),
                        ("essai", 0),
                        ("convention_code", "CCNS"),
                        ("ccns_group", "G1"),
                        ("weekly_hours", 21.0),
                        ("operation_type", "NEW"),
                        ("previous_contract_id", None),
                        ("signature", ""),
                        ("due", ""),
                    ],
                )
                _smoke_db.Commit()
                _smoke_db.Close()

                def _smoke_open_dialog(person_id):
                    dialog = _smoke_contract.Dialog(frame, IDcontrat=0, IDpersonne=person_id)
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

                def _smoke_prepare_ccns_21h(page, start_date, end_date=None):
                    page.SetDatePicker(page.datepicker_date_debut, start_date)
                    if end_date is not None:
                        page.SetDatePicker(page.datepicker_date_fin, end_date)
                    page.OnContractDateChanged(None)
                    page._SelectConvention("CCNS")
                    page.OnChoiceConvention(None)
                    page.RefreshCCNSGroups(preserve="G1")
                    page.SelectChoice(page.choice_ccns_group, "G1")
                    assert page.GetChoiceData(page.choice_ccns_group) == "G1"
                    page.weekly_hours.SetValue(21.0)
                    page.RefreshCCNSPreview()
                    page.RefreshTrialProposal(force=True)
                    assert _smoke_decimal(str(page.weekly_hours.GetValue())) == _smoke_decimal("21.0")
                    assert page._MonthlySalaryDecimal() is not None
                    assert page._MonthlySalaryDecimal() > 0
                    assert page.last_ccns_preview is not None
                    assert page.last_ccns_preview.compliant

                def _smoke_finish_and_read(dialog, person_id):
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
                        "SELECT c.IDcontrat, t.nom_abrege, c.convention_code, c.ccns_group, "
                        "c.weekly_hours, c.gross_monthly_salary, c.operation_type, "
                        "c.previous_contract_id, c.trial_period_value, c.date_debut, c.date_fin "
                        "FROM contrats c LEFT JOIN contrats_types t ON t.IDtype=c.IDtype "
                        "WHERE c.IDpersonne=%d AND c.IDcontrat>%d ORDER BY c.IDcontrat DESC LIMIT 1"
                        % (person_id, baseline)
                    )
                    rows = probe.ResultatReq()
                    probe.Close()
                    assert len(rows) == 1
                    row = rows[0]
                    _smoke_created_contract_ids.append(int(row[0]))
                    dialog.Destroy()
                    wx.Yield()
                    return row

                def _smoke_new_cdd(person_id, start_date, end_date):
                    dialog = _smoke_open_dialog(person_id)
                    page = dialog.page3
                    page.SelectChoice(page.choice_operation, "NEW")
                    page.OnOperationChanged(None)
                    assert page._SelectContractTypeCode("CDD")
                    page.OnChoiceType(None)
                    _smoke_prepare_ccns_21h(page, start_date, end_date)
                    row = _smoke_finish_and_read(dialog, person_id)
                    assert (row[1] or "").upper() == "CDD"
                    assert row[2] == "CCNS"
                    assert row[3] == "G1"
                    assert _smoke_decimal(str(row[4])) == _smoke_decimal("21.0")
                    assert _smoke_decimal(str(row[5])) > 0
                    assert row[6] == "NEW"
                    assert row[7] is None
                    assert row[9] == start_date
                    assert row[10] == end_date
                    return row

                print("TEAMWORKS_SMOKE_PMSL_21H_STAGE:cdd-1", flush=True)
                _smoke_cdd_1 = _smoke_new_cdd(_smoke_people[0], "2026-09-01", "2027-08-31")

                print("TEAMWORKS_SMOKE_PMSL_21H_STAGE:cdd-2", flush=True)
                _smoke_cdd_2 = _smoke_new_cdd(_smoke_people[1], "2026-09-01", "2027-08-31")
                assert _smoke_cdd_1[0] != _smoke_cdd_2[0]

                print("TEAMWORKS_SMOKE_PMSL_21H_STAGE:cdd-to-cdi", flush=True)
                _smoke_cdi = _smoke_open_dialog(_smoke_people[2])
                _smoke_cdi_page = _smoke_cdi.page3
                _smoke_cdi_page.SelectChoice(_smoke_cdi_page.choice_operation, "CDD_TO_CDI")
                _smoke_cdi_page.OnOperationChanged(None)
                _smoke_cdi_page.SelectChoice(
                    _smoke_cdi_page.choice_previous_contract,
                    _smoke_previous_contract_id,
                )
                assert _smoke_cdi_page.GetChoiceData(_smoke_cdi_page.choice_previous_contract) == _smoke_previous_contract_id
                _smoke_prepare_ccns_21h(_smoke_cdi_page, "2026-09-01")
                assert _smoke_cdi_page._CurrentContractType().value == "CDI"
                assert not _smoke_cdi_page.check_trial.GetValue()
                assert _smoke_cdi_page.trial_value.GetValue() == 0
                _smoke_cdi_row = _smoke_finish_and_read(_smoke_cdi, _smoke_people[2])
                assert (_smoke_cdi_row[1] or "").upper() == "CDI"
                assert _smoke_cdi_row[2] == "CCNS"
                assert _smoke_cdi_row[3] == "G1"
                assert _smoke_decimal(str(_smoke_cdi_row[4])) == _smoke_decimal("21.0")
                assert _smoke_decimal(str(_smoke_cdi_row[5])) > 0
                assert _smoke_cdi_row[6] == "CDD_TO_CDI"
                assert int(_smoke_cdi_row[7]) == _smoke_previous_contract_id
                assert int(_smoke_cdi_row[8] or 0) == 0
                assert _smoke_cdi_row[9] == "2026-09-01"
                assert _smoke_cdi_row[10] == "2999-01-01"

                print("TEAMWORKS_SMOKE_PMSL_CONTRACTS_21H_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_PMSL_CONTRACTS_21H_FAILED", flush=True)
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
        raise RuntimeError("injection des marqueurs PMSL 21 h absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_pmsl_contracts_21h_smoke as CORE"
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
            github_error_summary("PMSL contracts 21h StaticBox parentage failed", output)
            return 4
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("PMSL contracts 21h smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("PMSL contracts 21h smoke failed", output)
            print("marqueur PMSL contrats 21 h absent", file=sys.stderr)
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
        github_error_summary("PMSL contracts 21h smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
