#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Application de modèles de présences — coque moderne.

La logique d'application, de chevauchement, de vacances et de jours fériés
reste bit-for-bit dans ``DLG_Application_modele_core``. Ce module reconstruit
uniquement l'interface et les listes cochables avec la charte Teamworks.
"""

import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin

import GestionDB
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Dlg import DLG_Application_modele_core as CORE
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _

if "phoenix" in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else:
    from wx import DatePickerCtrl, DP_DROPDOWN


_PHOENIX = "phoenix" in wx.PlatformInfo
_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin


def _dialog_ancestor(window):
    current = window
    while current is not None:
        if isinstance(current, wx.Dialog):
            return current
        try:
            current = current.GetParent()
        except Exception:
            current = None
    return None


class listCtrl_Personnes(wx.ListCtrl, _CheckboxFallback):
    def __init__(self, parent, owner):
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
        self.owner = owner
        self._suspend_checks = False
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.dictPersonnes = self.Import_Personnes()
        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        if _PHOENIX:
            if hasattr(wx, "EVT_LIST_ITEM_CHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnNativeCheckItem)
            if hasattr(wx, "EVT_LIST_ITEM_UNCHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnNativeCheckItem)

    def _is_checked(self, index):
        return self.IsItemChecked(index) if _PHOENIX else self.IsChecked(index)

    def _set_checked(self, index, etat=True):
        self.CheckItem(index, etat)

    def Remplissage(self):
        self.ClearAll()
        self.InsertColumn(0, _(u"Individus"))
        self._suspend_checks = True
        try:
            personnes = sorted(
                self.dictPersonnes.items(),
                key=lambda item: ((item[1][0] or "") + " " + (item[1][1] or "")).upper(),
            )
            for key, valeurs in personnes:
                index = self.InsertItem(
                    self.GetItemCount(),
                    ((valeurs[0] or "") + " " + (valeurs[1] or "")).strip(),
                )
                self.SetItemData(index, key)
                self._set_checked(index, key in self.owner.selectionPersonnes)
        finally:
            self._suspend_checks = False
        wx.CallAfter(self.AjusterColonne)

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonne)
        event.Skip()

    def AjusterColonne(self):
        if self.GetColumnCount() and self.GetClientSize().GetWidth() > 0:
            self.SetColumnWidth(0, max(UTILS_Styles.Scale(180), self.GetClientSize().GetWidth() - 2))

    def OnItemActivated(self, event):
        self._suspend_checks = True
        try:
            self._set_checked(event.Index, not self._is_checked(event.Index))
        finally:
            self._suspend_checks = False
        self._sync_selection()

    def OnCheckItem(self, index, flag):
        if not self._suspend_checks:
            self._sync_selection()

    def OnNativeCheckItem(self, event):
        if not self._suspend_checks:
            self._sync_selection()
        event.Skip()

    def _sync_selection(self):
        selection = [
            self.GetItemData(index)
            for index in range(self.GetItemCount())
            if self._is_checked(index)
        ]
        self.owner.selectionPersonnes[:] = selection

    def Import_Personnes(self):
        DB = GestionDB.DB()
        DB.ExecuterReq(
            "SELECT IDpersonne, nom, prenom FROM personnes ORDER BY nom;"
        )
        donnees = DB.ResultatReq()
        DB.Close()
        return {
            IDpersonne: [nom, prenom]
            for IDpersonne, nom, prenom in donnees
        }


class listCtrl_Modeles(wx.ListCtrl, _CheckboxFallback):
    def __init__(self, parent, owner):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_VRULES | wx.BORDER_NONE,
        )
        if _PHOENIX:
            self.EnableCheckBoxes(True)
        else:
            CheckListCtrlMixin.__init__(self)
        self.owner = owner
        self._suspend_checks = False
        self.selections = []
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        if _PHOENIX:
            if hasattr(wx, "EVT_LIST_ITEM_CHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnNativeCheckItem)
            if hasattr(wx, "EVT_LIST_ITEM_UNCHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnNativeCheckItem)

    def _is_checked(self, index):
        return self.IsItemChecked(index) if _PHOENIX else self.IsChecked(index)

    def _set_checked(self, index, etat=True):
        self.CheckItem(index, etat)

    def Remplissage(self):
        self.dictModeles = self.Import_Modeles()
        self.ClearAll()
        self.InsertColumn(0, _(u"Nom"))
        self.InsertColumn(1, _(u"Description"))
        self._suspend_checks = True
        try:
            for key, valeurs in sorted(
                self.dictModeles.items(),
                key=lambda item: (item[1][0] or "").upper(),
            ):
                index = self.InsertItem(self.GetItemCount(), valeurs[0] or "")
                self.SetItem(index, 1, valeurs[1] or "")
                self.SetItemData(index, key)
                self._set_checked(index, key in self.selections)
        finally:
            self._suspend_checks = False
        wx.CallAfter(self.AjusterColonnes)

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0 or self.GetColumnCount() < 2:
            return
        nom = max(UTILS_Styles.Scale(160), int(largeur * 0.34))
        description = max(
            UTILS_Styles.Scale(240),
            largeur - nom - UTILS_Styles.GetSpacing("xs"),
        )
        self.SetColumnWidth(0, nom)
        self.SetColumnWidth(1, description)

    def OnItemActivated(self, event):
        self._suspend_checks = True
        try:
            self._set_checked(event.Index, not self._is_checked(event.Index))
        finally:
            self._suspend_checks = False
        self._sync_selection()

    def OnItemSelected(self, event):
        self.owner.boutonsEnabled(True, True, True)
        event.Skip()

    def OnItemDeselected(self, event):
        self.owner.boutonsEnabled(True, False, False)
        event.Skip()

    def OnCheckItem(self, index, flag):
        if not self._suspend_checks:
            self._sync_selection()

    def OnNativeCheckItem(self, event):
        if not self._suspend_checks:
            self._sync_selection()
        event.Skip()

    def _sync_selection(self):
        self.selections = [
            self.GetItemData(index)
            for index in range(self.GetItemCount())
            if self._is_checked(index)
        ]

    def Import_Modeles(self):
        DB = GestionDB.DB()
        DB.ExecuterReq(
            "SELECT IDmodele, nom, description FROM modeles_planning ORDER BY nom;"
        )
        donnees = DB.ResultatReq()
        DB.Close()
        return {
            IDmodele: [nom, description]
            for IDmodele, nom, description in donnees
        }

    def OnContextMenu(self, event):
        menu = UTILS_Adaptations.Menu()
        menu.Append(10, _(u"Créer un nouveau modèle"))
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)
        if self.GetFirstSelected() != -1:
            menu.AppendSeparator()
            menu.Append(20, _(u"Modifier"))
            menu.Append(40, _(u"Dupliquer"))
            menu.Append(30, _(u"Supprimer"))
            self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)
            self.Bind(wx.EVT_MENU, self.Menu_Dupliquer, id=40)
            self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)
        self.PopupMenu(menu)
        menu.Destroy()

    def Menu_Ajouter(self, event):
        self.owner.OnBoutonAjouter(None)

    def Menu_Modifier(self, event):
        self.owner.OnBoutonModifier(None)

    def Menu_Supprimer(self, event):
        self.owner.OnBoutonSupprimer(None)

    def Menu_Dupliquer(self, event):
        self.owner.OnBoutonDupliquer(None)


class Panel(CORE.Panel):
    """Même logique métier que le panel historique, coque wx moderne."""

    def __init__(
        self,
        parent,
        selectionLignes=None,
        selectionPersonnes=None,
        selectionDates=(None, None),
    ):
        wx.Panel.__init__(
            self,
            parent,
            -1,
            name="panel_applicModele",
            style=wx.TAB_TRAVERSAL,
        )
        self.parent = parent
        self.selectionLignes = list(selectionLignes or [])
        self.selectionPersonnes = list(selectionPersonnes or [])
        self.selectionDates = selectionDates
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self._depuis_fiche = hasattr(parent, "selectionLignes") and hasattr(
            parent, "selectionPersonnes"
        )

        self.section_parametres = CTRL_Section.Section(
            self,
            titre=_(u"Période et personnes"),
            niveau=2,
        )
        contenu_parametres = self.section_parametres.GetContentPanel()
        self.radio_btn_1 = wx.RadioButton(contenu_parametres, -1, u"", style=wx.RB_GROUP)
        self.radio_btn_2 = wx.RadioButton(
            contenu_parametres,
            -1,
            _(u"Selon une période et des personnes choisies"),
        )
        self.label_periode = CTRL_Texte.Label(contenu_parametres, _(u"Période"))
        self.date_debut = DatePickerCtrl(contenu_parametres, -1, style=DP_DROPDOWN)
        self.label_au = CTRL_Texte.BodySecondary(contenu_parametres, _(u"au"))
        self.date_fin = DatePickerCtrl(contenu_parametres, -1, style=DP_DROPDOWN)
        self.label_personnes = CTRL_Texte.Label(contenu_parametres, _(u"Personnes"))
        self.list_ctrl_personnes = listCtrl_Personnes(contenu_parametres, owner=self)
        self.list_ctrl_personnes.SetMinSize((-1, UTILS_Styles.Scale(120)))

        self.section_modeles = CTRL_Section.Section(
            self,
            titre=_(u"Modèles"),
            niveau=2,
        )
        contenu_modeles = self.section_modeles.GetContentPanel()
        self.list_ctrl_modeles = listCtrl_Modeles(contenu_modeles, owner=self)

        self.bouton_ajouter = CTRL_Bouton_image.CTRL(contenu_modeles, texte=_(u"Créer"))
        self.bouton_modifier = CTRL_Bouton_image.CTRL(contenu_modeles, texte=_(u"Modifier"))
        self.bouton_dupliquer = CTRL_Bouton_image.CTRL(contenu_modeles, texte=_(u"Dupliquer"))
        self.bouton_supprimer = CTRL_Bouton_image.CTRL(contenu_modeles, texte=_(u"Supprimer"))
        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Aide"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_OK,
            texte=_(u"Appliquer"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
        )

        self.__do_layout(contenu_parametres, contenu_modeles)
        self.__set_properties()

        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio1, self.radio_btn_1)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio2, self.radio_btn_2)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDupliquer, self.bouton_dupliquer)

        self.boutonsEnabled(True, False, False)
        self.SetLabelRadio1()
        self._initialiser_dates()

        # Compatibilité avec les quelques écrans historiques qui ajustent ces
        # éléments après construction.
        self.grid_sizer_manuel = self.sizer_manuel
        self.sizer_parametres_staticbox = self.section_parametres.titre

    def __set_properties(self):
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Créer un modèle")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Modifier le modèle sélectionné")))
        self.bouton_dupliquer.SetToolTip(wx.ToolTip(_(u"Dupliquer le modèle sélectionné")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Supprimer le modèle sélectionné")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Appliquer les modèles sélectionnés")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Annuler")))

    def __do_layout(self, contenu_parametres, contenu_modeles):
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        self.sizer_manuel = wx.BoxSizer(wx.VERTICAL)
        ligne_periode = wx.BoxSizer(wx.HORIZONTAL)
        ligne_periode.Add(self.label_periode, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_periode.Add(self.date_debut, 0, wx.RIGHT, field_gap)
        ligne_periode.Add(self.label_au, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_periode.Add(self.date_fin, 0)
        self.sizer_manuel.Add(ligne_periode, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        self.sizer_manuel.Add(self.label_personnes, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        self.sizer_manuel.Add(self.list_ctrl_personnes, 1, wx.EXPAND)

        parametres = wx.BoxSizer(wx.VERTICAL)
        parametres.Add(self.radio_btn_1, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        parametres.Add(self.radio_btn_2, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        parametres.Add(self.sizer_manuel, 1, wx.EXPAND)
        contenu_parametres.SetSizer(parametres)

        actions_modeles = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (
            self.bouton_ajouter,
            self.bouton_modifier,
            self.bouton_dupliquer,
            self.bouton_supprimer,
        ):
            actions_modeles.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, toolbar_gap)
        modeles = wx.BoxSizer(wx.VERTICAL)
        modeles.Add(actions_modeles, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        modeles.Add(self.list_ctrl_modeles, 1, wx.EXPAND)
        contenu_modeles.SetSizer(modeles)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, toolbar_gap)
        actions.Add(self.bouton_annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.section_parametres, 2, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(
            self.section_modeles,
            3,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        sizer.Add(
            actions,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        self.SetSizer(sizer)

    def _initialiser_dates(self):
        if self.selectionDates[0] is not None:
            date = wx.DateTime()
            date.Set(
                self.selectionDates[0].day,
                self.selectionDates[0].month - 1,
                self.selectionDates[0].year,
            )
            self.date_debut.SetValue(date)
        if self.selectionDates[1] is not None:
            date = wx.DateTime()
            date.Set(
                self.selectionDates[1].day,
                self.selectionDates[1].month - 1,
                self.selectionDates[1].year,
            )
            self.date_fin.SetValue(date)

    def SetLabelRadio1(self):
        if self._depuis_fiche:
            unite = _(u"date sélectionnée dans le calendrier") if len(self.selectionLignes) == 1 else _(u"dates sélectionnées dans le calendrier")
        else:
            unite = _(u"ligne sélectionnée dans le planning") if len(self.selectionLignes) == 1 else _(u"lignes sélectionnées dans le planning")
        if not self.selectionLignes:
            texte = _(
                u"Selon la sélection courante"
            )
        else:
            texte = _(u"Selon les %d %s") % (len(self.selectionLignes), unite)
        self.radio_btn_1.SetLabel(texte)
        utilise_selection = bool(self.selectionLignes)
        self.radio_btn_1.Enable(utilise_selection)
        if utilise_selection:
            self.radio_btn_1.SetValue(True)
            self.radio_btn_2.SetValue(False)
            self.ParamEnabled(False)
        else:
            self.radio_btn_1.SetValue(False)
            self.radio_btn_2.SetValue(True)
            self.ParamEnabled(True)

    def Fermer(self):
        dialog = _dialog_ancestor(self)
        if dialog is not None:
            dialog.EndModal(wx.ID_CANCEL)


class Dialog(wx.Dialog):
    def __init__(
        self,
        parent,
        selectionLignes=None,
        selectionPersonnes=None,
        selectionDates=(None, None),
    ):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title=_(u"Application d'un modèle"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.panel = Panel(
            self,
            selectionLignes=selectionLignes or [],
            selectionPersonnes=selectionPersonnes or [],
            selectionDates=selectionDates,
        )
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def Fermer(self):
        self.EndModal(wx.ID_CANCEL)


if __name__ == "__main__":
    import datetime
    app = wx.App(0)
    selection_lignes = [
        (1, datetime.date(2008, 3, 10)),
        (1, datetime.date(2008, 3, 11)),
    ]
    dlg = Dialog(None, selectionLignes=selection_lignes)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
