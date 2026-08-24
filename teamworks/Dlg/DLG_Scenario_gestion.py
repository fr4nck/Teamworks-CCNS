#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
import FonctionsPerso
import wx.lib.agw.hypertreelist as HTL
from Dlg import DLG_Scenario
from Utils import UTILS_Adaptations, UTILS_Dates, UTILS_Interface
import six


def _dip(window, width, height):
    try:
        return window.FromDIP(wx.Size(width, height))
    except Exception:
        return wx.Size(width, height)


class Panel(wx.Panel):
    def __init__(self, parent, ID=-1, IDpersonne=None):
        wx.Panel.__init__(self, parent, ID, name="gestion_scenarios", style=wx.TAB_TRAVERSAL)
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        texteIntro = _(u"Vous pouvez ici créer, modifier ou supprimer des scénarios.")
        self.label_introduction = FonctionsPerso.StaticWrapText(self, -1, texteIntro)
        self.label_introduction.SetForegroundColour(UTILS_Interface.GetToken("on_surface_variant"))

        self.listCtrl = TreeListCtrl(self, -1, IDpersonne=IDpersonne)
        self.bouton_ajouter = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Ajouter"), cheminImage="Images/32x32/Ajouter.png"
        )
        self.bouton_modifier = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Modifier"), cheminImage="Images/32x32/Modifier.png"
        )
        self.bouton_supprimer = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Supprimer"), cheminImage="Images/32x32/Supprimer.png"
        )
        self.bouton_dupliquer = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Dupliquer"), cheminImage="Images/32x32/Dupliquer.png"
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDupliquer, self.bouton_dupliquer)

    def __set_properties(self):
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour créer un nouveau scénario")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier le scénario sélectionné dans la liste")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer le scénario sélectionné dans la liste")))
        self.bouton_dupliquer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour dupliquer le scénario sélectionné")))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_introduction, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_base.Add(self.listCtrl, 1, wx.EXPAND | wx.ALL, 10)

        sizer_actions = wx.WrapSizer(wx.HORIZONTAL)
        sizer_actions.Add(self.bouton_ajouter, 0, wx.RIGHT | wx.BOTTOM, 6)
        sizer_actions.Add(self.bouton_modifier, 0, wx.RIGHT | wx.BOTTOM, 6)
        sizer_actions.Add(self.bouton_supprimer, 0, wx.RIGHT | wx.BOTTOM, 6)
        sizer_actions.Add(self.bouton_dupliquer, 0, wx.RIGHT | wx.BOTTOM, 6)
        sizer_base.Add(sizer_actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizer(sizer_base)

    def OnBoutonAjouter(self, event):
        self.Ajouter()

    def Ajouter(self):
        dlg = DLG_Scenario.Dialog(self, IDscenario=None, IDpersonne=self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonModifier(self, event):
        self.Modifier()

    def Modifier(self):
        item = self.listCtrl.GetSelection()
        IDscenario = self.listCtrl.GetItemData(item)
        if IDscenario is None or IDscenario > 100000 or IDscenario == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un scénario à modifier dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlg = DLG_Scenario.Dialog(self, IDscenario=IDscenario, IDpersonne=self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonSupprimer(self, event):
        self.Supprimer()

    def Supprimer(self):
        item = self.listCtrl.GetSelection()
        IDscenario = self.listCtrl.GetItemData(item)
        if IDscenario is None or IDscenario > 100000 or IDscenario == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un scénario à supprimer dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        DB = GestionDB.DB()
        req = "SELECT IDscenario_cat, IDscenario, IDcategorie, prevision, report, date_debut_realise, date_fin_realise FROM scenarios_cat;"
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        nbreReports = 0
        for IDscenario_cat, IDscenarioTmp, IDcategorie, prevision, report, date_debut_realise, date_fin_realise in listeDonnees:
            if report != "" and report is not None:
                if report[0] == "A":
                    IDscenarioReport, IDcategorie = report[1:].split(";")
                    if int(IDscenarioReport) == IDscenario:
                        nbreReports += 1

        if nbreReports > 0:
            if nbreReports == 1:
                txtMessage = six.text_type(_(u"Un report utilise ce scénario.\n\nSouhaitez-vous tout de même le supprimer ?"))
            else:
                txtMessage = six.text_type(_(u"%d reports utilisent ce scénario.\n\nSouhaitez-vous tout de même le supprimer ?") % nbreReports)
            dlgConfirm = wx.MessageDialog(self, txtMessage, _(u"Confirmation de suppression"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            reponse = dlgConfirm.ShowModal()
            dlgConfirm.Destroy()
            if reponse == wx.ID_NO:
                return

        Nom = self.listCtrl.GetItemText(item)
        txtMessage = six.text_type((_(u"Voulez-vous vraiment supprimer ce scénario ? \n\n> ") + Nom))
        dlgConfirm = wx.MessageDialog(self, txtMessage, _(u"Confirmation de suppression"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return

        DB = GestionDB.DB()
        DB.ReqDEL("scenarios", "IDscenario", IDscenario)
        DB.ReqDEL("scenarios_cat", "IDscenario", IDscenario)
        DB.Close()
        self.listCtrl.MAJ()

    def OnBoutonDupliquer(self, event):
        item = self.listCtrl.GetSelection()
        IDscenario = self.listCtrl.GetItemData(item)
        if IDscenario is None:
            return False
        if IDscenario > 100000 or IDscenario == -1:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord sélectionner un scénario à dupliquer dans la liste."), "Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        Nom = self.listCtrl.GetItemText(item)
        txtMessage = six.text_type((_(u"Voulez-vous vraiment dupliquer ce scénario ? \n\n> ") + Nom))
        dlgConfirm = wx.MessageDialog(self, txtMessage, _(u"Confirmation de duplication"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return

        DB = GestionDB.DB()
        req = "SELECT IDpersonne, nom, description, mode_heure, detail_mois, date_debut, date_fin, toutes_categories FROM scenarios WHERE IDscenario=%d ;" % IDscenario
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()

        for IDpersonne, nom, description, mode_heure, detail_mois, date_debut, date_fin, toutes_categories in listeDonnees:
            listeDonnees = [
                ("IDpersonne", IDpersonne),
                ("nom", _(u"Copie de %s") % nom),
                ("description", description),
                ("mode_heure", mode_heure),
                ("detail_mois", detail_mois),
                ("date_debut", date_debut),
                ("date_fin", date_fin),
                ("toutes_categories", toutes_categories),
            ]
            newIDscenario = DB.ReqInsert("scenarios", listeDonnees)
            DB.Commit()

        req = "SELECT IDscenario_cat, IDscenario, IDcategorie, prevision, report, date_debut_realise, date_fin_realise FROM scenarios_cat WHERE IDscenario=%d;" % IDscenario
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()

        for IDscenario_cat, IDscenario, IDcategorie, prevision, report, date_debut_realise, date_fin_realise in listeDonnees:
            listeDonnees = [
                ("IDscenario", newIDscenario),
                ("IDcategorie", IDcategorie),
                ("prevision", prevision),
                ("report", report),
                ("date_debut_realise", date_debut_realise),
                ("date_fin_realise", date_fin_realise),
            ]
            IDscenario_cat = DB.ReqInsert("scenarios_cat", listeDonnees)
            DB.Commit()

        DB.Close()
        dlg = DLG_Scenario.Dialog(self, IDscenario=newIDscenario, IDpersonne=self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()

    def MAJ_ListCtrl(self, IDselection=None):
        self.listCtrl.MAJ(IDselection)
        self.listCtrl.SetFocus()

    def MAJpanel(self):
        self.listCtrl.MAJ()


class TreeListCtrl(HTL.HyperTreeList):
    def __init__(self, *args, **kwds):
        self.IDpersonne = kwds.pop("IDpersonne", None)
        self.selectionID = kwds.pop("selectionID", None)
        self._columns_initialized = False
        HTL.HyperTreeList.__init__(self, *args, **kwds)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.SetAGWWindowStyleFlag(
            wx.TR_HIDE_ROOT
            | wx.TR_HAS_BUTTONS
            | HTL.TR_COLUMN_LINES
            | wx.TR_HAS_VARIABLE_ROW_HEIGHT
            | wx.TR_FULL_ROW_HIGHLIGHT
            | wx.TR_SINGLE
        )
        self.InitTreeCtrl()
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnContextMenu)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _init_columns(self):
        if self._columns_initialized:
            return
        if self.IDpersonne is None:
            self.AddColumn(_(u"Nom personne / nom scénario"))
        else:
            self.AddColumn(_(u"Nom du scénario"))
        self.AddColumn(_(u"Période"))
        self.AddColumn(_(u"Description"))
        self.SetMainColumn(0)
        self._columns_initialized = True
        self._resize_columns()

    def _resize_columns(self):
        if not self._columns_initialized:
            return
        width = max(430, self.GetClientSize().width - 18)
        if self.IDpersonne is None:
            proportions = (0.34, 0.24, 0.42)
        else:
            proportions = (0.30, 0.25, 0.45)
        first = max(130, int(width * proportions[0]))
        second = max(130, int(width * proportions[1]))
        third = max(160, width - first - second)
        self.SetColumnWidth(0, first)
        self.SetColumnWidth(1, second)
        self.SetColumnWidth(2, third)

    def OnSize(self, event):
        self._resize_columns()
        event.Skip()

    def InitTreeCtrl(self):
        self.dict_personnes = self.GetDictPersonnes()
        self.dictScenarios = self.GetDictScenarios()
        self._init_columns()

        self.root = self.AddRoot("Racine")
        self.SetItemText(self.root, u"", 1)
        self.SetItemText(self.root, u"", 2)

        if self.IDpersonne is None:
            listeIDPersonnes = list(self.dictScenarios.keys())
            listeNomsPersonnes = []
            for IDpersonne in listeIDPersonnes:
                if IDpersonne in self.dict_personnes:
                    IDpersonne, nom, prenom, civilite = self.dict_personnes[IDpersonne]
                    listeNomsPersonnes.append((u"%s %s" % (nom, prenom), civilite, IDpersonne))
            listeNomsPersonnes.sort()

            for nomPersonne, civilite, IDpersonne in listeNomsPersonnes:
                child = self.AppendItem(self.root, nomPersonne)
                self.SetItemBold(child, True)
                self.SetItemTextColour(child, UTILS_Interface.GetToken("on_surface"))
                self.SetItemText(child, "", 1)
                self.SetItemText(child, "", 2)
                self.SetItemData(child, 100000 + IDpersonne)

                listeScenarios = self.dictScenarios[IDpersonne]
                for IDscenario, nom, description, date_debut, date_fin in listeScenarios:
                    last = self.AppendItem(child, nom)
                    periode = _(u"Du %s au %s") % (self.FormateDate(date_debut), self.FormateDate(date_fin))
                    self.SetItemText(last, periode, 1)
                    if description == "" or description is None:
                        description = _(u"Aucune description")
                    self.SetItemText(last, str(description), 2)
                    self.SetItemData(last, IDscenario)
                    if self.selectionID == IDscenario:
                        self.EnsureVisible(last)
                        self.SelectItem(last, last)
                self.Expand(child)
        else:
            if self.IDpersonne in self.dictScenarios:
                listeScenarios = self.dictScenarios[self.IDpersonne]
                for IDscenario, nom, description, date_debut, date_fin in listeScenarios:
                    last = self.AppendItem(self.root, nom)
                    periode = _(u"Du %s au %s") % (self.FormateDate(date_debut), self.FormateDate(date_fin))
                    self.SetItemText(last, periode, 1)
                    if description == "" or description is None:
                        description = _(u"Aucune description")
                    self.SetItemText(last, str(description), 2)
                    self.SetItemData(last, IDscenario)
                    if self.selectionID == IDscenario:
                        self.EnsureVisible(last)
                        self.SelectItem(last, last)
        self._resize_columns()

    def MAJ(self, selectionID=None):
        self.DeleteAllItems()
        self.selectionID = selectionID
        self.InitTreeCtrl()

    def FormateDate(self, dateStr):
        return UTILS_Dates.DateEngFr(dateStr)

    def GetDictScenarios(self):
        DB = GestionDB.DB()
        if self.IDpersonne is None:
            req = "SELECT IDscenario, IDpersonne, nom, description, date_debut, date_fin FROM scenarios ORDER BY date_debut DESC;"
        else:
            req = "SELECT IDscenario, IDpersonne, nom, description, date_debut, date_fin FROM scenarios WHERE IDpersonne=%d ORDER BY date_debut DESC;" % self.IDpersonne
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        dictScenarios = {}
        for IDscenario, IDpersonne, nom, description, date_debut, date_fin in listeDonnees:
            if IDpersonne in dictScenarios:
                dictScenarios[IDpersonne].append((IDscenario, nom, description, date_debut, date_fin))
            else:
                dictScenarios[IDpersonne] = [(IDscenario, nom, description, date_debut, date_fin)]
        return dictScenarios

    def GetDictPersonnes(self):
        DB = GestionDB.DB()
        req = "SELECT IDpersonne, nom, prenom, civilite FROM personnes;"
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        dict_personnes = {}
        for valeurs in listeDonnees:
            dict_personnes[valeurs[0]] = valeurs
        return dict_personnes

    def OnActivated(self, event):
        item = self.GetSelection()
        data = self.GetItemData(item)
        if data is not None and data < 100000:
            self.GetParent().Modifier()
        else:
            event.Skip()

    def OnContextMenu(self, event):
        item = event.GetItem()
        data = self.GetItemData(item)
        if data is None or data > 100000:
            return
        self.SelectItem(item, item)

        menuPop = UTILS_Adaptations.Menu()
        item = wx.MenuItem(menuPop, 10, _(u"Ajouter"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().OnBoutonAjouter, id=10)

        item = wx.MenuItem(menuPop, 20, _(u"Modifier"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().OnBoutonModifier, id=20)
        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().OnBoutonSupprimer, id=30)
        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, 40, _(u"Dupliquer"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().OnBoutonDupliquer, id=40)

        self.PopupMenu(menuPop)
        menuPop.Destroy()


class Dialog(wx.Dialog):
    def __init__(self, parent, title=""):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            name="frm_gestion_scenarios",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.panel_base = wx.Panel(self, -1)
        self.panel_base.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.panel_contenu = Panel(self.panel_base, IDpersonne=None)

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_fermer = CTRL_Bouton_image.CTRL(
            self.panel_base,
            id=wx.ID_CANCEL,
            texte=_(u"Fermer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"),
        )
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_fermer, self.bouton_fermer)

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des scénarios"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour fermer")))
        self.SetMinSize(_dip(self, 600, 420))
        self.SetSize(_dip(self, 980, 680))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.panel_contenu, 1, wx.EXPAND | wx.ALL, 10)

        sizer_boutons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_boutons.Add(self.bouton_aide, 0)
        sizer_boutons.AddStretchSpacer(1)
        sizer_boutons.Add(self.bouton_fermer, 0)
        sizer_base.Add(sizer_boutons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.panel_base.SetSizer(sizer_base)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(outer)
        self.Layout()
        self.CentreOnScreen()
        self.sizer_pages = sizer_base

    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lagestiondesscnarios")

    def Onbouton_fermer(self, event):
        self.EndModal(wx.ID_CANCEL)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, "")
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
