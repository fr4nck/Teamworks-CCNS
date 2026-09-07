#!/usr/bin/env python3
"""Smoke Windows du clavier wx dans le bootstrap Teamworks réel."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_keyboard_accessibility_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_keyboard_accessibility_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "keyboard-accessibility-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_WX_KEYBOARD_ACCESSIBILITY_READY"
FAILURE_MARKER = "TEAMWORKS_WX_KEYBOARD_ACCESSIBILITY_FAILED"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            try:
                print("TEAMWORKS_KEYBOARD_STAGE:imports", flush=True)
                from Ctrl import CTRL_Bouton_image as _smoke_buttons
                from Dlg import DLG_Filtre_texte as _smoke_filter

                def _pump(milliseconds=120):
                    loops = max(1, int(milliseconds / 10))
                    for _ in range(loops):
                        wx.YieldIfNeeded()
                        wx.MilliSleep(10)

                def _focus_is(control):
                    _pump(60)
                    focused = wx.Window.FindFocus()
                    assert focused is control, "focus inattendu: %r au lieu de %r" % (focused, control)
                    assert control.IsEnabled()
                    assert control.IsShownOnScreen()

                def _press(simulator, keycode, shift=False):
                    if shift:
                        simulator.KeyDown(wx.WXK_SHIFT)
                    simulator.Char(keycode)
                    if shift:
                        simulator.KeyUp(wx.WXK_SHIFT)
                    _pump()

                class _KeyboardDialog(wx.Dialog):
                    def __init__(self, parent):
                        wx.Dialog.__init__(self, parent, title="Smoke clavier Teamworks")
                        self.primary_count = 0
                        self.text = wx.TextCtrl(self, value="test")
                        self.primary = _smoke_buttons.CTRL(self, id=wx.ID_OK, texte="Valider", role="primary")
                        self.toggle = _smoke_buttons.Toggle(self, texte="Basculer")
                        self.checkbox = wx.CheckBox(self, label="Option")
                        self.cancel = _smoke_buttons.CTRL(self, id=wx.ID_CANCEL, texte="Annuler", role="quiet")
                        self.primary.SetDefault()
                        self.primary.Bind(wx.EVT_BUTTON, self._on_primary)
                        sizer = wx.BoxSizer(wx.VERTICAL)
                        for control in (self.text, self.primary, self.toggle, self.checkbox, self.cancel):
                            sizer.Add(control, 0, wx.ALL | wx.EXPAND, 8)
                        self.SetSizerAndFit(sizer)

                    def _on_primary(self, event):
                        self.primary_count += 1

                simulator = wx.UIActionSimulator()

                print("TEAMWORKS_KEYBOARD_STAGE:common-components", flush=True)
                dialog = _KeyboardDialog(frame)
                dialog.Show()
                dialog.Raise()
                _pump()
                dialog.text.SetFocus()
                _focus_is(dialog.text)
                _press(simulator, wx.WXK_TAB)
                _focus_is(dialog.primary)
                _press(simulator, wx.WXK_TAB, shift=True)
                _focus_is(dialog.text)

                dialog.toggle.SetFocus()
                _focus_is(dialog.toggle)
                assert not dialog.toggle.GetValue()
                _press(simulator, wx.WXK_SPACE)
                assert dialog.toggle.GetValue()

                dialog.checkbox.SetFocus()
                _focus_is(dialog.checkbox)
                assert not dialog.checkbox.GetValue()
                _press(simulator, wx.WXK_SPACE)
                assert dialog.checkbox.GetValue()

                dialog.text.SetFocus()
                before = dialog.primary_count
                _press(simulator, wx.WXK_RETURN)
                assert dialog.primary_count == before + 1

                expected = {dialog.text, dialog.primary, dialog.toggle, dialog.checkbox, dialog.cancel}
                dialog.text.SetFocus()
                seen = {dialog.text}
                for _ in range(8):
                    _press(simulator, wx.WXK_TAB)
                    focused = wx.Window.FindFocus()
                    if focused is not None:
                        seen.add(focused)
                assert expected.issubset(seen), "Tab incomplet sur composants communs"

                dialog.cancel.SetFocus()
                seen = {dialog.cancel}
                for _ in range(8):
                    _press(simulator, wx.WXK_TAB, shift=True)
                    focused = wx.Window.FindFocus()
                    if focused is not None:
                        seen.add(focused)
                assert expected.issubset(seen), "Shift+Tab incomplet sur composants communs"
                dialog.Destroy()
                _pump()

                print("TEAMWORKS_KEYBOARD_STAGE:escape", flush=True)
                escape_dialog = wx.Dialog(frame, title="Smoke Escape")
                escape_cancel = _smoke_buttons.CTRL(escape_dialog, id=wx.ID_CANCEL, texte="Annuler")
                escape_sizer = wx.BoxSizer(wx.VERTICAL)
                escape_sizer.Add(escape_cancel, 0, wx.ALL, 12)
                escape_dialog.SetSizerAndFit(escape_sizer)

                def _send_escape():
                    escape_dialog.Raise()
                    escape_cancel.SetFocus()
                    _pump(40)
                    simulator.Char(wx.WXK_ESCAPE)

                def _escape_timeout():
                    if escape_dialog.IsModal():
                        escape_dialog.EndModal(wx.ID_ABORT)

                wx.CallLater(120, _send_escape)
                wx.CallLater(1800, _escape_timeout)
                result = escape_dialog.ShowModal()
                escape_dialog.Destroy()
                assert result == wx.ID_CANCEL, "Escape ne ferme pas avec wx.ID_CANCEL"

                print("TEAMWORKS_KEYBOARD_STAGE:filter-state", flush=True)
                filter_dialog = _smoke_filter.MyDialog(
                    frame,
                    nom_filtre="le nom",
                    titre_frame="Filtre du nom",
                    texte=None,
                )
                filter_dialog.Show()
                filter_dialog.Raise()
                _pump()
                _focus_is(filter_dialog.radio1)
                assert not filter_dialog.ctrl_texte.IsEnabled()

                filter_dialog.radio2.SetFocus()
                _press(simulator, wx.WXK_SPACE)
                assert filter_dialog.radio2.GetValue()
                assert filter_dialog.ctrl_texte.IsEnabled()
                _press(simulator, wx.WXK_TAB)
                _focus_is(filter_dialog.ctrl_texte)
                _press(simulator, wx.WXK_TAB, shift=True)
                _focus_is(filter_dialog.radio2)

                filter_dialog.radio1.SetFocus()
                _press(simulator, wx.WXK_SPACE)
                assert filter_dialog.radio1.GetValue()
                assert not filter_dialog.ctrl_texte.IsEnabled()
                _press(simulator, wx.WXK_TAB)
                assert wx.Window.FindFocus() is not filter_dialog.ctrl_texte
                filter_dialog.Destroy()
                _pump()

                print("TEAMWORKS_WX_KEYBOARD_ACCESSIBILITY_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_WX_KEYBOARD_ACCESSIBILITY_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched_core = core_source.replace(MARKER_LINE, INJECTION, 1)
    compile(patched_core, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_keyboard_accessibility_smoke as CORE"
    if entrypoint_source.count(import_line) != 1:
        raise RuntimeError("import du cœur Teamworks introuvable ou ambigu")
    patched_entrypoint = entrypoint_source.replace(import_line, patched_import, 1)
    compile(patched_entrypoint, str(PATCHED), "exec")
    PATCHED.write_text(patched_entrypoint, encoding="utf-8")
    return marker_count


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    marker_count = None
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
            github_error_summary("wx keyboard accessibility smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("wx keyboard accessibility smoke failed", output)
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
        github_error_summary("wx keyboard accessibility smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
