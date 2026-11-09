#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TW-UI-01 phase 3 : fermeture tentee pendant l'envoi, sur wx natif.

Parcours limite au composant de progression (pas l'application Teamworks
complete). Transports purement fictifs ; aucune base ni aucun socket.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path
import os
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "teamworks"))


def main():
    if sys.platform != "win32":
        print("TW_UI01_CLOSE_SKIPPED: hors Windows", flush=True)
        return 0

    import wx
    from Utils import UTILS_MailingSession

    app = wx.App(False)
    cadre = wx.Frame(None, title="TW-UI-01 / cycle de vie", size=(800, 600))
    app.SetTopWindow(cadre)
    cadre.Show()
    user32 = ctypes.windll.user32

    class WindowPlacement(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.UINT), ("flags", wintypes.UINT),
            ("showCmd", wintypes.UINT),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT),
        ]

    user32.GetWindowPlacement.argtypes = (
        wintypes.HWND, ctypes.POINTER(WindowPlacement)
    )
    user32.GetWindowPlacement.restype = wintypes.BOOL
    user32.GetForegroundWindow.restype = wintypes.HWND

    def placement():
        info = WindowPlacement()
        info.length = ctypes.sizeof(WindowPlacement)
        if not user32.GetWindowPlacement(cadre.GetHandle(), ctypes.byref(info)):
            raise OSError("GetWindowPlacement impossible")
        return info.showCmd

    etats = {
        "essais": 0, "appels": 0, "resultat": None,
        "placement_initial": placement(),
        "focus_initial": int(user32.GetForegroundWindow() or 0),
    }
    anomalies = []
    fin = threading.Event()

    class TransportFictif:
        def Connecter(self):
            time.sleep(0.25)
        def Envoyer(self, message):
            etats["appels"] += 1
            time.sleep(0.35)
            return 1
        def Fermer(self):
            pass

    def trouver_progression():
        return next(
            (win for win in wx.GetTopLevelWindows()
             if isinstance(win, wx.Dialog) and win.GetTitle() == "Envoi des mails"),
            None,
        )

    def tenter_fermeture():
        dlg = trouver_progression()
        assert dlg is not None and dlg.IsModal(), "Progression absente"
        etats["essais"] += 1
        dlg.Close()
        assert dlg.IsModal(), "Close a interrompu la boucle modale"
        assert dlg.IsShownOnScreen(), "Close a masque la progression"
        assert not cadre.IsMaximized(), "Maximisation forcee"
        etats["close_veto"] = True

    def verifier_apres_fermeture():
        dlg = trouver_progression()
        assert dlg is not None and dlg.IsModal()
        etats["modal_apres_close"] = True

    def verifier_destruction_differee():
        # Le vrai critere est une fenetre encore visible/apparente apres
        # la reprise normale de la boucle wx, pas juste apres Destroy().
        etats["dialogue_residuel"] = trouver_progression() is not None
        app.ExitMainLoop()

    def executer():
        appels = [
            wx.CallLater(90, tenter_fermeture),
            wx.CallLater(170, verifier_apres_fermeture),
        ]
        try:
            bilan = UTILS_MailingSession.envoyer_avec_progression(
                cadre, TransportFictif, ["fictif"], afficher_confirmation_envoi=False
            )
            etats["resultat"] = bilan
            # wx.Window.Destroy() sur une TopLevelWindow est souvent differe
            # jusqu'au prochain evenement idle. Ne pas mesurer trop tot.
            etats["worker_residuel"] = any(
                t.name == "teamworks-mailer" and t.is_alive()
                for t in threading.enumerate()
            )
            etats["fenetre_encore_normale"] = not cadre.IsMaximized()
            # Une iconisation demandee volontairement apres la transmission
            # ne doit pas provoquer de maximisation cachee.
            cadre.Iconize(True)
            etats["iconisation_volontaire"] = bool(cadre.IsIconized())
            cadre.Iconize(False)
            etats["retour_fenetre"] = not cadre.IsMaximized()
            etats["placement_final"] = placement()
            etats["focus_final"] = int(user32.GetForegroundWindow() or 0)
        except Exception:
            anomalies.append(traceback.format_exc())
        finally:
            for rappel in appels:
                if rappel.IsRunning():
                    rappel.Stop()
            wx.CallLater(120, verifier_destruction_differee)

    def expiration():
        if not fin.is_set():
            print("TW_UI01_CLOSE_TIMEOUT: modal ou worker bloques", flush=True)
            os._exit(124)

    watchdog = threading.Timer(12, expiration)
    watchdog.daemon = True
    watchdog.start()
    try:
        wx.CallLater(150, executer)
        app.MainLoop()
    finally:
        fin.set()
        watchdog.cancel()
        cadre.Destroy()

    if anomalies:
        print("TW_UI01_CLOSE_ERROR:\n" + anomalies[0], flush=True)
        return 1

    bilan = etats.get("resultat")
    requis = (
        bilan is not None and bilan.succes == ["fictif"]
        and etats.get("essais") == 1
        and etats.get("appels") == 1
        and etats.get("close_veto") is True
        and etats.get("modal_apres_close") is True
        and etats.get("dialogue_residuel") is False
        and etats.get("worker_residuel") is False
        and etats.get("fenetre_encore_normale") is True
        and etats.get("retour_fenetre") is True
        and etats.get("placement_final") not in (2, 3, 6, 7)
    )
    print(
        "TW_UI01_CLOSE_METRICS: fermeture_vetoe=%s, worker_residuel=%s, "
        "dialogue_residuel=%s, iconisation_volontaire=%s, "
        "placement_initial=%s, placement_final=%s, focus_change=%s" % (
            etats.get("close_veto"), etats.get("worker_residuel"),
            etats.get("dialogue_residuel"),
            etats.get("iconisation_volontaire"),
            etats.get("placement_initial"), etats.get("placement_final"),
            etats.get("focus_initial") != etats.get("focus_final"),
        ),
        flush=True,
    )
    if not requis:
        print("TW_UI01_CLOSE_FAIL: cycle de vie incorrect", flush=True)
        return 1
    print("TW_UI01_CLOSE_PASS: fermeture en cours de transport refusee", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
