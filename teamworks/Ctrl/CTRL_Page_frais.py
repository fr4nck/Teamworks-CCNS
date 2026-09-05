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
from Ctrl import CTRL_Section
from Dlg import DLG_Saisie_deplacement
from Dlg import DLG_Saisie_remboursement
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_Styles
import GestionDB
import FonctionsPerso


def DateEngFr(textDate):
    return str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])


def DateFrEng(textDate):
    return str(textDate[6:10]) + "/" + str(textDate[3:5]) + "/" + str(textDate[:2])


class Panel(wx.Panel):
    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Panel.__init__(self, parent, id, name="page_frais", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.section_deplacements = CTRL_Section.Section(
            self,
            titre=_(u"Déplacements"),
            niveau=2,
        )
        panel_deplacements = self.section_deplacements.GetContentPanel()
        self.ctrl_deplacements = ListCtrl_deplacements(panel_deplacements, -1, owner=self)
        self.ctrl_deplacements.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.bouton_deplacements_ajouter = self._bouton(
            panel_deplacements, _(u"Ajouter"), "Ajouter.png"
        )
        self.bouton_deplacements_modifier = self._bouton(
            panel_deplacements, _(u"Modifier"), "Modifier.png"
        )
        self.bouton_deplacements_supprimer = self._bouton(
            panel_deplacements, _(u"Supprimer"), "Supprimer.png"
        )
        self.bouton_deplacements_imprimer = self._bouton(
            panel_deplacements, _(u"Imprimer"), "Imprimante.png"
        )

        self.section_remboursements = CTRL_Section.Section(
            self,
            titre=_(u"Remboursements"),
            niveau=2,
        )
        panel_remboursements = self.section_remboursements.GetContentPanel()
        self.ctrl_remboursements = ListCtrl_remboursements(
            panel_remboursements,
            -1,
            owner=self,
        )
        self.ctrl_remboursements.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.bouton_remboursements_ajouter = self._bouton(
            panel_remboursements, _(u"Ajouter"), "Ajouter.png"
        )
        self.bouton_remboursements_modifier = self._bouton(
            panel_remboursements, _(u"Modifier"), "Modifier.png"
        )
        self.bouton_remboursements_supprimer = self._bouton(
            panel_remboursements, _(u"Supprimer"), "Supprimer.png"
        )

        self.__set_properties()
        self.__do_layout(panel_deplacements, panel_remboursements)

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjoutDeplacement, self.bouton_deplacements_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifDeplacement, self.bouton_deplacements_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprDeplacement, self.bouton_deplacements_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimerDeplacement, self.bouton_deplacements_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjoutRemboursement, self.bouton_remboursements_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifRemboursement, self.bouton_remboursements_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprRemboursement, self.bouton_remboursements_supprimer)

    def _bouton(self, parent, texte, image):
        return CTRL_Bouton_image.CTRL(
            parent,
            texte=texte,
            cheminImage=Chemins.GetStaticPath("Images/32x32/%s" % image),
        )

    def __set_properties(self):
        self.bouton_deplacements_ajouter.SetToolTip(wx.ToolTip(_(u"Saisir un nouveau déplacement")))
        self.bouton_deplacements_modifier.SetToolTip(wx.ToolTip(_(u"Modifier le déplacement sélectionné")))
        self.bouton_deplacements_supprimer.SetToolTip(wx.ToolTip(_(u"Supprimer le déplacement sélectionné")))
        self.bouton_deplacements_imprimer.SetToolTip(wx.ToolTip(_(u"Imprimer une fiche de frais de déplacement")))
        self.bouton_remboursements_ajouter.SetToolTip(wx.ToolTip(_(u"Saisir un nouveau remboursement")))
        self.bouton_remboursements_modifier.SetToolTip(wx.ToolTip(_(u"Modifier le remboursement sélectionné")))
        self.bouton_remboursements_supprimer.SetToolTip(wx.ToolTip(_(u"Supprimer le remboursement sélectionné")))
        self.bouton_deplacements_modifier.Enable(False)
        self.bouton_deplacements_supprimer.Enable(False)
        self.bouton_remboursements_modifier.Enable(False)
        self.bouton_remboursements_supprimer.Enable(False)

    def _barre_actions(self, *boutons):
        gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")
        sizer = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in boutons:
            sizer.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)
        return sizer

    def __do_layout(self, panel_deplacements, panel_remboursements):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")

        deplacements = wx.BoxSizer(wx.VERTICAL)
        deplacements.Add(
            self._barre_actions(
                self.bouton_deplacements_ajouter,
                self.bouton_deplacements_modifier,
                self.bouton_deplacements_supprimer,
                self.bouton_deplacements_imprimer,
            ),
            0,
            wx.EXPAND | wx.BOTTOM,
            gap,
        )
        deplacements.Add(self.ctrl_deplacements, 1, wx.EXPAND)
        panel_deplacements.SetSizer(deplacements)

        remboursements = wx.BoxSizer(wx.VERTICAL)
        remboursements.Add(
            self._barre_actions(
                self.bouton_remboursements_ajouter,
                self.bouton_remboursements_modifier,
                self.bouton_remboursements_supprimer,
            ),
            0,
            wx.EXPAND | wx.BOTTOM,
            gap,
        )
        remboursements.Add(self.ctrl_remboursements, 1, wx.EXPAND)
        panel_remboursements.SetSizer(remboursements)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(
            self.section_deplacements,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            page_gap,
        )
        sizer.Add(
            self.section_remboursements,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM,
            page_gap,
        )
        self.SetSizer(sizer)

    def MAJ_frm_gestion_frais(self):
        try:
            if self.GetGrandParent().GetName() == "frm_gestion_frais":
                self.GetGrandParent().ctrl_personnes.MAJListeCtrl()
        except Exception:
            pass

    def _verifie_personne(self):
        if self.IDpersonne is not None:
            return True
        dlg = wx.MessageDialog(
            self,
            _(u"Vous devez d'abord sélectionner une personne dans la liste"),
            "Information",
            wx.OK | wx.ICON_INFORMATION,
        )
        dlg.ShowModal()
        dlg.Destroy()
        return False

    def OnBoutonAjoutDeplacement(self, event):
        if not self._verifie_personne():
            return
        self.AjouterDeplacement()
        event.Skip()

    def AjouterDeplacement(self):
        dlg = DLG_Saisie_deplacement.SaisieDeplacement(
            self,
            IDdeplacement=None,
            IDpersonne=self.IDpersonne,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl_deplacements.MAJListeCtrl()
            self.ctrl_remboursements.MAJListeCtrl()
        dlg.Destroy()
        self.MAJ_frm_gestion_frais()

    def OnBoutonModifDeplacement(self, event):
        if not self._verifie_personne():
            return
        self.ModifierDeplacement()
        event.Skip()

    def ModifierDeplacement(self):
        index = self.ctrl_deplacements.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un déplacement à modifier dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDdeplacement = int(self.ctrl_deplacements.GetItem(index, 0).GetText())
        dlg = DLG_Saisie_deplacement.SaisieDeplacement(
            self,
            IDdeplacement=IDdeplacement,
            IDpersonne=self.IDpersonne,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl_deplacements.MAJListeCtrl()
            self.ctrl_remboursements.MAJListeCtrl()
        dlg.Destroy()
        self.MAJ_frm_gestion_frais()

    def OnBoutonSupprDeplacement(self, event):
        if not self._verifie_personne():
            return
        self.SupprimerDeplacement()
        event.Skip()

    def SupprimerDeplacement(self):
        index = self.ctrl_deplacements.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un déplacement à supprimer dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        IDdeplacement = int(self.ctrl_deplacements.GetItem(index, 0).GetText())
        DB = GestionDB.DB()
        req = "SELECT IDdeplacement, IDremboursement FROM deplacements WHERE IDdeplacement=%d;" % IDdeplacement
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        dejaAttribue = None
        for _, IDremboursement in listeDonnees:
            if IDremboursement not in (None, 0, ""):
                dejaAttribue = IDremboursement
                break
        if dejaAttribue is not None:
            dlg = wx.MessageDialog(
                self,
                _(u"Ce déplacement a déjà été attribué au remboursement n°")
                + str(dejaAttribue)
                + _(u".\nVous ne pouvez donc pas le supprimer."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        texte = self.ctrl_deplacements.GetItem(index, 3).GetText() + "\nLe " + self.ctrl_deplacements.GetItem(index, 1).GetText()
        dlgConfirm = wx.MessageDialog(
            self,
            six.text_type(_(u"Voulez-vous vraiment supprimer ce déplacement ? \n\n") + texte),
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return

        DB = GestionDB.DB()
        DB.ReqDEL("deplacements", "IDdeplacement", IDdeplacement)
        DB.Close()
        self.ctrl_deplacements.MAJListeCtrl()
        self.ctrl_remboursements.MAJListeCtrl()
        self.MAJ_frm_gestion_frais()

    def OnBoutonImprimerDeplacement(self, event):
        if not self._verifie_personne():
            return
        if self.ctrl_deplacements.GetItemCount() == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Il n'y a aucun déplacement à imprimer pour cette personne."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Dlg import DLG_Impression_frais
        dlg = DLG_Impression_frais.Dialog(self, self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonAjoutRemboursement(self, event):
        if not self._verifie_personne():
            return
        self.AjouterRemboursement()
        event.Skip()

    def AjouterRemboursement(self):
        dlg = DLG_Saisie_remboursement.SaisieRemboursement(
            self,
            IDremboursement=None,
            IDpersonne=self.IDpersonne,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl_deplacements.MAJListeCtrl()
            self.ctrl_remboursements.MAJListeCtrl()
        dlg.Destroy()
        self.MAJ_frm_gestion_frais()

    def OnBoutonModifRemboursement(self, event):
        if not self._verifie_personne():
            return
        self.ModifierRemboursement()
        event.Skip()

    def ModifierRemboursement(self):
        index = self.ctrl_remboursements.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un remboursement à modifier dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDremboursement = int(self.ctrl_remboursements.GetItem(index, 1).GetText())
        dlg = DLG_Saisie_remboursement.SaisieRemboursement(
            self,
            IDremboursement=IDremboursement,
            IDpersonne=self.IDpersonne,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl_deplacements.MAJListeCtrl()
            self.ctrl_remboursements.MAJListeCtrl()
        dlg.Destroy()
        self.MAJ_frm_gestion_frais()

    def OnBoutonSupprRemboursement(self, event):
        if not self._verifie_personne():
            return
        self.SupprimerRemboursement()
        event.Skip()

    def SupprimerRemboursement(self):
        index = self.ctrl_remboursements.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un remboursement à modifier dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        IDremboursement = int(self.ctrl_remboursements.GetItem(index, 1).GetText())
        DB = GestionDB.DB()
        req = "SELECT IDdeplacement FROM deplacements WHERE IDremboursement=%d;" % IDremboursement
        DB.ExecuterReq(req)
        listeDeplacements = DB.ResultatReq()
        DB.Close()
        nbreRattaches = len(listeDeplacements)
        if nbreRattaches != 0:
            dlgConfirm = wx.MessageDialog(
                self,
                _(u"Ce remboursement possède déjà ")
                + str(nbreRattaches)
                + _(u" déplacement(s) rattaché(s).\nSouhaitez-vous vous quand même le supprimer ?"),
                _(u"Confirmation de suppression"),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
            )
            reponse = dlgConfirm.ShowModal()
            dlgConfirm.Destroy()
            if reponse == wx.ID_NO:
                return

        texte = self.ctrl_remboursements.GetItem(index, 2).GetText() + _(u" d'un montant de ") + self.ctrl_remboursements.GetItem(index, 3).GetText()
        dlgConfirm = wx.MessageDialog(
            self,
            six.text_type(_(u"Voulez-vous vraiment supprimer le remboursement du ") + texte + " ?"),
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return

        DB = GestionDB.DB()
        try:
            DB.ExecuterReq(
                "UPDATE deplacements SET IDremboursement=0 WHERE IDremboursement=%d;"
                % IDremboursement
            )
            DB.ReqDEL(
                "remboursements",
                "IDremboursement",
                IDremboursement,
                commit=False,
            )
            DB.Commit()
        except Exception:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            raise
        finally:
            DB.Close()

        self.ctrl_deplacements.MAJListeCtrl()
        self.ctrl_remboursements.MAJListeCtrl()
        self.MAJ_frm_gestion_frais()


class _ListeFrais(wx.ListCtrl, listmix.ColumnSorterMixin):
    def __init__(self, parent, owner, id=-1):
        wx.ListCtrl.__init__(
            self,
            parent,
            id,
            style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES | wx.BORDER_NONE,
        )
        self.owner = owner
        self.IDpersonne = owner.IDpersonne
        self._ajustement_en_cours = False
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self._init_sort_images()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _init_sort_images(self):
        taille = UTILS_Styles.GetIconSize("small")[0]
        self.il = wx.ImageList(taille, taille)
        self.imgTriAz = self.il.Add(self._bitmap("Tri_az.png", taille))
        self.imgTriZa = self.il.Add(self._bitmap("Tri_za.png", taille))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

    def _bitmap(self, nom, taille):
        bitmap = wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/%s" % nom),
            wx.BITMAP_TYPE_PNG,
        )
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            bitmap = wx.Bitmap(
                bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
            )
        return bitmap

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

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

    def getColumnText(self, index, col):
        return self.GetItem(index, col).GetText()


class ListCtrl_deplacements(_ListeFrais):
    def __init__(self, parent, id=-1, owner=None):
        _ListeFrais.__init__(self, parent, owner, id)
        self.nbreColonnes = 8
        if self.IDpersonne is not None:
            self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def Remplissage(self):
        self.Importation()
        self.ClearAll()
        for titre, align in (
            (u"N°", wx.LIST_FORMAT_LEFT),
            (_(u"Date"), wx.LIST_FORMAT_LEFT),
            (_(u"Objet"), wx.LIST_FORMAT_LEFT),
            (_(u"Trajet"), wx.LIST_FORMAT_LEFT),
            (_(u"Distance"), wx.LIST_FORMAT_RIGHT),
            (_(u"Tarif"), wx.LIST_FORMAT_RIGHT),
            (_(u"Montant"), wx.LIST_FORMAT_RIGHT),
            (_(u"Remboursement"), wx.LIST_FORMAT_LEFT),
        ):
            self.InsertColumn(self.GetColumnCount(), titre, align)
        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(1, 1)
        wx.CallAfter(self.AjusterColonnes)

    def AjusterColonnes(self):
        if self._ajustement_en_cours or self.GetColumnCount() < 8:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return
        fixes = [
            UTILS_Styles.Scale(68),
            UTILS_Styles.Scale(105),
            None,
            None,
            UTILS_Styles.Scale(105),
            UTILS_Styles.Scale(110),
            UTILS_Styles.Scale(115),
            UTILS_Styles.Scale(125),
        ]
        disponible = max(
            UTILS_Styles.Scale(360),
            largeur - sum(value or 0 for value in fixes) - UTILS_Styles.GetSpacing("sm"),
        )
        fixes[2] = max(UTILS_Styles.Scale(150), int(disponible * 0.38))
        fixes[3] = max(UTILS_Styles.Scale(210), disponible - fixes[2])
        self._ajustement_en_cours = True
        try:
            for index, taille in enumerate(fixes):
                self.SetColumnWidth(index, taille)
        finally:
            self._ajustement_en_cours = False

    def OnItemSelected(self, event):
        self.owner.bouton_deplacements_modifier.Enable(True)
        self.owner.bouton_deplacements_supprimer.Enable(True)

    def OnItemDeselected(self, event):
        self.owner.bouton_deplacements_modifier.Enable(False)
        self.owner.bouton_deplacements_supprimer.Enable(False)

    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT IDdeplacement, date, objet, ville_depart, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement
        FROM deplacements WHERE IDpersonne=%d ORDER BY date;""" % self.IDpersonne
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        self.nbreLignes = len(listeDonnees)
        self.donnees = {}
        for IDdeplacement, date, objet, ville_depart, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement in listeDonnees:
            trajet = ville_depart + (" <--> " if aller_retour == "True" else " -> ") + ville_arrivee
            remboursement = u"N°%s" % IDremboursement if IDremboursement not in (None, 0, "") else ""
            dist = str(distance) + _(u" Km")
            montantStr = u"%.2f €" % (float(distance) * float(tarif_km))
            tarif_str = str(tarif_km) + _(u" €/km")
            self.donnees[IDdeplacement] = (
                IDdeplacement,
                date,
                objet,
                trajet,
                dist,
                tarif_str,
                montantStr,
                remboursement,
            )

    def MAJListeCtrl(self):
        self.IDpersonne = self.owner.IDpersonne
        self.ClearAll()
        if self.IDpersonne is not None:
            self.Remplissage()

    def OnItemActivated(self, event):
        self.owner.ModifierDeplacement()

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        valeur = six.text_type(self.itemDataMap[index][col])
        if col == 1 and valeur[4:5] == "-" and valeur[7:8] == "-":
            valeur = valeur[8:10] + "/" + valeur[5:7] + "/" + valeur[0:4]
        return valeur

    def OnGetItemImage(self, item):
        return -1

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False
        menuPop = UTILS_Adaptations.Menu()
        item_ajouter = menuPop.Append(10, _(u"Ajouter"))
        menuPop.AppendSeparator()
        item_modifier = menuPop.Append(20, _(u"Modifier"))
        item_supprimer = menuPop.Append(30, _(u"Supprimer"))
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.owner.AjouterDeplacement()

    def Menu_Modifier(self, event):
        self.owner.ModifierDeplacement()

    def Menu_Supprimer(self, event):
        self.owner.SupprimerDeplacement()


class ListCtrl_remboursements(_ListeFrais):
    def __init__(self, parent, id=-1, owner=None):
        _ListeFrais.__init__(self, parent, owner, id)
        self.nbreColonnes = 5
        if self.IDpersonne is not None:
            self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def Remplissage(self):
        self.Importation()
        self.ClearAll()
        self.InsertColumn(0, u"")
        self.InsertColumn(1, u"N°")
        self.InsertColumn(2, _(u"Date"))
        self.InsertColumn(3, _(u"Montant"), wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(4, _(u"Déplacements rattachés"))
        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(2, 1)
        wx.CallAfter(self.AjusterColonnes)

    def AjusterColonnes(self):
        if self._ajustement_en_cours or self.GetColumnCount() < 5:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return
        numero = UTILS_Styles.Scale(75)
        date = UTILS_Styles.Scale(110)
        montant = UTILS_Styles.Scale(120)
        restant = max(UTILS_Styles.Scale(260), largeur - numero - date - montant - UTILS_Styles.GetSpacing("sm"))
        self._ajustement_en_cours = True
        try:
            self.SetColumnWidth(0, 0)
            self.SetColumnWidth(1, numero)
            self.SetColumnWidth(2, date)
            self.SetColumnWidth(3, montant)
            self.SetColumnWidth(4, restant)
        finally:
            self._ajustement_en_cours = False

    def OnItemSelected(self, event):
        self.owner.bouton_remboursements_modifier.Enable(True)
        self.owner.bouton_remboursements_supprimer.Enable(True)

    def OnItemDeselected(self, event):
        self.owner.bouton_remboursements_modifier.Enable(False)
        self.owner.bouton_remboursements_supprimer.Enable(False)

    def Importation(self):
        DB = GestionDB.DB()
        req = "SELECT IDremboursement, date, montant FROM remboursements WHERE IDpersonne=%d ORDER BY date;" % self.IDpersonne
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()

        dictDeplacements = {}
        if listeDonnees:
            listeRemboursements = [str(IDremboursement) for IDremboursement, _, _ in listeDonnees]
            req = """SELECT IDdeplacement, IDremboursement FROM deplacements
            WHERE IDpersonne=%d AND IDremboursement IN (%s) ORDER BY IDdeplacement;""" % (
                self.IDpersonne,
                ",".join(listeRemboursements),
            )
            DB.ExecuterReq(req)
            for IDdeplacement, IDremboursement in DB.ResultatReq():
                dictDeplacements.setdefault(IDremboursement, []).append(IDdeplacement)
        DB.Close()

        self.nbreLignes = len(listeDonnees)
        self.donnees = {}
        for IDremboursement, date, montant in listeDonnees:
            montant_str = u"%.2f €" % montant
            listeID = dictDeplacements.get(IDremboursement, [])
            if not listeID:
                texteListeID = _(u"Aucun déplacement rattaché")
            else:
                texteListeID = u"N° " + ", ".join(str(x) for x in listeID)
            self.donnees[IDremboursement] = (
                "",
                IDremboursement,
                date,
                montant_str,
                texteListeID,
            )

    def MAJListeCtrl(self):
        self.IDpersonne = self.owner.IDpersonne
        self.ClearAll()
        if self.IDpersonne is not None:
            self.Remplissage()

    def OnItemActivated(self, event):
        self.owner.ModifierRemboursement()

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        valeur = six.text_type(self.itemDataMap[index][col])
        if col == 2 and valeur[4:5] == "-" and valeur[7:8] == "-":
            valeur = valeur[8:10] + "/" + valeur[5:7] + "/" + valeur[0:4]
        return valeur

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False
        menuPop = UTILS_Adaptations.Menu()
        menuPop.Append(10, _(u"Ajouter"))
        menuPop.AppendSeparator()
        menuPop.Append(20, _(u"Modifier"))
        menuPop.Append(30, _(u"Supprimer"))
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.owner.AjouterRemboursement()

    def Menu_Modifier(self, event):
        self.owner.ModifierRemboursement()

    def Menu_Supprimer(self, event):
        self.owner.SupprimerRemboursement()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        self.SetMinSize(UTILS_Styles.GetWindowSize("wide"))

        IDpersonne = 1
        self.panel.IDpersonne = IDpersonne
        self.panel.ctrl_deplacements.IDpersonne = IDpersonne
        self.panel.ctrl_remboursements.IDpersonne = IDpersonne
        self.panel.ctrl_deplacements.MAJListeCtrl()
        self.panel.ctrl_remboursements.MAJListeCtrl()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
