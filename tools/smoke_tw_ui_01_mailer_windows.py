#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TW-UI-01 : vraie boucle wx Windows, transport entierement fictif.

Ne charge aucune base, ne lit aucun compte SMTP et n'emet aucun courriel.
Le test observe les HWND, l'owner et les battements PENDANT le travail.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "teamworks"))


def main() -> int:
    if sys.platform != "win32":
        print("TW_UI01_WINDOWS_SKIPPED: plateforme non Windows", flush=True)
        return 0

    import wx
    from Utils import UTILS_MailingSession

    app = wx.App(False)
    frame = wx.Frame(None, title="TW-UI-01 banc fictif", size=(720, 500))
    app.SetTopWindow(frame)
    frame.Show()
    frame.Maximize(True)

    user32 = ctypes.windll.user32
    user32.GetWindow.argtypes = (wintypes.HWND, ctypes.c_uint)
    user32.GetWindow.restype = wintypes.HWND
    user32.IsHungAppWindow.argtypes = (wintypes.HWND,)
    user32.IsHungAppWindow.restype = wintypes.BOOL
    hwnd = frame.GetHandle()

    releves = []
    owners = []
    proprietaires_wx = []
    erreurs = []
    compteur_envois = []
    connexions = []
    resultat = {}
    fin = threading.Event()
    debut_travail = [None]

    def surveiller(event):
        now = time.monotonic()
        releves.append((
            now, bool(frame.IsMaximized()), bool(frame.IsIconized()),
            bool(user32.IsHungAppWindow(hwnd)),
        ))
        for fenetre in wx.GetTopLevelWindows():
            if (isinstance(fenetre, wx.Dialog)
                    and fenetre.GetTitle() == "Envoi des mails"):
                proprietaires_wx.append(fenetre.GetParent() is frame)
                owners.append(int(user32.GetWindow(fenetre.GetHandle(), 4) or 0))

    timer = wx.Timer(frame)
    frame.Bind(wx.EVT_TIMER, surveiller, timer)
    timer.Start(30)

    class TransportFictif:
        def Connecter(self):
            connexions.append(threading.get_ident())
            time.sleep(0.35)

        def Envoyer(self, message):
            compteur_envois.append((message, threading.get_ident()))
            time.sleep(0.35)
            return 1

        def Fermer(self):
            pass

    def executer():
        debut_travail[0] = time.monotonic()
        try:
            if not frame.IsMaximized():
                raise AssertionError("Le banc Windows n'a pas maximise la fenetre")
            resultat["bilan"] = UTILS_MailingSession.envoyer_avec_progression(
                parent=frame, fabrique=TransportFictif,
                messages=["message_fictif"],
                afficher_confirmation_envoi=False,
            )
            resultat["maximise_apres"] = bool(frame.IsMaximized())
            resultat["iconise_apres"] = bool(frame.IsIconized())
        except Exception:
            erreurs.append(traceback.format_exc())
        finally:
            timer.Stop()
            app.ExitMainLoop()

    def limite():
        if not fin.is_set():
            print("TW_UI01_WINDOWS_TIMEOUT: boucle ou worker bloques", flush=True)
            os._exit(124)

    watchdog = threading.Timer(15, limite)
    watchdog.daemon = True
    watchdog.start()
    lancement = wx.CallLater(150, executer)
    try:
        app.MainLoop()
    finally:
        fin.set()
        watchdog.cancel()
        timer.Stop()
        if frame:
            frame.Destroy()

    if erreurs:
        print("TW_UI01_WINDOWS_ERROR:\n" + erreurs[0], flush=True)
        return 1

    bilan = resultat.get("bilan")
    if bilan is None or bilan.succes != ["message_fictif"]:
        print("TW_UI01_WINDOWS_FAIL: pas d'acceptation fictive", flush=True)
        return 1
    if len(compteur_envois) != 1 or len(connexions) != 1:
        print("TW_UI01_WINDOWS_FAIL: envoi ou connexion multiple", flush=True)
        return 1

    # Les releves doivent couvrir le vrai travail, et pas seulement l'apres.
    pendant = [r for r in releves if r[0] >= debut_travail[0]]
    max_retard = max(
        (b[0] - a[0] for a, b in zip(pendant, pendant[1:])),
        default=float("inf"),
    )
    ok = (
        len(pendant) >= 5
        and max_retard < 1.0
        and all(maximise and not iconise and not bloque
                for _, maximise, iconise, bloque in pendant)
        and resultat.get("maximise_apres") is True
        and resultat.get("iconise_apres") is False
        and len(proprietaires_wx) >= 1
        and all(proprietaires_wx)
        and len(owners) >= 1
        and all(owner == hwnd for owner in owners)
        and all(tid != threading.get_ident() for tid in connexions)
        and all(tid != threading.get_ident() for _, tid in compteur_envois)
    )
    print(
        "TW_UI01_WINDOWS_METRICS: battements=%d, retard_max=%.3fs, "
        "dialogues=%d, owner_hwnd_ok=%s, max_ok=%s, inconnu=%s" % (
            len(pendant), max_retard, len(owners),
            bool(owners) and all(owner == hwnd for owner in owners),
            all(flag for _, flag, _, _ in pendant),
            not ok,
        ),
        flush=True,
    )
    if not ok:
        print("TW_UI01_WINDOWS_FAIL: reactivite ou etat Win32 invalide", flush=True)
        return 1
    print("TW_UI01_WINDOWS_PASS: HWND et transport fictif qualifies", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
