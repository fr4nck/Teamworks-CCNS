#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import unicodedata
import sqlite3
import Chemins
from Utils.UTILS_Traduction import _
import wx
import six
import wx.lib.masked as masked
import wx.lib.mixins.listctrl as listmix

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_Phonex
from Utils import UTILS_Styles
import FonctionsPerso


def NormaliseRecherche(word):
    texte = unicodedata.normalize("NFKD", six.text_type(word))
    return "".join(
        caractere for caractere in texte if not unicodedata.combining(caractere)
    ).upper()


def PhonexPerso(word):
    return UTILS_Phonex.phonex(NormaliseRecherche(word))


class Dialog(wx.Dialog):
    def __init__(
        self,
        parent,
        title,
        exportCP=None,
        exportVille=None,
        exportChamp=None,
    ):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )
        self.parent = parent
        self.exportCP = exportCP
        self.exportVille = exportVille
        self.exportChamp = exportChamp
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.titre = CTRL_Texte.H1(self, _(u"Gestion des villes"))
        self.label_Intro = CTRL_Texte.BodySecondary(
            self,
            _(u"Recherchez une ville ou un code postal dans la base de données française, puis insérez le résultat dans la fiche."),
        )

        self.section_recherche = CTRL_Section.Section(
            self, titre=_(u"Recherche"), niveau=2
        )
        panel_recherche = self.section_recherche.GetContentPanel()
        self.label_Recherche1 = CTRL_Texte.Label(
            panel_recherche, _(u"Ville ou code postal")
        )
        self.text_recherche_ville = wx.TextCtrl(
            panel_recherche, -1, "", style=wx.TE_PROCESS_ENTER
        )
        self.radio_box_recherche = wx.RadioBox(
            panel_recherche,
            -1,
            _(u"Type de recherche"),
            choices=[_(u"Une partie du nom"), _(u"Recherche phonétique")],
            majorDimension=2,
            style=wx.RA_SPECIFY_COLS,
        )
        self.bouton_Rechercher = CTRL_Bouton_image.CTRL(
            panel_recherche,
            texte=_(u"Rechercher"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Rechercher.png"),
        )
        self.bouton_AfficherTout = CTRL_Bouton_image.CTRL(
            panel_recherche,
            texte=_(u"Afficher tout"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Actualiser.png"),
        )
        self.bouton_AfficherTout.Hide()

        listeChamps = [
            ("cp", _(u"Code postal"), 110, True),
            ("ville", _(u"Nom de la ville"), 320, True),
        ]
        self.list_ctrl_1 = VirtualList(
            panel_recherche, "villes", listeChamps
        )
        self.list_ctrl_1.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )

        self.section_manuel = CTRL_Section.Section(
            self,
            titre=_(u"Saisie manuelle"),
            description=_(u"Utilisez cette zone uniquement si la ville n'est pas présente dans la base."),
            niveau=2,
        )
        panel_manuel = self.section_manuel.GetContentPanel()
        self.label_SaisieCode = CTRL_Texte.Label(
            panel_manuel, _(u"Code postal")
        )
        self.text_SaisieCode = masked.TextCtrl(
            panel_manuel, -1, "", style=wx.TE_CENTRE, mask="#####"
        )
        self.label_SaisieVille = CTRL_Texte.Label(
            panel_manuel, _(u"Nom de la ville")
        )
        self.text_SaisieVille = wx.TextCtrl(panel_manuel, -1, "")

        self.bouton_Aide = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_Ok = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_Annuler = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )

        self.__set_properties()
        self.__do_layout(panel_recherche, panel_manuel)

        self.bouton_Rechercher.Bind(wx.EVT_BUTTON, self.OnBoutonRechercher)
        self.text_recherche_ville.Bind(wx.EVT_TEXT_ENTER, self.OnBoutonRechercher)
        self.bouton_Ok.Bind(wx.EVT_BUTTON, self.OnBoutonOk)
        self.bouton_Annuler.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler)
        self.bouton_Aide.Bind(wx.EVT_BUTTON, self.OnBoutonAide)
        self.bouton_AfficherTout.Bind(wx.EVT_BUTTON, self.OnAfficherTout)

        if self.exportCP is None and self.exportVille is None:
            self.section_manuel.Hide()
            self.Layout()

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des villes"))
        self.text_recherche_ville.SetToolTip(
            wx.ToolTip(_(u"Saisissez un nom de ville ou un code postal"))
        )
        self.bouton_Rechercher.SetToolTip(
            wx.ToolTip(_(u"Lancer la recherche"))
        )
        self.bouton_AfficherTout.SetToolTip(
            wx.ToolTip(_(u"Réafficher la liste complète"))
        )
        self.radio_box_recherche.SetToolTip(
            wx.ToolTip(_(u"Sélectionnez un type de recherche"))
        )
        self.radio_box_recherche.SetSelection(0)
        self.text_SaisieCode.SetMinSize((UTILS_Styles.Scale(100), -1))
        self.text_SaisieCode.SetToolTip(
            wx.ToolTip(_(u"Saisissez un code postal"))
        )
        self.text_SaisieVille.SetToolTip(
            wx.ToolTip(_(u"Saisissez un nom de ville"))
        )
        self.bouton_Aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_Ok.SetToolTip(wx.ToolTip(_(u"Valider et fermer")))
        self.bouton_Annuler.SetToolTip(
            wx.ToolTip(_(u"Annuler et fermer"))
        )
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def __do_layout(self, panel_recherche, panel_manuel):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        xs = UTILS_Styles.GetSpacing("xs")

        recherche = wx.BoxSizer(wx.VERTICAL)
        recherche.Add(self.label_Recherche1, 0, wx.BOTTOM, xs)
        ligne_recherche = wx.BoxSizer(wx.HORIZONTAL)
        ligne_recherche.Add(self.text_recherche_ville, 1, wx.RIGHT, gap)
        ligne_recherche.Add(self.bouton_Rechercher, 0, wx.RIGHT, toolbar_gap)
        ligne_recherche.Add(self.bouton_AfficherTout, 0)
        recherche.Add(ligne_recherche, 0, wx.EXPAND | wx.BOTTOM, gap)
        recherche.Add(self.radio_box_recherche, 0, wx.EXPAND | wx.BOTTOM, gap)
        recherche.Add(self.list_ctrl_1, 1, wx.EXPAND)
        panel_recherche.SetSizer(recherche)

        manuel = wx.BoxSizer(wx.HORIZONTAL)
        bloc_cp = wx.BoxSizer(wx.VERTICAL)
        bloc_cp.Add(self.label_SaisieCode, 0, wx.BOTTOM, xs)
        bloc_cp.Add(self.text_SaisieCode, 0)
        manuel.Add(bloc_cp, 0, wx.RIGHT, gap)
        bloc_ville = wx.BoxSizer(wx.VERTICAL)
        bloc_ville.Add(self.label_SaisieVille, 0, wx.BOTTOM, xs)
        bloc_ville.Add(self.text_SaisieVille, 0, wx.EXPAND)
        manuel.Add(bloc_ville, 1, wx.EXPAND)
        panel_manuel.SetSizer(manuel)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_Aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_Ok, 0, wx.RIGHT, toolbar_gap)
        actions.Add(self.bouton_Annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, page_gap)
        sizer.Add(self.label_Intro, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, gap)
        sizer.Add(
            self.section_recherche,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            page_gap,
        )
        sizer.Add(
            self.section_manuel,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            section_gap,
        )
        sizer.Add(actions, 0, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)
        self.Layout()

    def OnBoutonRechercher(self, event):
        textRecherche = self.text_recherche_ville.GetValue()
        if self.radio_box_recherche.GetSelection() == 0:
            resultats = self.list_ctrl_1.RechercheBase(textRecherche)
        else:
            resultats = self.list_ctrl_1.RechercheSoundex(textRecherche)

        if textRecherche == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord saisir un nom de ville ou un code postal dans le champ de recherche."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.bouton_AfficherTout.Show()
            self.Layout()
            if resultats is False:
                dlg = wx.MessageDialog(
                    self,
                    _(u"Aucun résultat n'a été trouvé pour votre recherche"),
                    "Information",
                    wx.OK | wx.ICON_INFORMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
        event.Skip()

    def OnAfficherTout(self, event):
        self.bouton_AfficherTout.Hide()
        self.list_ctrl_1.comAfficherTout()
        self.Layout()
        event.Skip()

    def OnBoutonOk(self, event):
        if (
            self.text_SaisieCode.GetValue().strip() != ""
            or self.text_SaisieVille.GetValue().strip() != ""
        ):
            if self.ExportManuelVille() is True:
                self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_OK)

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Ladresse")

    def ExportManuelVille(self):
        code = self.text_SaisieCode.GetValue()
        ville = self.text_SaisieVille.GetValue()
        if code.strip() == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous avez saisi un nom de ville. Vous devez également saisir un code postal pour exporter cette ville"),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False
        if ville.strip() == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous avez saisi un code postal. Vous devez également saisir un nom de ville pour exporter cette ville"),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        self.parent.autoComplete = False
        if self.exportCP == "text_cp_naiss" and self.exportVille == "text_ville_naiss":
            self.parent.text_cp_naiss.SetValue(code)
            self.parent.text_ville_naiss.SetValue(ville.upper())
        elif self.exportCP == "text_cp" and self.exportVille == "text_ville":
            self.parent.text_cp.SetValue(code)
            self.parent.text_ville.SetValue(ville.upper())
        self.parent.autoComplete = True
        return True

    def ExportListeVille(self, code, ville):
        self.parent.autoComplete = False
        if self.exportCP == "text_cp_naiss" and self.exportVille == "text_ville_naiss":
            self.parent.text_cp_naiss.SetValue(str(code))
            self.parent.text_ville_naiss.SetValue(ville.upper())
        elif self.exportCP == "text_cp" and self.exportVille == "text_ville":
            self.parent.text_cp.SetValue(str(code))
            self.parent.text_ville.SetValue(ville.upper())
        self.parent.autoComplete = True

        dlg = wx.MessageDialog(
            self,
            _(u"La ville ") + ville + _(u" a bien été importée dans la fiche individuelle."),
            "Information",
            wx.OK | wx.ICON_INFORMATION,
        )
        dlg.ShowModal()
        dlg.Destroy()


