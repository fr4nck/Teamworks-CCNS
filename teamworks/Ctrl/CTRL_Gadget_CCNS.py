#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from teamworks.Utils import UTILS_Diagnostic_performance as DiagnosticPerformance
from teamworks.CcnsCore.home_gadgets_ccns import build_ccns_home_data
from Utils import UTILS_Colonnes
from Utils import UTILS_Interface

try:
    from Ctrl import CTRL_Page_contrats
except Exception:
    CTRL_Page_contrats = None


class Panel(wx.Panel):
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id, name="gadget_ccns")
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = wx.StaticText(self, -1, u"Contrôle CCNS")
        font = self.titre.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(max(11, font.GetPointSize() + 1))
        self.titre.SetFont(font)

        self.rows = []

        self.list_stats = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.list_stats.InsertColumn(0, u"Indicateur", width=250)
        self.list_stats.InsertColumn(1, u"Valeur", width=100)
        self.colonnes_stats = UTILS_Colonnes.ColonnesFlexibles(
            self.list_stats,
            extensibles=(0,),
        )

        self.list_alerts = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.list_alerts.InsertColumn(0, u"Alerte", width=420)
        self.list_alerts.InsertColumn(1, u"Détails", width=340)
        self.colonnes_alerts = UTILS_Colonnes.ColonnesFlexibles(
            self.list_alerts,
            extensibles=(0, 1),
        )

        self.button_refresh = wx.Button(self, -1, u"Actualiser")
        self.button_open_contract = wx.Button(self, -1, u"Ouvrir le contrat")
        self.button_open_contract.Enable(False)

        self.button_refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
        self.button_open_contract.Bind(wx.EVT_BUTTON, self.OnOpenContract)
        self.list_alerts.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChanged)
        self.list_alerts.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChanged)
        self.list_alerts.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnOpenContract)

        self.__do_layout()
        self._show_loading()
        wx.CallAfter(self.MAJ)

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_base.Add(self.list_stats, 0, wx.ALL | wx.EXPAND, 8)
        sizer_base.Add(
            self.list_alerts,
            1,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            8,
        )

        sizer_buttons = wx.WrapSizer(wx.HORIZONTAL)
        sizer_buttons.Add(self.button_refresh, 0, wx.RIGHT | wx.BOTTOM, 8)
        sizer_buttons.Add(self.button_open_contract, 0, wx.BOTTOM, 8)
        sizer_base.Add(sizer_buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        self.SetSizer(sizer_base)

    def _apply_alert_style(self, index, severity):
        """Utilise la sémantique CCNS sans aplats rouge/jaune agressifs."""
        try:
            background = UTILS_Interface.GetToken("surface_container_low")
            if severity == "blocking":
                foreground = UTILS_Interface.GetToken("danger")
            elif severity == "warning":
                foreground = UTILS_Interface.GetToken("warning")
            else:
                foreground = UTILS_Interface.GetToken("on_surface")
            self.list_alerts.SetItemBackgroundColour(index, background)
            self.list_alerts.SetItemTextColour(index, foreground)
        except Exception:
            pass

    def _show_loading(self):
        self.list_stats.DeleteAllItems()
        self.list_alerts.DeleteAllItems()
        idx = self.list_stats.InsertItem(0, u"Chargement…")
        self.list_stats.SetItem(idx, 1, u"")
        self.rows = []
        self.button_open_contract.Enable(False)

    def MAJ(self, force_refresh=False):
        with DiagnosticPerformance.mesurer(
            "total_action",
            "CTRL_Gadget_CCNS.MAJ",
            {"force_refresh": force_refresh},
        ):
            with DiagnosticPerformance.mesurer("widget", "CTRL_Gadget_CCNS.vider_listes"):
                self.list_stats.DeleteAllItems()
                self.list_alerts.DeleteAllItems()
                self.rows = []

            home_data = build_ccns_home_data(force_refresh=force_refresh)

            with DiagnosticPerformance.mesurer("widget", "CTRL_Gadget_CCNS.remplir_listes"):
                self._remplir_listes(home_data)

    def _remplir_listes(self, home_data):
        for stat in home_data["stats"]:
            idx = self.list_stats.InsertItem(self.list_stats.GetItemCount(), stat["label"])
            self.list_stats.SetItem(idx, 1, str(stat["value"]))
            try:
                if stat["severity"] == "blocking":
                    couleur = UTILS_Interface.GetToken("danger")
                elif stat["severity"] == "warning":
                    couleur = UTILS_Interface.GetToken("warning")
                elif stat["severity"] == "ok":
                    couleur = UTILS_Interface.GetToken("success")
                else:
                    couleur = UTILS_Interface.GetToken("on_surface")
                self.list_stats.SetItemTextColour(idx, couleur)
            except Exception:
                pass

        self.rows = home_data["alerts"]
        for row in self.rows:
            idx = self.list_alerts.InsertItem(
                self.list_alerts.GetItemCount(),
                row["label"],
            )
            self.list_alerts.SetItem(idx, 1, row["details"])
            self.list_alerts.SetItemData(idx, int(row["contract_id"]))
            self._apply_alert_style(idx, row["severity"])

        self.button_open_contract.Enable(False)
        wx.CallAfter(self.colonnes_stats.Ajuster)
        wx.CallAfter(self.colonnes_alerts.Ajuster)

    def OnRefresh(self, event):
        self._show_loading()
        wx.CallAfter(self.MAJ, True)

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
                dlg = wx.Dialog(
                    self,
                    -1,
                    u"Contrat %s" % id_contrat,
                    style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                )
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
