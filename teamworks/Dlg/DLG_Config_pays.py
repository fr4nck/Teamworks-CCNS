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
import six
import wx.lib.mixins.listctrl as listmix

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Texte
from Dlg import DLG_Saisie_pays
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_Styles
import GestionDB
import FonctionsPerso


class Panel(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(
            self,
            parent,
            ID,
            style=wx.TAB_TRAVERSAL,
            name="panel_config_pays",
        )
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = CTRL_Texte.H2(self, _(u"Pays et nationalités"))
        self.label_introduction = CTRL_Texte.BodySecondary(
            self,
            _(u"Ajoutez, modifiez ou supprimez les pays et les nationalités correspondantes."),
        )
        self.listCtrl = ListCtrl(self)
        self.listCtrl.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )

        self.bouton_ajouter = self._bouton(_(u"Ajouter"), "Ajouter.png")
        self.bouton_modifier = self._bouton(_(u"Modifier"), "Modifier.png")
        self.bouton_supprimer = self._bouton(_(u"Supprimer"), "Supprimer.png")
        self.bouton_aide = self._bouton(_(u"Aide"), "Aide.png")
        if parent.GetName() != "treebook_configuration":
            self.bouton_aide.Hide()

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)

        self.bouton_modifier.Enable(False)
        self.bouton_supprimer.Enable(False)

    def _bouton(self, texte, image):
        return CTRL_Bouton_image.CTRL(
            self,
            texte=texte,
            cheminImage=Chemins.GetStaticPath("Images/32x32/%s" % image),
        )

    def __set_properties(self):
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Créer un nouveau pays")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Modifier le pays sélectionné")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Supprimer le pays sélectionné")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(self.label_introduction, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, gap)

        actions = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (
            self.bouton_ajouter,
            self.bouton_modifier,
            self.bouton_supprimer,
            self.bouton_aide,
        ):
            actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, section_gap)
        sizer.Add(self.listCtrl, 1, wx.EXPAND | wx.ALL, padding)
        self.SetSizer(sizer)

    def OnBoutonAjouter(self, event):
        self.Ajouter()

    def Ajouter(self):
        dlg = DLG_Saisie_pays.Dialog(self, "", IDpays=0)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonModifier(self, event):
        self.Modifier()

    def Modifier(self):
        index = self.listCtrl.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un pays à modifier dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        ID = int(self.listCtrl.GetItem(index, 0).GetText())
        dlg = DLG_Saisie_pays.Dialog(self, "", IDpays=ID)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonSupprimer(self, event):
        self.Supprimer()

    def Supprimer(self):
        index = self.listCtrl.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un pays à supprimer dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        nbreTitulaires = int(self.listCtrl.GetItem(index, 4).GetText())
        if nbreTitulaires != 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Pour des raisons de sécurité des données, vous ne pouvez pas supprimer un pays qui a déjà été attribué à des personnes.\n\nSi vous voulez vraiment le supprimer, vous devez d'abord supprimer ce pays sur chaque fiche individuelle concernée."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        ID = int(self.listCtrl.GetItem(index, 0).GetText())
        if ID <= 230:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous ne pouvez pas supprimer un pays pré-enregistré."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        Nom = self.listCtrl.GetItem(index, 2).GetText()
        txtMessage = six.text_type(_(u"Voulez-vous vraiment supprimer ce pays ? \n\n> ") + Nom)
        dlgConfirm = wx.MessageDialog(
            self,
            txtMessage,
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return

        DB = GestionDB.DB()
        DB.ReqDEL("pays", "IDpays", ID)
        DB.Close()
        self.listCtrl.MAJListeCtrl()

    def MAJ_ListCtrl(self):
        self.listCtrl.MAJListeCtrl()

    def MAJpanel(self):
        self.listCtrl.MAJListeCtrl()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lespaysetnationalits")


class ListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES | wx.BORDER_NONE,
        )
        self.criteres = ""
        self.parent = parent
        self.selection = None
        self.nbreColonnes = 5
        self._ajustement_en_cours = False
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))

        if self.GetGrandParent().GetName() != "treebook_configuration":
            self.Remplissage()

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _bitmap_scaled(self, path, taille):
        bitmap = wx.Bitmap(path, wx.BITMAP_TYPE_PNG)
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            bitmap = wx.Bitmap(bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH))
        return bitmap

    def InitImageList(self):
        taille = UTILS_Styles.GetIconSize("medium")[0]
        self.il = wx.ImageList(taille, taille)
        self.imgTriAz = self.il.Add(
            self._bitmap_scaled(Chemins.GetStaticPath("Images/22x22/Tri_az.png"), taille)
        )
        self.imgTriZa = self.il.Add(
            self._bitmap_scaled(Chemins.GetStaticPath("Images/22x22/Tri_za.png"), taille)
        )
        self.imgDrapeauAutre = self.il.Add(
            self._bitmap_scaled(Chemins.GetStaticPath("Images/Drapeaux/autre.png"), taille)
        )
        for ID, code_drapeau in self.Importation_drapeaux():
            setattr(
                self,
                "imgDrapeau%s" % ID,
                self.il.Add(
                    self._bitmap_scaled(
                        Chemins.GetStaticPath("Images/Drapeaux/%s.png" % code_drapeau),
                        taille,
                    )
                ),
            )
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        if self._ajustement_en_cours or self.GetColumnCount() < 5:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return
        gap = UTILS_Styles.GetSpacing("sm")
        drapeau = UTILS_Styles.GetIconSize("medium")[0] + 2 * gap
        titulaires = max(UTILS_Styles.Scale(105), self.GetTextExtent(_(u"Nb titulaires"))[0] + 2 * gap)
        disponible = max(UTILS_Styles.Scale(360), largeur - drapeau - titulaires - 2 * gap)
        nom = max(UTILS_Styles.Scale(180), int(disponible * 0.56))
        nationalite = max(UTILS_Styles.Scale(150), disponible - nom)

        self._ajustement_en_cours = True
        try:
            self.SetColumnWidth(0, drapeau)
            self.SetColumnWidth(1, 0)
            self.SetColumnWidth(2, nom)
            self.SetColumnWidth(3, nationalite)
            self.SetColumnWidth(4, titulaires)
        finally:
            self._ajustement_en_cours = False

    def Remplissage(self):
        self.InitImageList()
        self.dictNbTitulaires = self.GetNbTitulaires()
        self.Importation()

        self.ClearAll()
        self.InsertColumn(0, u"")
        self.InsertColumn(1, _(u"Code drapeau"))
        self.InsertColumn(2, _(u"Nom"))
        self.InsertColumn(3, _(u"Nationalité"))
        self.InsertColumn(4, _(u"Nb titulaires"), wx.LIST_FORMAT_RIGHT)

        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(2, 1)
        wx.CallAfter(self.AjusterColonnes)

    def OnItemSelected(self, event):
        self.parent.bouton_modifier.Enable(True)
        self.parent.bouton_supprimer.Enable(True)
        if self.GetFirstSelected() == -1:
            return False
        index = self.GetFirstSelected()
        self.selection = int(self.getColumnText(index, 0))

    def OnItemDeselected(self, event):
        self.parent.bouton_modifier.Enable(False)
        self.parent.bouton_supprimer.Enable(False)
        self.selection = None

    def SetSelection(self, IDpays=0):
        self.selection = IDpays
        for key, valeurs in self.donnees.items():
            if valeurs[0] == IDpays:
                self.Focus(key - 1)
                self.Select(key - 1)
                return

    def Importation(self):
        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT IDpays, code_drapeau, nom, nationalite FROM pays ORDER BY nom;")
        liste = DB.ResultatReq()
        DB.Close()
        self.nbreLignes = len(liste)
        self.donnees = self.listeEnDict(liste)

    def Importation_drapeaux(self):
        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT IDpays, code_drapeau FROM pays ORDER BY nom;")
        listeDrapeaux = DB.ResultatReq()
        DB.Close()
        return listeDrapeaux

    def GetNbTitulaires(self):
        DB = GestionDB.DB()
        DB.ExecuterReq(
            """SELECT pays_naiss, Count(IDpersonne) AS CompteDeIDpersonne
            FROM personnes
            GROUP BY pays_naiss;"""
        )
        listeNbTitulaires = DB.ResultatReq()
        DB.Close()
        return {IDpays: nbrePersonne for IDpays, nbrePersonne in listeNbTitulaires}

    def MAJListeCtrl(self):
        self.Remplissage()

    def listeEnDict(self, liste):
        dictio = {}
        for index, ligne in enumerate(liste, 1):
            ligne = list(ligne)
            ID = ligne[0]
            ligne.append(self.dictNbTitulaires.get(ID, 0))
            dictio[index] = ligne
        return dictio

    def OnItemActivated(self, event):
        self.parent.Modifier()

    def getColumnText(self, index, col):
        return self.GetItem(index, col).GetText()

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        return six.text_type(self.itemDataMap[index][col])

    def OnGetItemImage(self, item):
        index = self.itemIndexMap[item]
        IDvaleur = self.itemDataMap[index][0]
        return getattr(self, "imgDrapeau%s" % IDvaleur, self.imgDrapeauAutre)

    def OnGetItemAttr(self, item):
        return None

    def SortItems(self, sorter=FonctionsPerso.cmp):
        items = list(self.itemDataMap.keys())
        self.itemIndexMap = FonctionsPerso.SortItems(items, sorter)
        self.Refresh()

    def GetListCtrl(self):
        return self

    def GetSortImages(self):
        return (self.imgTriAz, self.imgTriZa)

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False

        menuPop = UTILS_Adaptations.Menu()
        item = wx.MenuItem(menuPop, 10, _(u"Ajouter"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)
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
        self.parent.Ajouter()

    def Menu_Modifier(self, event):
        self.parent.Modifier()

    def Menu_Supprimer(self, event):
        self.parent.Supprimer()


class Dialog(wx.Dialog):
    def __init__(self, parent, title="", IDpays=0, saisie=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.saisie = saisie
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.panel_base = wx.Panel(self, -1)
        self.panel_base.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.panel_contenu = Panel(self.panel_base)
        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self.panel_base,
            id=wx.ID_OK,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self.panel_base,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)

        if IDpays != 0:
            self.panel_contenu.listCtrl.SetSelection(IDpays=IDpays)
        if self.saisie == "FicheIndiv_pays_naiss":
            self.panel_contenu.label_introduction.SetLabel(_(u"Sélectionnez un pays de naissance dans la liste."))
        if self.saisie == "FicheIndiv_nationalite":
            self.panel_contenu.label_introduction.SetLabel(_(u"Sélectionnez une nationalité dans la liste."))

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des pays"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Valider la sélection")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Annuler et fermer")))
        UTILS_Styles.ApplyWindowProfile(self, "standard")

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        sizer_panel = wx.BoxSizer(wx.VERTICAL)
        sizer_panel.Add(self.panel_contenu, 1, wx.EXPAND)

        boutons = wx.BoxSizer(wx.HORIZONTAL)
        boutons.Add(self.bouton_aide, 0)
        boutons.AddStretchSpacer(1)
        boutons.Add(self.bouton_ok, 0, wx.RIGHT, gap)
        boutons.Add(self.bouton_annuler, 0)
        sizer_panel.Add(boutons, 0, wx.EXPAND | wx.ALL, padding)
        self.panel_base.SetSizer(sizer_panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lespaysetnationalits")

    def Onbouton_annuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def Onbouton_ok(self, event):
        if self.saisie == "FicheIndiv_nationalite" or self.saisie == "FicheIndiv_nationalite":
            if self.panel_contenu.listCtrl.selection is None:
                dlg = wx.MessageDialog(
                    self,
                    _(u"Vous devez sélectionner un pays dans la liste."),
                    "Erreur",
                    wx.OK,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return

        if self.saisie == "FicheIndiv_nationalite":
            listCtrl = self.panel_contenu.listCtrl
            index = listCtrl.GetFirstSelected()
            nationalite = listCtrl.getColumnText(index, 3)
            if nationalite == "":
                dlg = wx.MessageDialog(
                    self,
                    _(u"Vous avez sélectionné un pays dont la nationalité n'a pas encore été précisée. \nCliquez sur le bouton 'Modifier' pour saisir le nom de la nationalité."),
                    "Erreur",
                    wx.OK,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return

        if self.saisie == "FicheIndiv_pays_naiss":
            self.parent.SetPaysNaiss(IDpays=self.panel_contenu.listCtrl.selection)
        if self.saisie == "FicheIndiv_nationalite":
            self.parent.SetNationalite(IDpays=self.panel_contenu.listCtrl.selection)
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
