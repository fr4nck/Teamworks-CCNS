#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import sys
import Chemins
from Utils.UTILS_Traduction import _
import wx
import GestionDB
from Dlg import DLG_Config_classifications
from Dlg import DLG_Config_types_contrats
from wx.lib.mixins.listctrl import CheckListCtrlMixin
from Dlg import DLG_Config_champs_contrats
from Utils import UTILS_Adaptations


class Page(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)

        self.dictTypes = {}

        self.sizer_champs_staticbox = wx.StaticBox(self, -1, _(u"Champs personnalisés"))
        self.sizer_caract_staticbox = wx.StaticBox(self, -1, _(u"Caractéristiques générales"))
        self.label_titre = wx.StaticText(self, -1, _(u"Création d'un modèle de contrat"))
        self.label_intro = wx.StaticText(self, -1, _(u"Saisissez les caractéristiques générales du contrat :"))

        self.label_type = wx.StaticText(self, -1, "Type de contrat :")
        self.choice_type = wx.Choice(self, -1, choices=[])
        self.Importation_Type()
        self.bouton_type = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)

        self.label_class = wx.StaticText(self, -1, "Classification :")
        self.choice_class = wx.Choice(self, -1, choices=[])
        self.Importation_classifications()
        self.bouton_class = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)

        self.listCtrl_champs = ListCtrl_champs(self)
        self.bouton_champs = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonClassifications, self.bouton_class)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonType, self.bouton_type)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonChamps, self.bouton_champs)

        self.Importation()

    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.bouton_type.SetMinSize((20, 20))
        self.bouton_type.SetToolTip(wx.ToolTip("Cliquez ici pour ajouter, modifier ou supprimer des types de contrat"))
        self.bouton_class.SetMinSize((20, 20))
        self.bouton_class.SetToolTip(wx.ToolTip("Cliquez ici pour ajouter, modifier ou supprimer des classifications"))
        self.bouton_champs.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour créer, modifier ou supprimer des champs personnalisés.")))
        self.bouton_champs.SetMinSize((20, 20))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        sizer_champs = wx.StaticBoxSizer(self.sizer_champs_staticbox, wx.VERTICAL)
        grid_sizer_champs = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_boutons = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        sizer_caract = wx.StaticBoxSizer(self.sizer_caract_staticbox, wx.VERTICAL)
        grid_sizer_caract = wx.FlexGridSizer(rows=3, cols=3, vgap=5, hgap=5)

        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT, 20)

        grid_sizer_caract.Add(self.label_type, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_caract.Add(self.choice_type, 0, wx.EXPAND, 0)
        grid_sizer_caract.Add(self.bouton_type, 0, 0, 0)
        grid_sizer_caract.Add(self.label_class, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_caract.Add(self.choice_class, 0, wx.EXPAND, 0)
        grid_sizer_caract.Add(self.bouton_class, 0, 0, 0)
        grid_sizer_caract.AddGrowableCol(1)
        sizer_caract.Add(grid_sizer_caract, 1, wx.ALL | wx.EXPAND, 5)
        grid_sizer_base.Add(sizer_caract, 1, wx.LEFT | wx.EXPAND, 20)

        grid_sizer_champs.Add(self.listCtrl_champs, 1, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_champs, 0, 0, 0)
        grid_sizer_champs.Add(grid_sizer_boutons, 1, 0, 0)
        grid_sizer_champs.AddGrowableRow(0)
        grid_sizer_champs.AddGrowableCol(0)
        sizer_champs.Add(grid_sizer_champs, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_base.Add(sizer_champs, 1, wx.LEFT | wx.EXPAND, 20)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(3)

    def Importation(self):
        dictModeles = self.GetGrandParent().dictModeles
        self.SelectChoice(self.choice_type, data=dictModeles["IDtype"])
        self.SelectChoice(self.choice_class, data=dictModeles["IDclassification"])

    def OnBoutonChamps(self, event):
        dlg = DLG_Config_champs_contrats.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.MAJ_ListCtrl()

    def OnBoutonClassifications(self, event):
        dlg = DLG_Config_classifications.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.MAJ_choice_Class()

    def OnBoutonType(self, event):
        dlg = DLG_Config_types_contrats.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.MAJ_choice_Type()

    def MAJ_ListCtrl(self):
        self.listCtrl_champs.MAJListeCtrl()

    def MAJ_choice_Class(self):
        self.Importation_classifications()

    def Importation_classifications(self):
        controle = self.choice_class
        selection = controle.GetSelection()
        IDselection = controle.GetClientData(selection) if selection != -1 else None

        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT * FROM contrats_class ")
        liste = DB.ResultatReq()
        DB.Close()

        controle.Clear()
        for index, (key, valeur) in enumerate(liste):
            controle.Append(valeur, key)
            if IDselection == key:
                controle.SetSelection(index)

    def MAJ_choice_Type(self):
        self.Importation_Type()

    def Importation_Type(self):
        controle = self.choice_type
        selection = controle.GetSelection()
        IDselection = controle.GetClientData(selection) if selection != -1 else None

        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT * FROM contrats_types ")
        liste = DB.ResultatReq()
        DB.Close()

        controle.Clear()
        self.dictTypes = {}
        for index, (key, nom, nom_abrege, duree_indeterminee) in enumerate(liste):
            self.dictTypes[key] = duree_indeterminee
            controle.Append(nom, key)
            if IDselection == key:
                controle.SetSelection(index)

    def GetChoiceData(self, controle):
        selection = controle.GetSelection()
        return controle.GetClientData(selection) if selection != -1 else None

    def SelectChoice(self, controle, data):
        for index in range(controle.GetCount()):
            if controle.GetClientData(index) == data:
                controle.SetSelection(index)
                return

    def Validation(self):
        type_contrat = self.GetChoiceData(self.choice_type)
        classification = self.GetChoiceData(self.choice_class)

        if type_contrat is None:
            dlg = wx.MessageDialog(self, _(u"Vous devez sélectionner un type de contrat dans la liste proposée."), "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.choice_type.SetFocus()
            return False

        if classification is None:
            dlg = wx.MessageDialog(self, _(u"Vous devez sélectionner une classification dans la liste proposée."), "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.choice_class.SetFocus()
            return False

        dictModeles = self.GetGrandParent().dictModeles
        dictModeles["IDtype"] = type_contrat
        dictModeles["IDclassification"] = classification

        if len(self.listCtrl_champs.selections) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous n'avez sélectionné aucun champ. \n\nVoulez-vous tout de même continuer ?"),
                _(u"Vérification"),
                wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
            )
            if dlg.ShowModal() == wx.ID_NO:
                dlg.Destroy()
                return False
            dlg.Destroy()

        self.GetGrandParent().page2.MAJ_panelDefilant()
        return True


class ListCtrl_champs(wx.ListCtrl, CheckListCtrlMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_NO_HEADER)
        CheckListCtrlMixin.__init__(self)
        self.EnableCheckBoxes(True)
        self.parent = parent

        listeIDchamps = list(self.GetGrandParent().GetParent().dictChamps.keys())
        self.selections = listeIDchamps if len(listeIDchamps) != 0 else []

        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def Remplissage(self):
        self.dictChamps = self.Import_Donnees()
        self.ClearAll()
        self.InsertColumn(0, "Nom")

        for key, valeurs in self.dictChamps.items():
            index = self.InsertItem(self.GetItemCount(), valeurs[1])
            self.SetItemData(index, key)
            if key in self.selections:
                self.CheckItem(index)

        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.SortItems(self.columnSorter)

    def MAJListeCtrl(self):
        self.ClearAll()
        self.Remplissage()

    def Import_Donnees(self):
        req = """
            SELECT IDchamp, nom, description, mot_cle, defaut, exemple
            FROM contrats_champs
            ORDER BY nom;
        """
        DB = GestionDB.DB()
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()

        dictChamps = {}
        for ID, nom, description, mot_cle, defaut, exemple in listeDonnees:
            dictChamps[ID] = (ID, nom, description, mot_cle, defaut, exemple)
        return dictChamps

    def columnSorter(self, key1, key2):
        item1 = self.dictChamps[key1][1]
        item2 = self.dictChamps[key2][1]
        if item1 == item2:
            return 0
        if item1 < item2:
            return -1
        return 1

    def OnItemActivated(self, evt):
        self.ToggleItem(evt.Index)

    def OnCheckItem(self, index, flag):
        ID = self.GetItemData(index)
        if flag:
            if ID not in self.selections:
                self.selections.append(ID)
        elif ID in self.selections:
            self.selections.remove(ID)

    def OnContextMenu(self, event):
        index = self.GetFirstSelected()
        mode = "selected" if index == -1 else "deselected"

        menuPop = UTILS_Adaptations.Menu()

        item = wx.MenuItem(menuPop, 10, _(u"Créer un nouveau champ"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)

        if mode == "deselected":
            menuPop.AppendSeparator()

            item = wx.MenuItem(menuPop, 20, _(u"Modifier"))
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG))
            menuPop.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)

            item = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG))
            menuPop.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.parent.OnBoutonAjouter(None)

    def Menu_Modifier(self, event):
        self.parent.OnBoutonModifier(None)

    def Menu_Supprimer(self, event):
        self.parent.OnBoutonSupprimer(None)
