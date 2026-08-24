#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import six
import wx
import wx.lib.mixins.listctrl as listmix

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Texte
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_Styles
import GestionDB
import FonctionsPerso


class Panel(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = CTRL_Texte.H2(self, _(u"Situations sociales"))
        self.label_introduction = CTRL_Texte.BodySecondary(
            self,
            _(u"Ajoutez, modifiez ou supprimez les types de situations utilisés dans les fiches personnes. Exemples : étudiant, retraité, employé."),
        )

        self.listCtrl_Situations = ListCtrl(self)
        self.listCtrl_Situations.SetBackgroundColour(
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

    def _bouton(self, texte, image):
        return CTRL_Bouton_image.CTRL(
            self,
            texte=texte,
            cheminImage=Chemins.GetStaticPath("Images/32x32/%s" % image),
        )

    def __set_properties(self):
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Créer un nouveau type de situation sociale")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Modifier le type de situation sociale sélectionné")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Supprimer le type de situation sociale sélectionné")))
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
        sizer.Add(
            self.listCtrl_Situations,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM,
            padding,
        )
        self.SetSizer(sizer)

    def OnBoutonAjouter(self, event):
        self.Ajouter()

    def Ajouter(self):
        dlg = wx.TextEntryDialog(
            self,
            _(u"Saisissez le nom du nouveau type de situation sociale :"),
            _(u"Saisie d'un nouveau type de situation sociale"),
            u"",
        )
        if dlg.ShowModal() == wx.ID_OK:
            varSituation = dlg.GetValue()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        if varSituation == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Le nom que vous avez saisi n'est pas valide."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        DB = GestionDB.DB()
        DB.ReqInsert("situations", [("situation", varSituation)])
        DB.Close()
        self.listCtrl_Situations.MAJListeCtrl()

    def OnBoutonModifier(self, event):
        self.Modifier()

    def Modifier(self):
        index = self.listCtrl_Situations.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un type de situation sociale à modifier dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        nbreTitulaires = int(self.listCtrl_Situations.GetItem(index, 2).GetText())
        if nbreTitulaires != 0:
            message = (
                _(u"Avertissement : Ce type de situation sociale a déjà été attribué a ")
                + str(nbreTitulaires)
                + _(u" personne(s). Toute modification sera donc répercutée en cascade sur toutes les fiches des personnes à qui cette situation sociale a été attribuée. \n\nSouhaitez-vous quand même modifier ce type de situation ?")
            )
            dlg = wx.MessageDialog(
                self,
                message,
                "Information",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION,
            )
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse == wx.ID_NO:
                return

        varIDsituation = int(self.listCtrl_Situations.GetItem(index, 0).GetText())
        varNomSituation = self.listCtrl_Situations.GetItem(index, 1).GetText()
        dlg = wx.TextEntryDialog(
            self,
            _(u"Saisissez le nom du nouveau type de situation sociale :"),
            _(u"Saisie d'un nouveau type de situation sociale"),
            varNomSituation,
        )
        if dlg.ShowModal() == wx.ID_OK:
            varNomSituation = dlg.GetValue()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        if varNomSituation == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Le nom que vous avez saisi n'est pas valide."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        DB = GestionDB.DB()
        DB.ReqMAJ(
            "situations",
            [("situation", varNomSituation)],
            "IDsituation",
            varIDsituation,
        )
        DB.Close()
        self.listCtrl_Situations.MAJListeCtrl()

    def MAJpanel(self):
        self.listCtrl_Situations.MAJListeCtrl()

    def OnBoutonSupprimer(self, event):
        self.Supprimer()

    def Supprimer(self):
        index = self.listCtrl_Situations.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un type de situation sociale à supprimer dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        nbreTitulaires = int(self.listCtrl_Situations.GetItem(index, 2).GetText())
        if nbreTitulaires != 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Pour des raisons de sécurité des données, vous ne pouvez pas supprimer un type de situation sociale qui a déjà été attribué à des personnes.\n\nSi vous voulez vraiment le supprimer, vous devez d'abord supprimer cette situation sociale sur chaque fiche individuelle concernée."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        IDsituation = int(self.listCtrl_Situations.GetItem(index, 0).GetText())
        NomSituation = self.listCtrl_Situations.GetItem(index, 1).GetText()
        txtMessage = six.text_type(
            _(u"Voulez-vous vraiment supprimer ce type de situation sociale ? \n\n> ")
            + NomSituation
        )
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
        DB.ReqDEL("situations", "IDsituation", IDsituation)
        DB.Close()
        self.listCtrl_Situations.MAJListeCtrl()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lestypesdesituations")


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
        self.nbreColonnes = 3
        self._ajustement_en_cours = False

        icon_size = UTILS_Styles.GetIconSize("small")[0]
        self.il = wx.ImageList(icon_size, icon_size)
        self.imgTriAz = self.il.Add(self._bitmap_tri("Tri_az.png", icon_size))
        self.imgTriZa = self.il.Add(self._bitmap_tri("Tri_za.png", icon_size))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))

        if self.GetGrandParent().GetName() != "treebook_configuration":
            self.Remplissage()

        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _bitmap_tri(self, image, taille):
        bitmap = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s" % image), wx.BITMAP_TYPE_PNG)
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            bitmap = wx.Bitmap(bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH))
        return bitmap

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        if self._ajustement_en_cours or self.GetColumnCount() < 3:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return
        marge = UTILS_Styles.GetSpacing("sm")
        compte = max(UTILS_Styles.Scale(110), self.GetTextExtent(_(u"Nb titulaires"))[0] + 2 * marge)
        nom = max(UTILS_Styles.Scale(220), largeur - compte - 2 * marge)
        self._ajustement_en_cours = True
        try:
            self.SetColumnWidth(0, 0)
            self.SetColumnWidth(1, nom)
            self.SetColumnWidth(2, compte)
        finally:
            self._ajustement_en_cours = False

    def Remplissage(self):
        self.Importation()
        self.ClearAll()
        self.InsertColumn(0, _(u"ID"))
        self.InsertColumn(1, _(u"Nom de la situation sociale"))
        self.InsertColumn(2, _(u"Nb titulaires"), wx.LIST_FORMAT_RIGHT)

        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(1, 1)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        wx.CallAfter(self.AjusterColonnes)

    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT situations.IDsituation, situations.situation, Count(personnes.IDpersonne) AS CompteDeIDsituation
        FROM situations LEFT JOIN personnes ON situations.IDsituation = personnes.IDsituation
        GROUP BY situations.IDsituation, situations.situation %s;
        """ % self.criteres
        DB.ExecuterReq(req)
        listeSituations = DB.ResultatReq()
        DB.Close()
        self.nbreLignes = len(listeSituations)
        self.donnees = self.listeEnDict(listeSituations)

    def MAJListeCtrl(self):
        self.Remplissage()

    def listeEnDict(self, liste):
        return {index + 1: ligne for index, ligne in enumerate(liste)}

    def OnItemActivated(self, event):
        self.parent.Modifier()

    def getColumnText(self, index, col):
        return self.GetItem(index, col).GetText()

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        return six.text_type(self.itemDataMap[index][col])

    def OnGetItemImage(self, item):
        return -1

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
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.panel_base = wx.Panel(self, -1)
        self.panel_base.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.panel_contenu = Panel(self.panel_base)
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
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_fermer)

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des types de situations"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_(u"Fermer")))
        UTILS_Styles.ApplyWindowProfile(self, "standard")

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.panel_contenu, 1, wx.EXPAND)

        boutons = wx.BoxSizer(wx.HORIZONTAL)
        boutons.Add(self.bouton_aide, 0)
        boutons.AddStretchSpacer(1)
        boutons.Add(self.bouton_fermer, 0)

        contenu.Add(boutons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, padding)
        self.panel_base.SetSizer(contenu)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lestypesdesituations")

    def Onbouton_annuler(self, event):
        self.EndModal(wx.ID_CANCEL)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
