#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from teamworks.CcnsCore.home_gadgets_ccns import (
    build_ccns_home_gadgets,
    build_ccns_home_alert_lines,
)

try:
    from Ctrl import CTRL_Page_contrats
except Exception:
    CTRL_Page_contrats = None


class Panel(wx.Panel):
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.staticbox = wx.StaticBox(self, -1, u"Contrôle CCNS")
        self.rows = []

        self.list_stats = wx.ListCtrl(self, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_stats.InsertColumn(0, u"Indicateur", width=250)
        self.list_stats.InsertColumn(1, u"Valeur", width=100)

        self.list_alerts = wx.ListCtrl(self, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_alerts.InsertColumn(0, u"Alerte", width=420)
        self.list_alerts.InsertColumn(1, u"Détails", width=340)

        self.button_refresh = wx.Button(self, -1, u"Actualiser")
        self.button_open_contract = wx.Button(self, -1, u"Ouvrir le contrat")
        self.button_open_contract.Enable(False)

        self.button_refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
        self.button_open_contract.Bind(wx.EVT_BUTTON, self.OnOpenContract)
        self.list_alerts.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChanged)
        self.list_alerts.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChanged)
        self.list_alerts.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnOpenContract)

        self.__do_layout()
        self.MAJ()

    def __do_layout(self):
        sizer_base = wx.StaticBoxSizer(self.staticbox, wx.VERTICAL)
        sizer_base.Add(self.list_stats, 0, wx.ALL | wx.EXPAND, 8)
        sizer_base.Add(self.list_alerts, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons.Add(self.button_refresh, 0, wx.RIGHT, 8)
        sizer_buttons.Add(self.button_open_contract, 0, 0, 0)
        sizer_base.Add(sizer_buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 8)

        self.SetSizer(sizer_base)
        self.Layout()

    def _apply_alert_style(self, index, severity):
        try:
            if severity == "blocking":
                self.list_alerts.SetItemBackgroundColour(index, wx.Colour(255, 228, 228))
                self.list_alerts.SetItemTextColour(index, wx.Colour(120, 0, 0))
            elif severity == "warning":
                self.list_alerts.SetItemBackgroundColour(index, wx.Colour(255, 245, 204))
                self.list_alerts.SetItemTextColour(index, wx.Colour(90, 60, 0))
        except Exception:
            pass

    def MAJ(self):
        self.list_stats.DeleteAllItems()
        self.list_alerts.DeleteAllItems()
        self.rows = []

        for stat in build_ccns_home_gadgets():
            idx = self.list_stats.InsertItem(self.list_stats.GetItemCount(), stat["label"])
            self.list_stats.SetItem(idx, 1, str(stat["value"]))
            try:
                if stat["severity"] == "blocking":
                    self.list_stats.SetItemTextColour(idx, wx.Colour(140, 0, 0))
                elif stat["severity"] == "warning":
                    self.list_stats.SetItemTextColour(idx, wx.Colour(130, 80, 0))
                elif stat["severity"] == "ok":
                    self.list_stats.SetItemTextColour(idx, wx.Colour(0, 110, 0))
            except Exception:
                pass

        self.rows = build_ccns_home_alert_lines()
        for row in self.rows:
            idx = self.list_alerts.InsertItem(self.list_alerts.GetItemCount(), row["label"])
            self.list_alerts.SetItem(idx, 1, row["details"])
            self.list_alerts.SetItemData(idx, int(row["contract_id"]))
            self._apply_alert_style(idx, row["severity"])

        self.button_open_contract.Enable(False)

    def OnRefresh(self, event):
        self.MAJ()

    def _get_selected_contract_id(self):
        index = self.list_alerts.GetFirstSelected()
        if index == -1:
            return None
        try:
            return self.list_alerts.GetItemData(index)
        except Exception:
            return None

    def OnSelectionChanged(self, event):
        self.button_open_contract.Enable(self._get_selected_contract_id() is not None)
        if event is not None:
            event.Skip()

    def OnOpenContract(self, event):
        id_contrat = self._get_selected_contract_id()
        if id_contrat is None:
            return

        if CTRL_Page_contrats is None:
            wx.MessageBox(
                u"Le module de contrat n'est pas disponible dans cet environnement.",
                u"Ouverture indisponible",
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        opened = False
        if hasattr(CTRL_Page_contrats, "Dialog"):
            try:
                dlg = CTRL_Page_contrats.Dialog(self, IDcontrat=id_contrat)
                dlg.ShowModal()
                dlg.Destroy()
                opened = True
            except Exception:
                opened = False

        if not opened and hasattr(CTRL_Page_contrats, "CTRL"):
            try:
                dlg = wx.Dialog(self, -1, u"Contrat %s" % id_contrat, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
                ctrl = CTRL_Page_contrats.CTRL(dlg, IDcontrat=id_contrat)
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(ctrl, 1, wx.EXPAND | wx.ALL, 8)
                dlg.SetSizer(sizer)
                dlg.SetSize((980, 720))
                dlg.CentreOnScreen()
                dlg.ShowModal()
                dlg.Destroy()
                opened = True
            except Exception:
                opened = False

        if not opened:
            wx.MessageBox(
                u"Impossible d'ouvrir directement le contrat %s." % id_contrat,
                u"Ouverture impossible",
                wx.OK | wx.ICON_WARNING,
                self,
            )
