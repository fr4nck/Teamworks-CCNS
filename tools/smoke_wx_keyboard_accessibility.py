#!/usr/bin/env python3
"""Smoke Windows du clavier wx et des changements d'état UX.

Ce smoke doit être exécuté sur un vrai runner Windows avec wxPython. Il vérifie
les comportements que l'analyse statique ne peut pas prouver : focus effectif,
Tab/Shift+Tab, activation Enter/Espace, Escape et maintien d'un focus valide
après changement d'état.
"""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
REPORT_DIR = ROOT / "artifacts" / "keyboard-accessibility-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"

if str(TEAMWORKS_DIR) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS_DIR))

import wx

from Ctrl import CTRL_Bouton_image
from Dlg import DLG_Filtre_texte


class KeyboardContractDialog(wx.Dialog):
    """Petit hôte réel pour qualifier les composants communs Teamworks."""

    def __init__(self, parent):
        super().__init__(parent, title="Smoke clavier Teamworks")
        self.primary_count = 0
        self.cancel_count = 0

        self.text = wx.TextCtrl(self, value="test")
        self.primary = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_OK,
            texte="Valider",
            role="primary",
        )
        self.toggle = CTRL_Bouton_image.Toggle(self, texte="Basculer")
        self.checkbox = wx.CheckBox(self, label="Option")
        self.cancel = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte="Annuler",
            role="quiet",
        )
        self.primary.SetDefault()

        self.primary.Bind(wx.EVT_BUTTON, self._on_primary)
        self.cancel.Bind(wx.EVT_BUTTON, self._on_cancel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        for control in (
            self.text,
            self.primary,
            self.toggle,
            self.checkbox,
            self.cancel,
        ):
            sizer.Add(control, 0, wx.ALL | wx.EXPAND, 8)
        self.SetSizerAndFit(sizer)

    def _on_primary(self, event):
        self.primary_count += 1

    def _on_cancel(self, event):
        self.cancel_count += 1
        event.Skip()


def _pump(milliseconds=120):
    loops = max(1, int(milliseconds / 10))
    for _ in range(loops):
        wx.YieldIfNeeded()
        wx.MilliSleep(10)


def _focus_is(control):
    _pump(60)
    focused = wx.Window.FindFocus()
    assert focused is control, (
        "focus inattendu: attendu=%s obtenu=%s"
        % (control.GetName() or control.__class__.__name__, getattr(focused, "GetName", lambda: "aucun")())
    )
    assert control.IsEnabled()
    assert control.IsShownOnScreen()


def _press(simulator, keycode, shift=False):
    if shift:
        simulator.KeyDown(wx.WXK_SHIFT)
    simulator.Char(keycode)
    if shift:
        simulator.KeyUp(wx.WXK_SHIFT)
    _pump()


def _test_common_components(frame, simulator):
    print("TEAMWORKS_KEYBOARD_STAGE:common-components", flush=True)
    dialog = KeyboardContractDialog(frame)
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
    assert dialog.toggle.GetValue(), "Espace n'active pas CTRL_Bouton_image.Toggle"

    dialog.checkbox.SetFocus()
    _focus_is(dialog.checkbox)
    assert not dialog.checkbox.GetValue()
    _press(simulator, wx.WXK_SPACE)
    assert dialog.checkbox.GetValue(), "Espace n'active pas wx.CheckBox"

    dialog.text.SetFocus()
    _focus_is(dialog.text)
    before = dialog.primary_count
    _press(simulator, wx.WXK_RETURN)
    assert dialog.primary_count == before + 1, "Enter n'active pas l'action par défaut"

    expected = {dialog.text, dialog.primary, dialog.toggle, dialog.checkbox, dialog.cancel}
    dialog.text.SetFocus()
    seen_forward = {dialog.text}
    for _ in range(8):
        _press(simulator, wx.WXK_TAB)
        focused = wx.Window.FindFocus()
        if focused is not None:
            seen_forward.add(focused)
    assert expected.issubset(seen_forward), "Tab ne parcourt pas tous les contrôles communs"

    dialog.cancel.SetFocus()
    seen_backward = {dialog.cancel}
    for _ in range(8):
        _press(simulator, wx.WXK_TAB, shift=True)
        focused = wx.Window.FindFocus()
        if focused is not None:
            seen_backward.add(focused)
    assert expected.issubset(seen_backward), "Shift+Tab ne parcourt pas tous les contrôles communs"

    dialog.Destroy()
    _pump()


def _test_escape(frame, simulator):
    print("TEAMWORKS_KEYBOARD_STAGE:escape", flush=True)
    dialog = wx.Dialog(frame, title="Smoke Escape")
    cancel = CTRL_Bouton_image.CTRL(dialog, id=wx.ID_CANCEL, texte="Annuler")
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(cancel, 0, wx.ALL, 12)
    dialog.SetSizerAndFit(sizer)

    def send_escape():
        dialog.Raise()
        cancel.SetFocus()
        _pump(40)
        simulator.Char(wx.WXK_ESCAPE)

    def force_timeout():
        if dialog.IsModal():
            dialog.EndModal(wx.ID_ABORT)

    wx.CallLater(120, send_escape)
    wx.CallLater(1800, force_timeout)
    result = dialog.ShowModal()
    dialog.Destroy()
    assert result == wx.ID_CANCEL, "Escape ne ferme pas le dialogue avec wx.ID_CANCEL"


def _test_filter_state_and_navigation(frame, simulator):
    print("TEAMWORKS_KEYBOARD_STAGE:filter-dialog", flush=True)
    dialog = DLG_Filtre_texte.MyDialog(
        frame,
        nom_filtre="le nom",
        titre_frame="Filtre du nom",
        texte=None,
    )
    dialog.Show()
    dialog.Raise()
    _pump()

    _focus_is(dialog.radio1)
    assert not dialog.ctrl_texte.IsEnabled()

    # Le parcours avant doit atteindre les deux actions sans se perdre.
    seen = {wx.Window.FindFocus()}
    for _ in range(8):
        _press(simulator, wx.WXK_TAB)
        focused = wx.Window.FindFocus()
        if focused is not None:
            seen.add(focused)
    assert dialog.bouton_ok in seen, "Tab n'atteint pas l'action Appliquer"
    assert dialog.bouton_annuler in seen, "Tab n'atteint pas l'action Annuler"

    # Changement d'état réel au clavier : radio2 active le champ texte.
    dialog.radio2.SetFocus()
    _focus_is(dialog.radio2)
    _press(simulator, wx.WXK_SPACE)
    assert dialog.radio2.GetValue()
    assert dialog.ctrl_texte.IsEnabled()
    _press(simulator, wx.WXK_TAB)
    _focus_is(dialog.ctrl_texte)
    _press(simulator, wx.WXK_TAB, shift=True)
    _focus_is(dialog.radio2)

    # Retour à l'état initial : le champ désactivé ne doit plus recevoir Tab.
    dialog.radio1.SetFocus()
    _press(simulator, wx.WXK_SPACE)
    assert dialog.radio1.GetValue()
    assert not dialog.ctrl_texte.IsEnabled()
    _press(simulator, wx.WXK_TAB)
    assert wx.Window.FindFocus() is not dialog.ctrl_texte

    dialog.Destroy()
    _pump()


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if sys.platform != "win32":
        REPORT.write_text("Smoke réservé à Windows.\n", encoding="utf-8")
        return 0

    app = wx.App(False)
    frame = wx.Frame(None, title="Teamworks wx keyboard smoke")
    frame.Show()
    frame.Raise()
    _pump()
    simulator = wx.UIActionSimulator()

    try:
        _test_common_components(frame, simulator)
        _test_escape(frame, simulator)
        _test_filter_state_and_navigation(frame, simulator)
        REPORT.write_text(
            "Focus, Tab, Shift+Tab, Enter, Espace, Escape et changements d'état : OK.\n",
            encoding="utf-8",
        )
        print("TEAMWORKS_WX_KEYBOARD_ACCESSIBILITY_READY", flush=True)
        return 0
    except Exception:
        details = traceback.format_exc()
        REPORT.write_text(details, encoding="utf-8")
        print(details, file=sys.stderr)
        print("TEAMWORKS_WX_KEYBOARD_ACCESSIBILITY_FAILED", flush=True)
        return 1
    finally:
        if frame:
            frame.Destroy()
        _pump(40)


if __name__ == "__main__":
    raise SystemExit(main())
