#!/usr/bin/env python3
"""Construit les contrôles à cases secondaires dans le contexte Teamworks réel."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
SOURCE = TEAMWORKS_DIR / "Teamworks.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_secondary_checklists_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "checklist-controls-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_CHECKLIST_CONTROLS_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_CHECKLIST_CONTROLS_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:imports", flush=True)
                import GestionDB as _smoke_gestiondb
                from Dlg import DLG_Config_gadgets as _cfg_gadgets
                from Dlg import DLG_Config_liste_personnes as _cfg_people
                from Dlg import DLG_Selection_liste as _selection
                from Dlg import DLG_Publiposteur_Choix as _publipost
                from Dlg import DLG_Impression_frais as _frais
                from Dlg import DLG_Saisie_remboursement as _remboursement
                from Dlg import DLG_Statistiques as _stats
                from Dlg import DLG_Application_modele as _modeles
                from Ctrl import CTRL_Creation_modele_contrat_p1 as _modele_contrat

                _smoke_db = _smoke_gestiondb.DB()
                _smoke_db.ExecuterReq("SELECT IDpersonne FROM personnes ORDER BY IDpersonne LIMIT 1")
                _smoke_people = _smoke_db.ResultatReq()
                _smoke_db.Close()
                if not _smoke_people:
                    raise RuntimeError("aucune personne disponible pour les contrôles secondaires")
                _smoke_person_id = _smoke_people[0][0]

                _host = wx.Frame(frame, title="Smoke contrôles secondaires")
                _host.label_rattachement = wx.StaticText(_host, -1, "")
                _controls = []
                _dialogs = []

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:gadgets", flush=True)
                _controls.append(_cfg_gadgets.ListCtrl(_host))

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:config-personnes", flush=True)
                _cfg_people_columns = [
                    ["Nom", "left", 140, "nom", "", "Nom de la personne", True, 1],
                    ["Prénom", "left", 120, "prenom", "", "Prénom de la personne", True, 2],
                ]
                _cfg_people_dialog = _cfg_people.Dialog(_host, listeColonnes=_cfg_people_columns)
                _dialogs.append(_cfg_people_dialog)
                _controls.append(_cfg_people_dialog.panel_contenu.listCtrl)

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:selection", flush=True)
                _selection_ctrl = _selection.ListCtrl(
                    _host,
                    [
                        ("ID", "left", 50, "id"),
                        ("Libellé", "left", 160, "label"),
                    ],
                    [(1, "Alpha"), (2, "Bêta")],
                )
                _controls.append(_selection_ctrl)

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:publipostage", flush=True)
                _publipost_ctrl = _publipost.CheckListCtrl(
                    _host,
                    ([('ID', 50), ('Nom', 160)], [(1, 'Alice'), (2, 'Bob')]),
                )
                _controls.append(_publipost_ctrl)

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:frais", flush=True)
                _controls.append(_frais.ListCtrl(_host, IDpersonne=_smoke_person_id))

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:remboursement", flush=True)
                _controls.append(
                    _remboursement.ListCtrl_deplacements(
                        _host,
                        IDremboursement=None,
                        IDpersonne=_smoke_person_id,
                    )
                )

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:statistiques", flush=True)
                _controls.append(_stats.listCtrl_Personnes(_host, listePersonnes=[]))

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:modeles", flush=True)
                _controls.append(_modeles.listCtrl_Modeles(_host))

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:modele-contrat", flush=True)
                # ListCtrl_champs lit dictChamps via
                # self.GetGrandParent().GetParent().
                _modele_context = wx.Panel(_host, -1)
                _modele_context.dictChamps = {}
                _modele_page = wx.Panel(_modele_context, -1)
                _controls.append(_modele_contrat.ListCtrl_champs(_modele_page))

                print("TEAMWORKS_SMOKE_CHECKLIST_STAGE:assertions", flush=True)
                for _control in _controls:
                    assert _control.GetColumnCount() >= 1
                    assert hasattr(_control, "EnableCheckBoxes")
                    assert hasattr(_control, "IsItemChecked")

                assert _cfg_people_dialog.panel_contenu.listCtrl.GetItemCount() == 2
                assert _selection_ctrl.GetItemCount() == 2
                assert _selection_ctrl.IsItemChecked(0)
                assert _selection_ctrl.IsItemChecked(1)

                assert _publipost_ctrl.GetItemCount() == 2
                _publipost_ctrl.CheckItem(0, True)
                assert _publipost_ctrl.IsItemChecked(0)

                print("TEAMWORKS_SMOKE_CHECKLIST_CONTROLS_READY", flush=True)
                for _control in reversed(_controls):
                    if not any(_control is _dialog.panel_contenu.listCtrl for _dialog in _dialogs):
                        _control.Destroy()
                for _dialog in reversed(_dialogs):
                    _dialog.Destroy()
                _host.Destroy()
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_CHECKLIST_CONTROLS_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    marker_count = source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched = source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched or FAILURE_MARKER not in patched:
        raise RuntimeError("marqueurs secondaires absents après injection")
    compile(patched, str(PATCHED), "exec")
    PATCHED.write_text(patched, encoding="utf-8")
    return marker_count


def decode_output(data: bytes) -> str:
    for encoding in ("utf-8",):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def write_diagnostic(*, return_code: int, marker_count: int | None, output: str) -> None:
    REPORT.write_text(
        f"return_code={return_code}\n"
        f"entrypoint_marker_count={marker_count}\n"
        f"ready_marker={READY_MARKER in output}\n"
        f"failure_marker={FAILURE_MARKER in output}\n"
        "--- output ---\n"
        f"{output}",
        encoding="utf-8",
    )


def build_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["TEAMWORKS_SMOKE_MODE"] = "main-window"
    paths = [str(ROOT), str(TEAMWORKS_DIR)]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    marker_count: int | None = None
    try:
        marker_count = build_patched_entrypoint()
        result = subprocess.run(
            [sys.executable, str(PATCHED)],
            cwd=TEAMWORKS_DIR,
            env=build_environment(),
            capture_output=True,
            timeout=180,
            check=False,
        )
        output = decode_output(result.stdout) + "\n" + decode_output(result.stderr)
        write_diagnostic(return_code=result.returncode, marker_count=marker_count, output=output)
        print(output)
        if result.returncode != 0 or FAILURE_MARKER in output:
            return result.returncode or 1
        if READY_MARKER not in output:
            return 2
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(return_code=3, marker_count=marker_count, output=output)
        print(output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
