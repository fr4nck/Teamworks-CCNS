#!/usr/bin/env python3
"""Vérifie le rendu structurel de la navigation et du dashboard sous Windows."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
sys.path.insert(0, str(TEAMWORKS))

# Le défaut signalé concerne explicitement l'apparence sombre. La valeur est
# posée avant les imports du thème afin de ne pas dépendre du profil du runner.
os.environ["TEAMWORKS_APPEARANCE"] = "dark"

import wx
import wx.aui as aui

from Ctrl import CTRL_Gadgets_flottants
from Ctrl import CTRL_Navigation_principale
from Utils import UTILS_Interface


def _same_colour(left, right):
    return tuple(left) == tuple(right)


def main() -> int:
    if sys.platform != "win32":
        print("Windows-only navigation smoke skipped")
        return 0

    app = wx.App(False)
    print("TEAMWORKS_SMOKE_MAIN_NAVIGATION_STAGE:navigation", flush=True)
    frame = wx.Frame(None, title="Navigation sombre", size=(1200, 700))
    navigation = CTRL_Navigation_principale.NavigationPrincipale(frame)
    for label in ("Accueil", "Individus", "Présences", "Recrutement"):
        navigation.AddPage(wx.Panel(navigation), label, select=label == "Accueil")

    frame.Show()
    frame.Layout()
    app.ProcessPendingEvents()
    wx.YieldIfNeeded()

    widths = [button.GetSize().GetWidth() for button in navigation._boutons]
    minimums = [button.GetMinSize().GetWidth() for button in navigation._boutons]
    maximums = [button.GetMaxSize().GetWidth() for button in navigation._boutons]
    print(
        "TEAMWORKS_SMOKE_MAIN_NAVIGATION_SIZES:%s:%s:%s:%s"
        % (widths, minimums, maximums, navigation.barre.GetClientSize().GetWidth()),
        flush=True,
    )
    assert len(widths) == 4
    assert widths == minimums == maximums
    assert max(widths) < min(widths) * 1.75
    assert sum(widths) < navigation.barre.GetClientSize().GetWidth() * 0.75

    inactive_background, inactive_text, _ = navigation._boutons[-1]._Couleurs()
    assert _same_colour(
        inactive_background,
        UTILS_Interface.GetToken("surface_container_low", appearance="dark"),
    )
    assert _same_colour(
        inactive_text,
        UTILS_Interface.GetToken("on_surface", appearance="dark"),
    )

    print("TEAMWORKS_SMOKE_MAIN_NAVIGATION_STAGE:dashboard", flush=True)
    dashboard_frame = wx.Frame(None, title="Dashboard sombre", size=(900, 600))
    dashboard = CTRL_Gadgets_flottants.EspaceGadgets(dashboard_frame, [])
    art = dashboard.manager.GetArtProvider()
    assert _same_colour(
        art.GetColour(aui.AUI_DOCKART_BACKGROUND_COLOUR),
        UTILS_Interface.GetToken("surface", appearance="dark"),
    )
    assert _same_colour(
        art.GetColour(aui.AUI_DOCKART_SASH_COLOUR),
        UTILS_Interface.GetToken("surface_container_high", appearance="dark"),
    )

    dashboard_frame.Destroy()
    frame.Destroy()
    app.ProcessPendingEvents()
    print("TEAMWORKS_SMOKE_MAIN_NAVIGATION_READY", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
