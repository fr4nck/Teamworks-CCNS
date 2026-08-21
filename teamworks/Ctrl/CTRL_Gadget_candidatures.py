#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Synthèse des éléments de recrutement à traiter.

Le contenu métier reste identique à l'ancien gadget, mais son rendu consomme
exclusivement la charte Teamworks : typographie sémantique, surfaces neutres et
couleur primaire pour la sélection.
"""

import datetime

import wx
import wx.lib.agw.customtreectrl as CT

import GestionDB
from Ctrl import CTRL_Texte
from Utils import UTILS_Dates
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


class Panel(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="panel_gadget_candidatures", style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.titre = CTRL_Texte.H3(self, _(u"Infos recrutement"))
        self.treeCtrl = TreeCtrl(self)
        self.treeCtrl.MAJ()

        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.AddSpacer(gap)
        sizer.Add(self.treeCtrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)


class PanelGadget(wx.Panel):
    """Version compacte utilisée dans les gadgets de l'accueil."""

    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="panel_gadget_candidatures", style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.treeCtrl = TreeCtrl(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.treeCtrl, 1, wx.EXPAND)
        self.SetSizer(sizer)


class MyFrame(wx.Frame):
    def __init__(self, parent, title=""):
        wx.Frame.__init__(self, parent, -1, title=title, name="frm_gadget_candidatures", style=wx.DEFAULT_FRAME_STYLE)
        self.panel = Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "standard")


class TreeCtrl(CT.CustomTreeCtrl):
    def __init__(self, parent, fichier="", id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.NO_BORDER):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        self.parent = parent

        self.SetAGWWindowStyleFlag(
            wx.TR_HIDE_ROOT
            | wx.TR_HAS_BUTTONS
            | wx.TR_HAS_VARIABLE_ROW_HEIGHT
            | CT.TR_AUTO_CHECK_CHILD
        )
        self.EnableSelectionVista(True)

        self.couleurFond = UTILS_Interface.GetToken("surface_container_lowest")
        self.SetBackgroundColour(self.couleurFond)
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.SetFont(UTILS_Styles.GetFont("body-small"))
        try:
            self.SetHilightFocusColour(UTILS_Interface.GetToken("primary_container"))
            self.SetHilightNonFocusColour(UTILS_Interface.GetToken("surface_container_high"))
        except Exception:
            pass

        self.ctrl_vide = wx.StaticText(self, -1, _(u"Aucune information"), style=wx.ALIGN_CENTER)
        UTILS_Styles.AppliquerTexte(self.ctrl_vide, "body-secondary")
        self.ctrl_vide.SetBackgroundColour(self.couleurFond)
        self.ctrl_vide.Show(False)

        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeftDown)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        self.ctrl_vide.SetBackgroundColour(self.GetBackgroundColour())
        largeur, hauteur = self.GetClientSize()
        best = self.ctrl_vide.GetBestSize()
        x = max(0, int((largeur - best.GetWidth()) / 2))
        y = max(0, int((hauteur - best.GetHeight()) / 3))
        self.ctrl_vide.SetPosition((x, y))
        event.Skip()

    def OnLeftDown(self, event):
        self.Unselect()
        event.Skip()

    def MAJ(self):
        self.DeleteAllItems()
        self.listeDonnees = self.GetListeDonnees()
        self.ctrl_vide.Show(not bool(self.listeDonnees))

        self.root = self.AddRoot("Root")
        self.SetItemData(self.root, None)
        self.AddTreeNodes(self.root, self.listeDonnees)
        self.Refresh()

    def AddTreeNodes(self, parentItem, items, img=None):
        for item in items:
            if not isinstance(item, list):
                ID, label = item
                newItem = self.AppendItem(parentItem, label)
                self.SetItemData(newItem, ID)
                self.SetItemFont(newItem, UTILS_Styles.GetFont("body-small"))
                self.SetItemTextColour(newItem, UTILS_Interface.GetToken("on_surface_variant"))
            else:
                texte = item[0][1]
                newItem = self.AppendItem(parentItem, texte)
                self.SetItemData(newItem, None)
                self.SetItemFont(newItem, UTILS_Styles.GetFont("h6"))
                self.SetItemTextColour(newItem, UTILS_Interface.GetToken("on_surface"))
                self.AddTreeNodes(newItem, item[1], img)
                self.Expand(newItem)

    def GetNom(self, IDcandidat=0, IDpersonne=0):
        if IDcandidat not in (0, None):
            nomID = "IDcandidat"
            ID = IDcandidat
            table = "candidats"
        else:
            nomID = "IDpersonne"
            ID = IDpersonne
            table = "personnes"

        DB = GestionDB.DB()
        req = """SELECT %s, civilite, nom, prenom
        FROM %s WHERE %s=%d ORDER BY nom, prenom; """ % (nomID, table, nomID, ID)
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if listeDonnees:
            return u"%s %s" % (listeDonnees[0][2], listeDonnees[0][3])
        return ""

    def FormateDate(self, dateStr):
        return UTILS_Dates.DateEngFr(dateStr)

    def GetListeDonnees(self):
        listeInfos = []

        DB = GestionDB.DB()
        dateDuJour = datetime.date.today()
        req = """SELECT IDentretien, IDcandidat, date, heure, avis, remarques, IDpersonne
        FROM entretiens WHERE (date <= '%s' AND avis=0) ORDER BY date, heure; """ % dateDuJour
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if listeDonnees:
            if len(listeDonnees) == 1:
                groupe = (0, _(u"1 entretien sans avis"))
            else:
                groupe = (0, _(u"%d entretiens sans avis") % len(listeDonnees))
            listeItems = []
            for IDentretien, IDcandidat, date, heure, avis, remarques, IDpersonne in listeDonnees:
                nom = self.GetNom(IDcandidat, IDpersonne)
                dateStr = self.FormateDate(date)
                listeItems.append((IDentretien, u"%s : %s" % (dateStr, nom)))
            listeInfos.append([groupe, listeItems])

        DB = GestionDB.DB()
        req = """SELECT IDcandidature, IDcandidat, IDpersonne, date_depot
        FROM candidatures WHERE (reponse_obligatoire=1 AND reponse=0) ORDER BY date_depot; """
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if listeDonnees:
            if len(listeDonnees) == 1:
                groupe = (0, _(u"1 candidature sans réponse"))
            else:
                groupe = (0, _(u"%d candidatures sans réponse") % len(listeDonnees))
            listeItems = []
            for IDcandidature, IDcandidat, IDpersonne, date_depot in listeDonnees:
                nom = self.GetNom(IDcandidat, IDpersonne)
                dateStr = self.FormateDate(date_depot)
                listeItems.append((IDcandidature, u"%s : %s" % (dateStr, nom)))
            listeInfos.append([groupe, listeItems])

        return listeInfos


if __name__ == "__main__":
    app = wx.App(0)
    frame = MyFrame(None, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
