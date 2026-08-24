#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sélection et recherche des personnes dans l'écran Présences."""

import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin

import FonctionsPerso
import GestionDB
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Presences_common
from Ctrl import CTRL_Texte
from Dlg import DLG_Application_modele
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


_PHOENIX = "phoenix" in wx.PlatformInfo
_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin


class listCtrl_Personnes(wx.ListCtrl, _CheckboxFallback):
    """Liste des personnes avec un seul mécanisme de checkbox par plateforme."""

    def __init__(self, parent):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.BORDER_NONE,
        )
        if _PHOENIX:
            self.EnableCheckBoxes(True)
        else:
            CheckListCtrlMixin.__init__(self)
        self.parent = parent
        self._suspend_checks = False
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        if _PHOENIX:
            if hasattr(wx, "EVT_LIST_ITEM_CHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnNativeCheckItem)
            if hasattr(wx, "EVT_LIST_ITEM_UNCHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnNativeCheckItem)

    def _is_checked(self, index):
        if _PHOENIX:
            return self.IsItemChecked(index)
        return self.IsChecked(index)

    def _set_checked(self, index, etat=True):
        self.CheckItem(index, etat)

    def _synchroniser_selection(self, notifier=True):
        for index in range(self.GetItemCount()):
            IDpersonne = self.GetItemData(index)
            self.parent.dictPersonnes[IDpersonne][4] = self._is_checked(index)
        personnes = [
            IDpersonne
            for IDpersonne, valeurs in self.parent.dictPersonnes.items()
            if valeurs[4]
        ]
        panel = CTRL_Presences_common.find_presences_panel(self)
        if panel is not None:
            panel.SetSelectionPersonnes(personnes)
            if notifier:
                panel.MAJpanelPlanning()

    def _bulk_check(self, predicate, notifier=True):
        self._suspend_checks = True
        try:
            for index in range(self.GetItemCount()):
                self._set_checked(index, bool(predicate(index)))
        finally:
            self._suspend_checks = False
        self._synchroniser_selection(notifier=notifier)

    def Remplissage(self):
        self.ClearAll()
        self.InsertColumn(0, _(u"Individus"))
        self._suspend_checks = True
        try:
            for key, valeurs in self.parent.dictPersonnes.items():
                if not valeurs[3]:
                    continue
                if self.parent.triCritere == "prenom":
                    texte = valeurs[1] + " " + valeurs[0]
                else:
                    texte = valeurs[0] + " " + valeurs[1]
                index = self.InsertItem(self.GetItemCount(), texte)
                self.SetItemData(index, key)
                if valeurs[4]:
                    self._set_checked(index, True)
        finally:
            self._suspend_checks = False
        self.SortItems(self.columnSorter)
        wx.CallAfter(self.AjusterColonne)

    def CreateCouleurs(self, cocheAussi=True):
        panel = CTRL_Presences_common.find_presences_panel(self)
        liste_presents = panel.panelPlanning.listePresents if panel is not None else []
        for index in range(self.GetItemCount()):
            item = self.GetItem(index)
            key = self.GetItemData(index)
            token = "primary" if key in liste_presents else "on_surface"
            item.SetTextColour(UTILS_Interface.GetToken(token))
            self.SetItem(item)
        if cocheAussi:
            self._bulk_check(
                lambda index: self.GetItemData(index) in liste_presents,
                notifier=False,
            )
        self.Refresh()

    def columnSorter(self, key1, key2):
        if self.parent.triOrdre == "decroissant":
            key1, key2 = key2, key1
        if self.parent.triCritere == "presence":
            item1 = self.parent.dictPersonnes[key1][2]
            item2 = self.parent.dictPersonnes[key2][2]
        else:
            item1 = self.parent.dictPersonnes[key1][0] + " " + self.parent.dictPersonnes[key1][1]
            item2 = self.parent.dictPersonnes[key2][0] + " " + self.parent.dictPersonnes[key2][1]
        item1 = item1 or ""
        item2 = item2 or ""
        if item1 == item2:
            return 0
        return -1 if item1 < item2 else 1

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonne)
        event.Skip()

    def AjusterColonne(self):
        if self.GetColumnCount() == 0:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur > 0:
            self.SetColumnWidth(0, max(UTILS_Styles.Scale(160), largeur - 2))

    def OnItemActivated(self, event):
        self._suspend_checks = True
        try:
            self._set_checked(event.Index, not self._is_checked(event.Index))
        finally:
            self._suspend_checks = False
        self._synchroniser_selection()

    def OnCheckItem(self, index, flag):
        if not self._suspend_checks:
            self._synchroniser_selection()

    def OnNativeCheckItem(self, event):
        if not self._suspend_checks:
            self._synchroniser_selection()
        event.Skip()

    def OnContextMenu(self, event):
        self.parent.Menu_Personnes(event)

    def GetListePersonnes(self):
        panel = CTRL_Presences_common.find_presences_panel(self)
        return panel.GetSelectionPersonnes() if panel is not None else []

    def SetTousCoches(self, etat=True):
        self._bulk_check(lambda index: etat)

    def SetUniquement(self, index_selectionne):
        self._bulk_check(lambda index: index == index_selectionne)

    def SetPresents(self, liste_presents):
        self._bulk_check(lambda index: self.GetItemData(index) in liste_presents)


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.SetDescriptiveText(_(u"Rechercher une personne"))
        self.ShowSearchButton(True)
        self.ShowCancelButton(True)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, event):
        self.Recherche(self.GetValue())

    def OnCancel(self, event):
        self.SetValue("")
        self.Recherche("")

    def OnDoSearch(self, event):
        self.Recherche(self.GetValue())

    def Recherche(self, txtSearch):
        txtSearch = txtSearch.upper()
        for valeurs in self.parent.dictPersonnes.values():
            if self.parent.triCritere == "prenom":
                texte = valeurs[1] + " " + valeurs[0]
            else:
                texte = valeurs[0] + " " + valeurs[1]
            valeurs[3] = txtSearch in texte.upper()
        self.parent.MAJlistCtrl()