class VirtualList(wx.ListCtrl, listmix.ColumnSorterMixin):
    def __init__(self, parent, nomTable, listeChamps):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES | wx.BORDER_NONE,
        )
        self.nomTable = nomTable
        self.listeChamps = listeChamps
        self.criteres = ""
        self.parametres_criteres = ()
        self.parent = parent
        self._ajustement_en_cours = False
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )

        taille = UTILS_Styles.GetIconSize("small")[0]
        self.il = wx.ImageList(taille, taille)
        self.imgTriAz = self.il.Add(self._bitmap("Tri_az.png", taille))
        self.imgTriZa = self.il.Add(self._bitmap("Tri_za.png", taille))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        self.CreationListeColonnes()
        self.InitListCtrl()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _bitmap(self, nom, taille):
        bitmap = wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/%s" % nom), wx.BITMAP_TYPE_PNG
        )
        if bitmap.IsOk() and (
            bitmap.GetWidth() != taille or bitmap.GetHeight() != taille
        ):
            bitmap = wx.Bitmap(
                bitmap.ConvertToImage().Scale(
                    taille, taille, wx.IMAGE_QUALITY_HIGH
                )
            )
        return bitmap

    def InitListCtrl(self):
        self.ImportationDonnees(self.nomTable, self.listeChamps)
        self.ClearAll()
        for index, colonne in enumerate(self.listeColonnes):
            for champ in self.listeChamps:
                if colonne == champ[0]:
                    self.InsertColumn(index, champ[1])
                    break
        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(1, 1)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        wx.CallAfter(self.AjusterColonnes)

    def CreationListeColonnes(self):
        self.listeColonnes = [champ[0] for champ in self.listeChamps if champ[3]]

    def ImportationDonnees(self, nomTable, listeChamps):
        champs = ", ".join(self.listeColonnes)
        con = sqlite3.connect(Chemins.GetStaticPath("Databases/Villes.db3"))
        con.create_function("phonex", 1, PhonexPerso)
        cur = con.cursor()
        cur.execute(
            "SELECT %s FROM %s %s" % (champs, nomTable, self.criteres),
            self.parametres_criteres,
        )
        listeValeurs = cur.fetchall()
        con.close()
        self.nbreColonnes = len(self.listeColonnes)
        self.nbreLignes = len(listeValeurs)
        self.donnees = self.listeEnDict(listeValeurs)

    def MAJListeCtrl(self):
        self.InitListCtrl()

    def listeEnDict(self, liste):
        return {index + 1: ligne for index, ligne in enumerate(liste)}

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        if self._ajustement_en_cours or self.GetColumnCount() < 2:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return
        cp = max(UTILS_Styles.Scale(120), int(largeur * 0.25))
        ville = max(UTILS_Styles.Scale(240), largeur - cp - UTILS_Styles.GetSpacing("xs"))
        self._ajustement_en_cours = True
        try:
            self.SetColumnWidth(0, cp)
            self.SetColumnWidth(1, ville)
        finally:
            self._ajustement_en_cours = False

    def OnColClick(self, event):
        event.Skip()

    def OnItemSelected(self, event):
        self.currentItem = event.Index
        event.Skip()

    def OnItemActivated(self, event):
        self.currentItem = event.Index
        if self.GetGrandParent().exportCP is not None:
            self.GetGrandParent().ExportListeVille(
                self.getColumnText(self.currentItem, 0),
                self.getColumnText(self.currentItem, 1),
            )
        event.Skip()

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

    def comAfficherTout(self):
        self.criteres = ""
        self.parametres_criteres = ()
        self.MAJListeCtrl()

    def RechercheBase(self, textRecherche):
        textRecherche = NormaliseRecherche(textRecherche)
        if textRecherche != "":
            strCriteres = "WHERE "
            for champ in self.listeColonnes:
                strCriteres += champ + " like '%" + textRecherche + "%' or "
            self.criteres = strCriteres[:-4]
            self.parametres_criteres = ()
            self.MAJListeCtrl()
        return self.GetItemCount() != 0

    def RechercheSoundex(self, textRecherche):
        textRecherche = NormaliseRecherche(textRecherche)
        if textRecherche != "":
            self.criteres = "WHERE phonex(ville)=phonex(?)"
            self.parametres_criteres = (textRecherche,)
            self.MAJListeCtrl()
        return self.GetItemCount() != 0

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False
        index = self.GetFirstSelected()
        self.selection = (
            int(self.getColumnText(index, 0)),
            self.getColumnText(index, 1),
        )
        menuPop = UTILS_Adaptations.Menu()
        item = wx.MenuItem(
            menuPop,
            10,
            _(u"Insérer cette ville dans la fiche individuelle"),
        )
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Menu_Inserer, id=10)
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Inserer(self, event):
        code, ville = self.selection
        self.GetGrandParent().ExportListeVille(code, ville)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, "")
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
