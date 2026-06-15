#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from teamworks.CcnsCore.audit_person_summary import build_person_ccns_summary

try:
    from Ctrl import CTRL_Page_contrats
except Exception:
    CTRL_Page_contrats = None


class Panel(wx.Panel):
    def __init__(self, parent, id=-1, IDpersonne=None):
        wx.Panel.__init__(self, parent, id)
        self.IDpersonne = IDpersonne
        self.rows = []

        self.staticbox = wx.StaticBox(self, -1, u"Synthese CCNS")
        self.label_status = wx.StaticText(self, -1, u"Statut global :")
        self.ctrl_status = wx.StaticText(self, -1, u"")

        self.label_counts = wx.StaticText(self, -1, u"Contrats / anomalies :")
        self.ctrl_counts = wx.StaticText(self, -1, u"")

        self.legend = wx.StaticText(
            self,
            -1,
            u"Rouge = bloquant, jaune = a revoir, vert = OK. Double-clic pour tenter d'ouvrir le contrat.",
        )

        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.InsertColumn(0, u"ID", width=70)
        self.list_ctrl.InsertColumn(1, u"Gravite", width=90)
        self.list_ctrl.InsertColumn(2, u"Classification", width=100)
        self.list_ctrl.InsertColumn(3, u"Type", width=100)
        self.list_ctrl.InsertColumn(4, u"Salaire base", width=100)
        self.list_ctrl.InsertColumn(5, u"Anomalies", width=260)
        self.list_ctrl.InsertColumn(6, u"Messages", width=460)

        self.button_refresh = wx.Button(self, -1, u"Actualiser")
        self.button_open_contract = wx.Button(self, -1, u"Ouvrir le contrat")
        self.button_open_contract.Enable(False)

        self.button_refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
        self.button_open_contract.Bind(wx.EVT_BUTTON, self.OnOpenContract)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChanged)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChanged)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnOpenContract)

        self.__do_layout()
        self.MAJ()

    def __do_layout(self):
        sizer_base = wx.StaticBoxSizer(self.staticbox, wx.VERTICAL)

        sizer_header = wx.FlexGridSizer(rows=2, cols=2, vgap=6, hgap=10)
        sizer_header.Add(self.label_status, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_header.Add(self.ctrl_status, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_header.Add(self.label_counts, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_header.Add(self.ctrl_counts, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons.Add(self.button_refresh, 0, wx.RIGHT, 8)
        sizer_buttons.Add(self.button_open_contract, 0, 0, 0)

        sizer_base.Add(sizer_header, 0, wx.ALL | wx.EXPAND, 10)
        sizer_base.Add(self.legend, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer_base.Add(self.list_ctrl, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer_base.Add(sizer_buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 10)

        self.SetSizer(sizer_base)
        self.Layout()

    def _status_to_label(self, status):
        return {
            "BLOQUANT": u"Bloquant",
            "A_REVOIR": u"A revoir",
            "OK": u"OK",
            "AUCUN_CONTRAT": u"Aucun contrat",
        }.get(status, status)

    def _apply_row_style(self, index, severity):
        try:
            if severity == "blocking":
                self.list_ctrl.SetItemBackgroundColour(index, wx.Colour(255, 228, 228))
                self.list_ctrl.SetItemTextColour(index, wx.Colour(120, 0, 0))
            elif severity == "warning":
                self.list_ctrl.SetItemBackgroundColour(index, wx.Colour(255, 245, 204))
                self.list_ctrl.SetItemTextColour(index, wx.Colour(90, 60, 0))
            else:
                self.list_ctrl.SetItemBackgroundColour(index, wx.Colour(232, 247, 232))
                self.list_ctrl.SetItemTextColour(index, wx.Colour(0, 70, 0))
        except Exception:
            pass

    def MAJ(self):
        summary = build_person_ccns_summary(self.IDpersonne)
        self.rows = summary["rows"]

        self.ctrl_status.SetLabel(self._status_to_label(summary["global_status"]))
        self.ctrl_counts.SetLabel(
            u"%d contrat(s), %d anomalie(s), %d bloquant(s), %d a revoir, %d OK" % (
                summary["nb_contracts"],
                summary["nb_anomalies"],
                summary["nb_blocking"],
                summary["nb_warning"],
                summary["nb_ok"],
            )
        )

        self.list_ctrl.DeleteAllItems()
        labels = {"blocking": u"Bloquant", "warning": u"A revoir", "ok": u"OK"}

        ordered = sorted(
            self.rows,
            key=lambda row: (row.get("severity_rank", 2), row.get("IDcontrat", 0))
        )

        for row in ordered:
            idx = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), str(row.get("IDcontrat", "")))
            self.list_ctrl.SetItem(idx, 1, labels.get(row.get("severity_label", "ok"), ""))
            self.list_ctrl.SetItem(idx, 2, row.get("classification", ""))
            self.list_ctrl.SetItem(idx, 3, row.get("type_contrat", ""))
            salaire = row.get("salaire_base")
            self.list_ctrl.SetItem(idx, 4, "" if salaire is None else "%.2f" % float(salaire))
            self.list_ctrl.SetItem(idx, 5, ", ".join(row.get("anomalies", [])))
            self.list_ctrl.SetItem(idx, 6, " | ".join(row.get("messages", [])))
            self.list_ctrl.SetItemData(idx, int(row.get("IDcontrat", 0)))
            self._apply_row_style(idx, row.get("severity_label", "ok"))

        self.button_open_contract.Enable(False)
        self.Layout()

    def OnRefresh(self, event):
        self.MAJ()

    def _get_selected_contract_id(self):
        index = self.list_ctrl.GetFirstSelected()
        if index == -1:
            return None
        try:
            return self.list_ctrl.GetItemData(index)
        except Exception:
            text = self.list_ctrl.GetItem(index, 0).GetText()
            try:
                return int(text)
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
                u"Le module d'ouverture de contrat n'est pas disponible dans cet environnement.",
                u"Ouverture indisponible",
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        opened = False
        errors = []

        if hasattr(CTRL_Page_contrats, "Dialog"):
            try:
                dlg = CTRL_Page_contrats.Dialog(self, IDcontrat=id_contrat)
                dlg.ShowModal()
                dlg.Destroy()
                opened = True
            except Exception as exc:
                errors.append("Dialog(IDcontrat=...): %s" % exc)

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
            except Exception as exc:
                errors.append("CTRL(IDcontrat=...): %s" % exc)

        if not opened:
            message = u"Impossible d'ouvrir directement la fiche contrat %s." % id_contrat
            if errors:
                message += u"\n\nTentatives effectuees :\n- " + u"\n- ".join(errors)
            wx.MessageBox(
                message,
                u"Ouverture impossible",
                wx.OK | wx.ICON_WARNING,
                self,
            )
