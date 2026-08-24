#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from Utils import UTILS_Interface

try:
    from Ctrl import CTRL_Page_contrats
except Exception:
    CTRL_Page_contrats = None


def apply_ccns_item_style(tree_ctrl, item, severity):
    """Applique la même sémantique visuelle que le reste du contrôle CCNS."""
    try:
        couleurs = {
            "blocking": UTILS_Interface.GetToken("danger"),
            "warning": UTILS_Interface.GetToken("warning"),
            "ok": UTILS_Interface.GetToken("success"),
        }
        tree_ctrl.SetItemTextColour(
            item,
            couleurs.get(severity, UTILS_Interface.GetToken("on_surface")),
        )
    except Exception:
        pass


def _taille_dialogue(parent):
    """Dimensionne le contrat selon l'écran au lieu d'imposer 980x720."""
    try:
        display_index = wx.Display.GetFromWindow(parent)
        if display_index == wx.NOT_FOUND:
            display_index = 0
        zone = wx.Display(display_index).GetClientArea()
        largeur = max(760, min(1180, int(zone.GetWidth() * 0.82)))
        hauteur = max(540, min(840, int(zone.GetHeight() * 0.82)))
        return largeur, hauteur
    except Exception:
        return 980, 720


def open_ccns_target(parent, contract_ids, open_individual_callback=None, IDpersonne=None):
    contract_ids = contract_ids or []

    if len(contract_ids) == 1:
        id_contrat = contract_ids[0]
        if CTRL_Page_contrats is None:
            wx.MessageBox(
                u"Le module de contrat n'est pas disponible.",
                u"Ouverture indisponible",
                wx.OK | wx.ICON_WARNING,
                parent,
            )
            return False

        opened = False
        if hasattr(CTRL_Page_contrats, "Dialog"):
            try:
                dlg = CTRL_Page_contrats.Dialog(parent, IDcontrat=id_contrat)
                dlg.ShowModal()
                dlg.Destroy()
                opened = True
            except Exception:
                opened = False

        if not opened and hasattr(CTRL_Page_contrats, "CTRL"):
            try:
                dlg = wx.Dialog(
                    parent,
                    -1,
                    u"Contrat %s" % id_contrat,
                    style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                )
                ctrl = CTRL_Page_contrats.CTRL(dlg, IDcontrat=id_contrat)
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(ctrl, 1, wx.EXPAND | wx.ALL, 8)
                dlg.SetSizer(sizer)
                dlg.SetSize(_taille_dialogue(parent))
                dlg.CentreOnParent()
                dlg.ShowModal()
                dlg.Destroy()
                opened = True
            except Exception:
                opened = False
        return opened

    if open_individual_callback and IDpersonne is not None:
        open_individual_callback(IDpersonne, page_code="ccns_summary")
        return True

    return False
