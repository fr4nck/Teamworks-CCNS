#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Référentiel moderne des diffuseurs d'offres d'emploi."""

import wx
import GestionDB
from Ctrl import CTRL_Bouton_image, CTRL_Section
from Dlg import DLG_Config_diffuseurs_core as CORE
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


class ListCtrl(wx.ListCtrl):
    def __init__(self, parent, owner):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES)
        self.parent = owner
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest")); self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.InsertColumn(0, _(u"ID")); self.InsertColumn(1, _(u"Diffuseur")); self.InsertColumn(2, _(u"Offres diffusées")); self.SetColumnWidth(0, 0)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected); self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected); self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda evt: self.parent.Modifier()); self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu); self.Bind(wx.EVT_SIZE, self.OnSize)
        self.MAJListeCtrl()

    def MAJListeCtrl(self):
        self.DeleteAllItems(); DB = GestionDB.DB()
        req = """SELECT diffuseurs.IDdiffuseur, diffuseurs.diffuseur, COUNT(emplois_diffuseurs.IDemploi_diffuseur)
        FROM diffuseurs LEFT JOIN emplois_diffuseurs ON emplois_diffuseurs.IDdiffuseur=diffuseurs.IDdiffuseur
        GROUP BY diffuseurs.IDdiffuseur, diffuseurs.diffuseur ORDER BY diffuseurs.diffuseur;"""
        DB.ExecuterReq(req); rows = DB.ResultatReq(); DB.Close()
        for index, (IDdiffuseur, diffuseur, nombre) in enumerate(rows):
            self.InsertItem(index, str(IDdiffuseur)); self.SetItem(index, 1, diffuseur or ""); self.SetItem(index, 2, str(nombre or 0))
        self._ajuster_colonnes(); self.parent.bouton_modifier.Enable(False); self.parent.bouton_supprimer.Enable(False)

    def _ajuster_colonnes(self):
        largeur = max(360, self.GetClientSize().width); self.SetColumnWidth(0, 0); self.SetColumnWidth(2, max(110, int(largeur * 0.26))); self.SetColumnWidth(1, max(220, largeur - self.GetColumnWidth(2) - 8))
    def OnSize(self, event): self._ajuster_colonnes(); event.Skip()
    def OnItemSelected(self, event): self.parent.bouton_modifier.Enable(True); self.parent.bouton_supprimer.Enable(True); event.Skip()
    def OnItemDeselected(self, event):
        if self.GetFirstSelected() == -1: self.parent.bouton_modifier.Enable(False); self.parent.bouton_supprimer.Enable(False)
        event.Skip()

    def OnContextMenu(self, event):
        menu = wx.Menu(); id_add = wx.NewIdRef(); menu.Append(id_add, _(u"Ajouter un diffuseur")); self.Bind(wx.EVT_MENU, lambda evt: self.parent.Ajouter(), id=id_add)
        if self.GetFirstSelected() != -1:
            menu.AppendSeparator(); id_edit = wx.NewIdRef(); id_delete = wx.NewIdRef(); menu.Append(id_edit, _(u"Modifier")); menu.Append(id_delete, _(u"Supprimer")); self.Bind(wx.EVT_MENU, lambda evt: self.parent.Modifier(), id=id_edit); self.Bind(wx.EVT_MENU, lambda evt: self.parent.Supprimer(), id=id_delete)
        self.PopupMenu(menu); menu.Destroy()


class Panel(CORE.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, style=wx.TAB_TRAVERSAL); self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.section = CTRL_Section.Section(self, titre=_(u"Diffuseurs d'offres"), niveau=2, description=_(u"Organismes ou canaux utilisés pour diffuser les offres d'emploi.")); self.barreTitre = self.section.titre; contenu = self.section.GetContentPanel()
        self.bouton_ajouter = CTRL_Bouton_image.CTRL(contenu, texte=_(u"Ajouter")); self.bouton_modifier = CTRL_Bouton_image.CTRL(contenu, texte=_(u"Modifier")); self.bouton_supprimer = CTRL_Bouton_image.CTRL(contenu, texte=_(u"Supprimer")); self.bouton_aide = CTRL_Bouton_image.CTRL(contenu, texte=_(u"Aide"))
        self.bouton_modifier.Enable(False); self.bouton_supprimer.Enable(False)
        self.listCtrl = ListCtrl(contenu, self)
        if parent.GetName() != "treebook_configuration": self.bouton_aide.Show(False)
        gap = UTILS_Styles.GetLayoutSpacing("field_gap"); actions = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (self.bouton_ajouter, self.bouton_modifier, self.bouton_supprimer, self.bouton_aide): actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)
        s = wx.BoxSizer(wx.VERTICAL); s.Add(self.listCtrl, 1, wx.EXPAND); s.AddSpacer(gap); s.Add(actions, 0, wx.EXPAND); contenu.SetSizer(s); root = wx.BoxSizer(wx.VERTICAL); root.Add(self.section, 1, wx.EXPAND); self.SetSizer(root)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter); self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier); self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer); self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER); self.parent = parent; self.panel_contenu = Panel(self); self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide")); self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte=_(u"Fermer")); self.SetTitle(_(u"Gestion des diffuseurs"))
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding"); actions = wx.BoxSizer(wx.HORIZONTAL); actions.Add(self.bouton_aide, 0); actions.AddStretchSpacer(1); actions.Add(self.bouton_fermer, 0); s = wx.BoxSizer(wx.VERTICAL); s.Add(self.panel_contenu, 1, wx.EXPAND | wx.ALL, padding); s.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding); self.SetSizer(s)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.panel_contenu.OnBoutonAide(evt), self.bouton_aide); self.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CANCEL), self.bouton_fermer); UTILS_Styles.ApplyWindowProfile(self, "standard")


if __name__ == "__main__":
    app = wx.App(0); dlg = Dialog(None); dlg.ShowModal(); dlg.Destroy(); app.MainLoop()
