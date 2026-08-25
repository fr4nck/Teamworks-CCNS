#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gestion globale des frais de déplacement."""

import wx
import wx.lib.mixins.listctrl as listmix

import Chemins
import FonctionsPerso
import GestionDB
import six
from Ctrl import CTRL_Bouton_image, CTRL_Page_frais
from Utils.UTILS_Traduction import _
from infrastructure.persistence.person_reader import PersonReader


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            name="frm_gestion_frais",
            style=(
                wx.DEFAULT_DIALOG_STYLE
                | wx.RESIZE_BORDER
                | wx.MAXIMIZE_BOX
                | wx.MINIMIZE_BOX
            ),
        )
        self.parent = parent
        self.IDpersonne = None
        self.nomPersonne = None

        self.panel_base = wx.Panel(self, -1)
        self.label_intro = wx.StaticText(
            self.panel_base,
            -1,
            _(
                u"Veuillez sélectionner un individu dans la liste pour afficher "
                u"les déplacements et remboursements correspondants :"
            ),
        )
        self.staticBox_selection = wx.StaticBox(
            self.panel_base, -1, _(u"Sélection")
        )

        self.label_check_tous = wx.StaticText(
            self.staticBox_selection, -1, _(u"Afficher toutes les personnes")
        )
        self.ctrl_check_tous = wx.RadioButton(
            self.staticBox_selection, -1, "", style=wx.RB_GROUP
        )
        self.label_check_nonRembourses = wx.StaticText(
            self.staticBox_selection,
            -1,
            _(
                u"Afficher uniquement les \npersonnes ayant au moins un "
                u"\ndéplacement non remboursé"
            ),
        )
        self.ctrl_check_nonRembourses = wx.RadioButton(
            self.staticBox_selection, -1, ""
        )
        self.ctrl_check_nonRembourses.SetValue(True)

        self.ctrl_personnes = ListCtrl_personnes(self.staticBox_selection)
        self.panel_pageFrais = CTRL_Page_frais.Panel(
            self.panel_base, IDpersonne=self.IDpersonne
        )

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Fermer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"),
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnCheckTous, self.ctrl_check_tous)
        self.Bind(
            wx.EVT_RADIOBUTTON,
            self.OnCheckNonRembourses,
            self.ctrl_check_nonRembourses,
        )

        # Si aucune personne n'a de déplacement à rembourser, afficher tout le monde.
        if len(self.ctrl_personnes.donnees) == 0:
            self.ctrl_check_tous.SetValue(True)
            self.ctrl_personnes.MAJListeCtrl()

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des frais de déplacement"))
        icon = wx.Icon() if "phoenix" in wx.PlatformInfo else wx.EmptyIcon()
        icon.CopyFromBitmap(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Logo.png"),
                wx.BITMAP_TYPE_ANY,
            )
        )
        self.SetIcon(icon)
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Fermer la gestion des frais")))
        self.SetMinSize((760, 600))

    def __do_layout(self):
        filtre = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=5)
        filtre.Add(self.ctrl_check_tous, 0)
        filtre.Add(self.label_check_tous, 0)
        filtre.Add(self.ctrl_check_nonRembourses, 0)
        filtre.Add(self.label_check_nonRembourses, 0)

        selection = wx.StaticBoxSizer(self.staticBox_selection, wx.HORIZONTAL)
        selection.Add(self.ctrl_personnes, 1, wx.ALL | wx.EXPAND, 5)
        selection.Add(filtre, 0, wx.ALL, 5)

        boutons = wx.BoxSizer(wx.HORIZONTAL)
        boutons.Add(self.bouton_aide, 0)
        boutons.AddStretchSpacer(1)
        boutons.Add(self.bouton_ok, 0)

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.label_intro, 0, wx.ALL | wx.EXPAND, 10)
        contenu.Add(selection, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        contenu.Add(
            self.panel_pageFrais,
            1,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            10,
        )
        contenu.Add(boutons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.panel_base.SetSizer(contenu)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetSize((1050, 760))
        self.Layout()
        self.CenterOnScreen()

    def _set_section_title(self, section, texte):
        titre = getattr(section, "titre", None)
        if titre is not None:
            titre.SetLabel(texte)
            section.Layout()

    def OnCheckTous(self, event):
        self.ctrl_personnes.MAJListeCtrl()
        self.IDpersonne = None
        self.nomPersonne = None
        self.MAJlistes()

    def OnCheckNonRembourses(self, event):
        self.ctrl_personnes.MAJListeCtrl()
        self.IDpersonne = None
        self.nomPersonne = None
        self.MAJlistes()

    def MAJlistes(self):
        self.panel_pageFrais.IDpersonne = self.IDpersonne
        self.panel_pageFrais.ctrl_deplacements.IDpersonne = self.IDpersonne
        self.panel_pageFrais.ctrl_remboursements.IDpersonne = self.IDpersonne

        if self.IDpersonne is None:
            titre_deplacements = _(u"Déplacements")
            titre_remboursements = _(u"Remboursements")
        else:
            titre_deplacements = _(u"Déplacements de %s") % self.nomPersonne
            titre_remboursements = _(u"Remboursements de %s") % self.nomPersonne

        self._set_section_title(
            self.panel_pageFrais.section_deplacements, titre_deplacements
        )
        self._set_section_title(
            self.panel_pageFrais.section_remboursements, titre_remboursements
        )
        self.panel_pageFrais.ctrl_deplacements.MAJListeCtrl()
        self.panel_pageFrais.ctrl_remboursements.MAJListeCtrl()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide

        UTILS_Aide.Aide("Gestiondesfraisdedplacements")

    def OnBoutonOk(self, event):
        self.EndModal(wx.ID_OK)


class ListCtrl_personnes(
    wx.ListCtrl,
    listmix.ListCtrlAutoWidthMixin,
    listmix.ColumnSorterMixin,
):
    def __init__(self, parent, IDpersonne=None):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=(
                wx.LC_REPORT
                | wx.LC_VIRTUAL
                | wx.LC_SINGLE_SEL
                | wx.LC_HRULES
                | wx.LC_VRULES
            ),
        )
        self.IDpersonne = IDpersonne
        self.parent = parent
        self.selection = (0, None)

        taille_icones = 16
        self.il = wx.ImageList(taille_icones, taille_icones)
        self.imgTriAz = self.il.Add(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Tri_az.png"),
                wx.BITMAP_TYPE_PNG,
            )
        )
        self.imgTriZa = self.il.Add(
            wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Tri_za.png"),
                wx.BITMAP_TYPE_PNG,
            )
        )
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        self.attr1 = wx.ItemAttr()
        self.attr1.SetBackgroundColour("#EEF4FB")
        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)

    def Remplissage(self):
        self.Importation()
        self.nbreColonnes = 4
        self.InsertColumn(0, _(u"ID"))
        self.SetColumnWidth(0, 0)
        self.InsertColumn(1, _(u"Nom et prénom"))
        self.SetColumnWidth(1, 200)
        self.InsertColumn(2, _(u"Déplac. remboursés"))
        self.SetColumnWidth(2, 120)
        self.InsertColumn(3, _(u"Déplac. non remboursés"))
        self.SetColumnWidth(3, 150)

        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(1, 1)

    def OnItemSelected(self, event):
        index = self.GetFirstSelected()
        if index == -1:
            return False
        IDpersonne = int(self.getColumnText(index, 0))
        nomPersonne = self.getColumnText(index, 1)
        dialog = self.GetGrandParent()
        dialog.IDpersonne = IDpersonne
        dialog.nomPersonne = nomPersonne
        dialog.MAJlistes()
        event.Skip()

    def Importation(self):
        reader = PersonReader()
        try:
            listePersonnes = reader.lire_identites()
        finally:
            reader.close()

        dictDonnees = {
            IDpersonne: [IDpersonne, "%s %s" % (nom or "", prenom or ""), 0, 0.0, 0, 0.0]
            for IDpersonne, nom, prenom in listePersonnes
        }

        DB = GestionDB.DB()
        req = """SELECT IDdeplacement, IDpersonne, distance, tarif_km, IDremboursement
        FROM deplacements;"""
        DB.ExecuterReq(req)
        listeDeplacements = DB.ResultatReq()
        DB.Close()

        for _, IDpersonne, distance, tarif_km, IDremboursement in listeDeplacements:
            # Une ancienne donnée orpheline ne doit pas empêcher l'ouverture de la fenêtre.
            if IDpersonne not in dictDonnees:
                continue
            montant = float(distance or 0) * float(tarif_km or 0)
            if IDremboursement in (None, 0):
                dictDonnees[IDpersonne][4] += 1
                dictDonnees[IDpersonne][5] += montant
            else:
                dictDonnees[IDpersonne][2] += 1
                dictDonnees[IDpersonne][3] += montant

        afficher_non_rembourses = self.GetGrandParent().ctrl_check_nonRembourses.GetValue()
        self.donnees = {}
        index = 0
        for IDpersonne, valeurs in dictDonnees.items():
            nom = valeurs[1]
            nbreRembourses, montantRembourses = valeurs[2], valeurs[3]
            nbreNonRembourses, montantNonRembourses = valeurs[4], valeurs[5]
            txtRembourses = (
                "" if nbreRembourses == 0
                else str(nbreRembourses) + _(u" (soit %.2f €) ") % montantRembourses
            )
            txtNonRembourses = (
                "" if nbreNonRembourses == 0
                else str(nbreNonRembourses) + _(u" (soit %.2f €) ") % montantNonRembourses
            )
            if afficher_non_rembourses and nbreNonRembourses == 0:
                continue
            self.donnees[index] = (
                IDpersonne,
                nom,
                txtRembourses,
                txtNonRembourses,
            )
            index += 1

        self.nbreLignes = len(self.donnees)

    def MAJListeCtrl(self):
        self.ClearAll()
        self.Remplissage()

    def getColumnText(self, index, col):
        return self.GetItem(index, col).GetText()

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        return six.text_type(self.itemDataMap[index][col])

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        return self.attr1 if item % 2 == 1 else None

    def SortItems(self, sorter=FonctionsPerso.cmp):
        items = list(self.itemDataMap.keys())
        self.itemIndexMap = FonctionsPerso.SortItems(items, sorter)
        self.Refresh()

    def GetListCtrl(self):
        return self

    def GetSortImages(self):
        return (self.imgTriAz, self.imgTriZa)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
