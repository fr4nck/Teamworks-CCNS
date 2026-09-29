#!/usr/bin/env python3
"""Reproduit en processus frais les crashes MSW autour de wx.SearchCtrl.

Le smoke injecte un scénario minimal juste après l'ouverture de la base Exemple.
Il sert uniquement au diagnostic Windows : aucun code de production n'est patché.
"""

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
PATCHED = TEAMWORKS_DIR / "Teamworks_searchctrl_lifecycle_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_searchctrl_lifecycle_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "searchctrl-lifecycle-smoke"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_SEARCHCTRL_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_SEARCHCTRL_FAILED"
SCENARIOS = ("backup-search", "backup-email")


def build_injection(scenario: str, cycles: int) -> str:
    return f'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                import wx as _smoke_wx
                from Dlg import DLG_Config_sauvegarde as _smoke_backup
                from Dlg import DLG_Emails_exp as _smoke_email
                _smoke_scenario = {scenario!r}
                _smoke_cycles = {cycles}

                def _smoke_show_destroy(_smoke_window):
                    _smoke_window.Show()
                    _smoke_window.Layout()
                    _smoke_wx.Yield()
                    _smoke_window.Destroy()
                    _smoke_wx.Yield()

                for _smoke_cycle in range(_smoke_cycles):
                    print(
                        "TEAMWORKS_SMOKE_SEARCHCTRL_CYCLE:%s:%d/%d"
                        % (_smoke_scenario, _smoke_cycle + 1, _smoke_cycles),
                        flush=True,
                    )
                    _smoke_backup_dialog = _smoke_backup.MyFrame(frame)
                    _smoke_show_destroy(_smoke_backup_dialog)

                    if _smoke_scenario == "backup-search":
                        _smoke_probe = _smoke_wx.Dialog(frame, title="SearchCtrl lifecycle probe")
                        _smoke_search = _smoke_wx.SearchCtrl(
                            _smoke_probe,
                            style=_smoke_wx.TE_PROCESS_ENTER,
                        )
                        _smoke_sizer = _smoke_wx.BoxSizer(_smoke_wx.VERTICAL)
                        _smoke_sizer.Add(_smoke_search, 1, _smoke_wx.EXPAND | _smoke_wx.ALL, 8)
                        _smoke_probe.SetSizerAndFit(_smoke_sizer)
                        _smoke_show_destroy(_smoke_probe)
                    elif _smoke_scenario == "backup-email":
                        _smoke_email_dialog = _smoke_email.Dialog(frame)
                        _smoke_show_destroy(_smoke_email_dialog)
                    else:
                        raise RuntimeError("scénario SearchCtrl inconnu: %s" % _smoke_scenario)

                print("TEAMWORKS_SMOKE_SEARCHCTRL_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_SEARCHCTRL_FAILED", flush=True)
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
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs SearchCtrl absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_searchctrl_lifecycle_smoke as CORE"
    if import_line not in entrypoint_source:
        raise RuntimeError("import du cœur Teamworks introuvable dans la coque active")
    patched_entrypoint = entrypoint_source.replace(import_line, patched_import, 1)
    compile(patched_entrypoint, str(PATCHED), "exec")
    PATCHED.write_text(patched_entrypoint, encoding="utf-8")
    return marker_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    parser.add_argument("--cycles", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cycles < 1 or args.cycles > 100:
        raise SystemExit("--cycles doit être compris entre 1 et 100")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / f"diagnostic-{args.scenario}.txt"
    marker_count: int | None = None
    try:
        marker_count = build_patched_entrypoint(args.scenario, args.cycles)
        return_code, output = run_entrypoint(
            PATCHED,
            root=ROOT,
            teamworks_dir=TEAMWORKS_DIR,
            timeout=max(180, args.cycles * 15),
        )
        write_diagnostic(
            report,
            return_code=return_code,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary(
                f"SearchCtrl lifecycle smoke failed ({args.scenario})",
                output,
            )
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary(
                f"SearchCtrl lifecycle smoke failed ({args.scenario})",
                output,
            )
            print("marqueur SearchCtrl absent", file=sys.stderr)
            return 2
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
            f"SearchCtrl lifecycle smoke failed ({args.scenario})",
            output,
        )
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