class PanelPersonnes(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.triCritere = FonctionsPerso.Parametres(
            mode="get",
            categorie="presences",
            nom="tri_critere",
            valeur="presence",
        )
        self.triOrdre = FonctionsPerso.Parametres(
            mode="get",
            categorie="presences",
            nom="tri_ordre",
            valeur="decroissant",
        )
        self.dictPersonnes = self.Import_Personnes()

        self.bouton_options = CTRL_Bouton_image.CTRL(self, texte=_(u"Options"))
        self.bouton_options.SetToolTip(
            wx.ToolTip(_(u"Options d'affichage et de sélection"))
        )
        self.txtOptions = CTRL_Texte.Caption(self, u"")
        self.MAJtexteOptions()
        self.listCtrlPersonnes = listCtrl_Personnes(self)
        self.barreRecherche = BarreRecherche(self)
        self.Bind(wx.EVT_BUTTON, self.Menu_Personnes, self.bouton_options)

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        options = wx.BoxSizer(wx.HORIZONTAL)
        options.Add(self.bouton_options, 0, wx.RIGHT, gap)
        options.Add(self.txtOptions, 1, wx.ALIGN_CENTER_VERTICAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(options, 0, wx.EXPAND | wx.BOTTOM, gap)
        sizer.Add(self.listCtrlPersonnes, 1, wx.EXPAND | wx.BOTTOM, gap)
        sizer.Add(self.barreRecherche, 0, wx.EXPAND)
        self.SetSizer(sizer)

    def MAJtexteOptions(self):
        texte = (
            _(u"Tri asc. selon ")
            if self.triOrdre == "croissant"
            else _(u"Tri desc. selon ")
        )
        if self.triCritere == "presence":
            texte += _(u"la dernière présence")
        elif self.triCritere == "nom":
            texte += _(u"le nom")
        else:
            texte += _(u"le prénom")
        self.txtOptions.SetLabel(texte)

    def MAJpanel(self):
        ancienne_selection = {
            key: valeurs[4] for key, valeurs in self.dictPersonnes.items()
        }
        self.dictPersonnes = self.Import_Personnes()
        for key, etat in ancienne_selection.items():
            if key in self.dictPersonnes:
                self.dictPersonnes[key][4] = etat
        self.MAJtexteOptions()
        self.listCtrlPersonnes.Remplissage()
        self.listCtrlPersonnes.CreateCouleurs(True)

    def Menu_Personnes(self, event):
        menu = UTILS_Adaptations.Menu()

        sm_tri = UTILS_Adaptations.Menu()
        sm_tri.Append(110, _(u"Dernière présence"), _(u"Trier selon la dernière présence"), wx.ITEM_RADIO)
        sm_tri.Append(120, _(u"Nom"), _(u"Trier selon le nom"), wx.ITEM_RADIO)
        sm_tri.Append(130, _(u"Prénom"), _(u"Trier selon le prénom"), wx.ITEM_RADIO)
        sm_tri.Check({"presence": 110, "nom": 120, "prenom": 130}[self.triCritere], True)
        menu.AppendSubMenu(sm_tri, _(u"Tri par"))

        sm_ordre = UTILS_Adaptations.Menu()
        sm_ordre.Append(210, _(u"Ordre croissant"), _(u"Trier par ordre croissant"), wx.ITEM_RADIO)
        sm_ordre.Append(220, _(u"Ordre décroissant"), _(u"Trier par ordre décroissant"), wx.ITEM_RADIO)
        sm_ordre.Check(210 if self.triOrdre == "croissant" else 220, True)
        menu.AppendSubMenu(sm_ordre, _(u"Ordre de tri"))

        menu.AppendSeparator()
        menu.Append(30, _(u"Afficher toute la liste"), _(u"Tout afficher"))
        menu.AppendSeparator()
        menu.Append(40, _(u"Tout sélectionner"), _(u"Tout sélectionner"))
        menu.Append(50, _(u"Tout désélectionner"), _(u"Tout désélectionner"))

        index = self.listCtrlPersonnes.GetFirstSelected()
        if index != -1:
            nom_personne = self.listCtrlPersonnes.GetItem(index, 0).GetText()
            texte = _(u"Sélectionner uniquement ") + nom_personne
            menu.Append(55, texte, texte)

        menu.Append(
            60,
            _(u"Sélectionner les personnes présentes"),
            _(u"Sélectionner les personnes présentes sur les jours sélectionnés"),
        )
        menu.AppendSeparator()
        menu.Append(
            70,
            _(u"Appliquer un modèle aux personnes sélectionnées"),
            _(u"Appliquer un modèle aux personnes sélectionnées"),
        )

        if index != -1:
            nom_personne = self.listCtrlPersonnes.GetItem(index, 0).GetText()
            menu.AppendSeparator()
            texte = _(u"Afficher la liste des présences de ") + nom_personne
            menu.Append(80, texte, texte)
            texte = _(u"Imprimer un planning annuel pour ") + nom_personne
            menu.Append(90, texte, texte)

        bindings = {
            110: self.Menu_110,
            120: self.Menu_120,
            130: self.Menu_130,
            210: self.Menu_210,
            220: self.Menu_220,
            30: self.Menu_30,
            40: self.Menu_40,
            50: self.Menu_50,
            55: self.Menu_55,
            60: self.Menu_60,
            70: self.Menu_70,
            80: self.Menu_80,
            90: self.Menu_90,
        }
        for identifiant, handler in bindings.items():
            self.Bind(wx.EVT_MENU, handler, id=identifiant)

        self.PopupMenu(menu)
        menu.Destroy()

    def MAJlistCtrl(self):
        self.listCtrlPersonnes.Remplissage()
        self.listCtrlPersonnes.CreateCouleurs(False)

    def _set_tri(self, critere=None, ordre=None):
        if critere is not None:
            self.triCritere = critere
            FonctionsPerso.Parametres(
                mode="set",
                categorie="presences",
                nom="tri_critere",
                valeur=critere,
            )
        if ordre is not None:
            self.triOrdre = ordre
            FonctionsPerso.Parametres(
                mode="set",
                categorie="presences",
                nom="tri_ordre",
                valeur=ordre,
            )
        self.MAJtexteOptions()
        self.MAJlistCtrl()

    def Menu_110(self, event):
        self._set_tri(critere="presence")

    def Menu_120(self, event):
        self._set_tri(critere="nom")

    def Menu_130(self, event):
        self._set_tri(critere="prenom")

    def Menu_210(self, event):
        self._set_tri(ordre="croissant")

    def Menu_220(self, event):
        self._set_tri(ordre="decroissant")

    def Menu_30(self, event):
        for valeurs in self.dictPersonnes.values():
            valeurs[3] = True
        self.MAJlistCtrl()

    def Menu_40(self, event):
        self.listCtrlPersonnes.SetTousCoches(True)

    def Menu_50(self, event):
        self.listCtrlPersonnes.SetTousCoches(False)

    def Menu_55(self, event):
        index = self.listCtrlPersonnes.GetFirstSelected()
        if index != -1:
            self.listCtrlPersonnes.SetUniquement(index)

    def Menu_60(self, event):
        panel = CTRL_Presences_common.find_presences_panel(self)
        if panel is not None:
            self.listCtrlPersonnes.SetPresents(panel.panelPlanning.listePresents)

    def Menu_70(self, event):
        personnes = [
            self.listCtrlPersonnes.GetItemData(index)
            for index in range(self.listCtrlPersonnes.GetItemCount())
            if self.listCtrlPersonnes._is_checked(index)
        ]
        if not personnes:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord cocher un ou plusieurs noms de personnes dans la liste."),
                _(u"Erreur"),
                wx.OK | wx.ICON_WARNING,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        panel = CTRL_Presences_common.find_presences_panel(self)
        dates = list(panel.GetSelectionDates()) if panel is not None else []
        dates.sort()
        plage = (dates[0], dates[-1]) if dates else (None, None)
        dlg = DLG_Application_modele.Dialog(
            self,
            selectionPersonnes=personnes,
            selectionDates=plage,
        )
        dlg.ShowModal()
        dlg.Destroy()
        if panel is not None:
            panel.MAJpanelPlanning()

    def Menu_80(self, event):
        index = self.listCtrlPersonnes.GetFirstSelected()
        if index == -1:
            return
        IDpersonne = int(self.listCtrlPersonnes.GetItemData(index))
        from Ctrl import CTRL_Page_presences
        dlg = CTRL_Page_presences.Dialog(self, IDpersonne=IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()

    def Menu_90(self, event):
        index = self.listCtrlPersonnes.GetFirstSelected()
        if index == -1:
            return
        IDpersonne = int(self.listCtrlPersonnes.GetItemData(index))
        from Dlg import DLG_Impression_calendrier_annuel
        dlg = DLG_Impression_calendrier_annuel.MyDialog(
            None,
            IDpersonne=IDpersonne,
            autoriser_choix_personne=False,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def Import_Personnes(self):
        req = """
            SELECT personnes.IDpersonne, personnes.nom, personnes.prenom, Max(presences.date) AS MaxDedate
            FROM personnes LEFT JOIN presences ON personnes.IDpersonne = presences.IDpersonne
            GROUP BY personnes.IDpersonne, personnes.nom, personnes.prenom
            ORDER BY Max(presences.date);
        """
        DB = GestionDB.DB()
        DB.ExecuterReq(req)
        liste_donnees = DB.ResultatReq()
        DB.Close()
        return {
            personne[0]: [personne[1], personne[2], personne[3], True, False]
            for personne in liste_donnees
        }
