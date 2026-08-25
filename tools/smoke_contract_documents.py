#!/usr/bin/env python3
"""Qualifie le publipostage des contrats dans l'application Windows réelle."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_contract_documents_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_contract_documents_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "contract-documents-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_CONTRACT_DOCUMENTS_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_CONTRACT_DOCUMENTS_FAILED"
STATICBOX_PARENT_WARNING = "of wxStaticBoxSizer should be created as child of its wxStaticBox"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_contract_id = None
            _smoke_model_paths = []
            _smoke_model_names = []
            _smoke_gestiondb = None
            _smoke_models = None
            try:
                print("TEAMWORKS_SMOKE_CONTRACT_DOC_STAGE:imports", flush=True)
                from pathlib import Path as _smoke_Path
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Liste_contrats as _smoke_registry
                from Dlg import DLG_Publiposteur_contrat as _smoke_pub
                from Utils import UTILS_Contrats_modeles_documents as _smoke_models
                from Utils import UTILS_Contrats_schema as _smoke_schema
                from Utils import UTILS_Fichiers as _smoke_files
                from Utils import UTILS_Publipostage_donnees as _smoke_mail_data

                print("TEAMWORKS_SMOKE_CONTRACT_DOC_STAGE:fixture", flush=True)
                _smoke_db = _smoke_gestiondb.DB()
                _smoke_schema.EnsureContractEngineColumns(_smoke_db)
                _smoke_models.EnsureTable(_smoke_db)
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_person_rows = _smoke_db.ResultatReq()
                if not _smoke_person_rows:
                    raise RuntimeError("aucun salarié disponible pour le smoke documents contrat")
                _smoke_person_id = int(_smoke_person_rows[0][0])
                _smoke_db.ExecuterReq(
                    "SELECT IDtype FROM contrats_types WHERE UPPER(COALESCE(nom_abrege, ''))='CDI' "
                    "ORDER BY IDtype LIMIT 1"
                )
                _smoke_type_rows = _smoke_db.ResultatReq()
                if not _smoke_type_rows:
                    raise RuntimeError("type CDI introuvable dans la base de smoke")
                _smoke_cdi_type_id = int(_smoke_type_rows[0][0])
                _smoke_contract_id = _smoke_db.ReqInsert(
                    "contrats",
                    [
                        ("IDpersonne", _smoke_person_id),
                        ("IDclassification", None),
                        ("IDtype", _smoke_cdi_type_id),
                        ("valeur_point", None),
                        ("date_debut", "2026-09-01"),
                        ("date_fin", "2999-01-01"),
                        ("essai", 0),
                        ("convention_code", "CCNS"),
                        ("ccns_group", "G1"),
                        ("weekly_hours", 35.0),
                        ("gross_monthly_salary", 2000.0),
                        ("trial_period_value", 30),
                        ("trial_period_unit", "DAY"),
                        ("operation_type", "NEW"),
                    ],
                )
                _smoke_db.Commit()
                _smoke_db.Close()

                print("TEAMWORKS_SMOKE_CONTRACT_DOC_STAGE:mail-data", flush=True)
                _smoke_data = _smoke_mail_data.GetDictDonnees(
                    categorie="contrat",
                    listeID=[_smoke_contract_id],
                )
                assert _smoke_data["CATEGORIE"] == "contrat"
                assert _smoke_data["NBREDOCUMENTS"] == 1
                assert _smoke_data[1]["CONVENTION"] == "CCNS"
                assert _smoke_data[1]["GROUPECCNS"] == "G1"
                assert _smoke_data[1]["DUREEHEBDO"] == "35 h"
                assert _smoke_data[1]["SALAIREBRUTMENSUEL"] == "2000.00 €"
                assert _smoke_data[1]["CONFORMITEREMUNERATION"] == "Conforme"

                print("TEAMWORKS_SMOKE_CONTRACT_DOC_STAGE:model-filter", flush=True)
                _smoke_models_dir = _smoke_Path(_smoke_files.GetRepModeles())
                _smoke_models_dir.mkdir(parents=True, exist_ok=True)
                _smoke_model_specs = [
                    ("__uat_contract_legacy.twd", None, None),
                    ("__uat_contract_g1.twd", "CCNS", "G1"),
                    ("__uat_contract_g2.twd", "CCNS", "G2"),
                ]
                _smoke_db = _smoke_gestiondb.DB()
                for _smoke_name, _smoke_convention, _smoke_group in _smoke_model_specs:
                    _smoke_path = _smoke_models_dir / _smoke_name
                    _smoke_path.write_text("Modèle UAT {NOM} {PRENOM} {GROUPECCNS}", encoding="utf-8")
                    _smoke_model_paths.append(_smoke_path)
                    _smoke_model_names.append(_smoke_name)
                    if _smoke_convention:
                        _smoke_models.SaveMetadata(
                            _smoke_db,
                            _smoke_name,
                            convention_code=_smoke_convention,
                            ccns_group=_smoke_group,
                        )
                _smoke_db.Commit()
                _smoke_db.Close()

                _smoke_pub_dialog = _smoke_pub.Dialog(frame, "", dictDonnees=_smoke_data)
                _smoke_pub_dialog.Show()
                wx.Yield()
                _smoke_pub_dialog.page4.choixLogiciel = 3
                _smoke_visible = _smoke_pub_dialog.page4.listCtrl.GetListeDocuments()
                _smoke_visible_names = {values[0] for values in _smoke_visible.values()}
                assert "__uat_contract_legacy.twd" in _smoke_visible_names
                assert "__uat_contract_g1.twd" in _smoke_visible_names
                assert "__uat_contract_g2.twd" not in _smoke_visible_names
                _smoke_pub_dialog.Destroy()
                wx.Yield()

                print("TEAMWORKS_SMOKE_CONTRACT_DOC_STAGE:registry", flush=True)
                _smoke_registry_dialog = _smoke_registry.Dialog(frame)
                _smoke_registry_dialog.Show()
                wx.Yield()
                _smoke_track = next(
                    item for item in _smoke_registry_dialog.ctrl_listview.donnees
                    if int(item.IDcontrat) == int(_smoke_contract_id)
                )
                _smoke_registry_dialog.ctrl_listview.SelectObject(
                    _smoke_track,
                    deselectOthers=True,
                    ensureVisible=True,
                )
                wx.Yield()
                assert _smoke_registry_dialog.GetSelectedContractID(show_message=False) == _smoke_contract_id
                _smoke_registry_data = _smoke_registry_dialog.BuildPublipostageData(_smoke_contract_id)
                assert _smoke_registry_data[1]["GROUPECCNS"] == "G1"

                _smoke_original_pub_modal = _smoke_pub.Dialog.ShowModal
                _smoke_pub.Dialog.ShowModal = lambda self: wx.ID_CANCEL
                try:
                    assert _smoke_registry_dialog.OnBoutonPublipostage(None)
                finally:
                    _smoke_pub.Dialog.ShowModal = _smoke_original_pub_modal
                _smoke_registry_dialog.Destroy()
                wx.Yield()

                print("TEAMWORKS_SMOKE_CONTRACT_DOCUMENTS_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_CONTRACT_DOCUMENTS_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                try:
                    if _smoke_gestiondb is not None:
                        _smoke_cleanup = _smoke_gestiondb.DB()
                        if _smoke_models is not None:
                            for _smoke_name in _smoke_model_names:
                                _smoke_models.DeleteMetadata(_smoke_cleanup, _smoke_name)
                        if _smoke_contract_id is not None:
                            _smoke_cleanup.ReqDEL("contrats_valchamps", "IDcontrat", _smoke_contract_id)
                            _smoke_cleanup.ReqDEL("contrats", "IDcontrat", _smoke_contract_id)
                        _smoke_cleanup.Commit()
                        _smoke_cleanup.Close()
                    for _smoke_path in _smoke_model_paths:
                        _smoke_path.unlink(missing_ok=True)
                except Exception:
                    import traceback as _smoke_cleanup_traceback
                    _smoke_cleanup_traceback.print_exc()
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs documents contrat absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_contract_documents_smoke as CORE"
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
            github_error_summary("Contract documents StaticBox parentage failed", output)
            return 4
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("Contract documents smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Contract documents smoke failed", output)
            print("marqueur documents contrat absent", file=sys.stderr)
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
        github_error_summary("Contract documents smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
