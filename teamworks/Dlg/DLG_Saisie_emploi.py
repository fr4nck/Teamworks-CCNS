#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Coque moderne de la saisie d'une offre d'emploi Recrutement."""

import wx
import six

from Ctrl import CTRL_Bouton_image, CTRL_Section, CTRL_Texte
from Dlg import DLG_Saisie_emploi_core as CORE
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _

if "phoenix" in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else:
    from wx import DatePickerCtrl, DP_DROPDOWN

# Le moteur historique utilise six dans la suppression d'une période sur
# certaines branches anciennes sans l'importer explicitement.
CORE.six = six


class ListBoxDisponibilites(wx.ListBox):
    """Liste de périodes moderne, avec menu textuel sans micro-icônes."""

    def __init__(self, parent, owner):
        wx.ListBox.__init__(self, parent, choices=[])
        self.owner = owner
        self.dictIndexes = {}
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnDoubleClick)

    def Remplissage(self, listeDisponibilites=None):
        if listeDisponibilites is None:
            listeDisponibilites = []
        self.dictIndexes = {}
        self.Clear()
        for index, (IDdisponibilite, date_debut, date_fin) in enumerate(listeDisponibilites):
            texte = _(u"Du %s au %s") % (
                date_debut.strftime("%d/%m/%Y"),
                date_fin.strftime("%d/%m/%Y"),
            )
            self.Append(texte)
            self.dictIndexes[index] = IDdisponibilite

    def GetIDselection(self):
        index = self.GetSelection()
        return self.dictIndexes.get(index)

    def OnDoubleClick(self, event):
        if self.GetSelection() != wx.NOT_FOUND:
            self.owner.OnModifierPeriode(None)

    def OnContextMenu(self, event):
        index = self.HitTest(event.GetPosition())
        if index != wx.NOT_FOUND:
            self.SetSelection(index)
        menu = wx.Menu()
        id_ajouter = wx.NewIdRef()
        menu.Append(id_ajouter, _(u"Ajouter une période"))
        self.Bind(wx.EVT_MENU, lambda evt: self.owner.OnAjouterPeriode(None), id=id_ajouter)
        if index != wx.NOT_FOUND:
            menu.AppendSeparator()
            id_modifier = wx.NewIdRef()
            id_supprimer = wx.NewIdRef()
            menu.Append(id_modifier, _(u"Modifier la période"))
            menu.Append(id_supprimer, _(u"Supprimer la période"))
            self.Bind(wx.EVT_MENU, lambda evt: self.owner.OnModifierPeriode(None), id=id_modifier)
            self.Bind(wx.EVT_MENU, lambda evt: self.owner.OnSupprimerPeriode(None), id=id_supprimer)
        self.PopupMenu(menu)
        menu.Destroy()


class CheckListBox(CORE.CheckListBox):
    def __init__(self, parent):
        CORE.CheckListBox.__init__(self, parent)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))


BitmapComboBox = CORE.BitmapComboBox


class Panel(CORE.Panel):
    """Interface moderne ; toutes les méthodes métier sont héritées du core."""

    def __init__(self, parent, IDemploi=None):
        wx.Panel.__init__(self, parent, id=-1, name="panel_emploi", style=wx.TAB_TRAVERSAL)
        self.IDemploi = IDemploi
        self.listeDisponibilites = []
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.section_generalites = CTRL_Section.Section(
            self,
            titre=_(u"Généralités"),
            niveau=2,
            description=_(u"Informations principales et période de publication de l'offre."),
        )
        self.section_disponibilites = CTRL_Section.Section(
            self,
            titre=_(u"Disponibilités"),
            niveau=2,
            description=_(u"Périodes pendant lesquelles le poste doit être pourvu."),
        )
        self.section_poste = CTRL_Section.Section(
            self,
            titre=_(u"Poste"),
            niveau=2,
            description=_(u"Fonctions et affectations recherchées."),
        )
        self.section_diffusion = CTRL_Section.Section(
            self,
            titre=_(u"Diffusion de l'offre"),
            niveau=2,
            description=_(u"Canaux utilisés pour publier ou relayer l'offre."),
        )

        self._creer_generalites(self.section_generalites.GetContentPanel())
        self._creer_disponibilites(self.section_disponibilites.GetContentPanel())
        self._creer_poste(self.section_poste.GetContentPanel())
        self._creer_diffusion(self.section_diffusion.GetContentPanel())
        self._creer_commandes()
        self._installer_layout()
        self._set_properties()
        self._bind_events()

        if self.IDemploi is not None:
            self.Importation()

    def _input_height(self, controle):
        controle.SetMinSize((-1, UTILS_Styles.GetControlMetric("input_min_height")))
        return controle

    def _creer_generalites(self, parent):
        self.label_date_debut = CTRL_Texte.Label(parent, _(u"Lancement"))
        self.ctrl_date_debut = DatePickerCtrl(parent, -1, style=DP_DROPDOWN)
        self.label_date_fin = CTRL_Texte.Label(parent, _(u"Clôture"))
        self.ctrl_date_fin = DatePickerCtrl(parent, -1, style=DP_DROPDOWN)
        self.label_intitule = CTRL_Texte.Label(parent, _(u"Intitulé"))
        self.ctrl_intitule = self._input_height(wx.TextCtrl(parent, -1, ""))
        self.label_detail = CTRL_Texte.Label(parent, _(u"Détail"))
        self.ctrl_detail = wx.TextCtrl(parent, -1, "", style=wx.TE_MULTILINE)
        self.ctrl_detail.SetMinSize((-1, UTILS_Styles.Scale(140)))
        self.label_reference = CTRL_Texte.Label(parent, _(u"Référence France Travail / offre"))
        self.ctrl_reference = self._input_height(wx.TextCtrl(parent, -1, ""))

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        dates = wx.BoxSizer(wx.HORIZONTAL)
        for label, controle in (
            (self.label_date_debut, self.ctrl_date_debut),
            (self.label_date_fin, self.ctrl_date_fin),
        ):
            bloc = wx.BoxSizer(wx.VERTICAL)
            bloc.Add(label, 0, wx.EXPAND | wx.BOTTOM, gap)
            bloc.Add(controle, 0, wx.EXPAND)
            dates.Add(bloc, 1, wx.EXPAND | (wx.RIGHT if controle is self.ctrl_date_debut else 0), gap)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(dates, 0, wx.EXPAND)
        for label, controle, proportion in (
            (self.label_intitule, self.ctrl_intitule, 0),
            (self.label_detail, self.ctrl_detail, 1),
            (self.label_reference, self.ctrl_reference, 0),
        ):
            sizer.AddSpacer(gap)
            sizer.Add(label, 0, wx.EXPAND)
            sizer.AddSpacer(gap)
            sizer.Add(controle, proportion, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_disponibilites(self, parent):
        self.label_periodes = CTRL_Texte.Label(parent, _(u"Périodes"))
        self.ctrl_periodes = ListBoxDisponibilites(parent, self)
        self.ctrl_periodes.SetMinSize((-1, UTILS_Styles.Scale(130)))
        self.bouton_ajouter_periode = CTRL_Bouton_image.CTRL(parent, texte=_(u"Ajouter"))
        self.bouton_modifier_periode = CTRL_Bouton_image.CTRL(parent, texte=_(u"Modifier"))
        self.bouton_supprimer_periode = CTRL_Bouton_image.CTRL(parent, texte=_(u"Supprimer"))
        self.label_periodes_remarques = CTRL_Texte.Label(parent, _(u"Remarques"))
        self.ctrl_periodes_remarques = self._input_height(wx.TextCtrl(parent, -1, u""))

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        actions = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (self.bouton_ajouter_periode, self.bouton_modifier_periode, self.bouton_supprimer_periode):
            actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_periodes, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.ctrl_periodes, 1, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(actions, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.label_periodes_remarques, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.ctrl_periodes_remarques, 0, wx.EXPAND)
        parent.SetSizer(sizer)

    def _liste_geree(self, parent, titre, donnees, handler):
        label = CTRL_Texte.Label(parent, titre)
        ctrl = CheckListBox(parent)
        ctrl.Remplissage(donnees)
        ctrl.SetMinSize((-1, UTILS_Styles.Scale(110)))
        bouton = CTRL_Bouton_image.CTRL(parent, texte=_(u"Gérer…"))
        bouton.Bind(wx.EVT_BUTTON, handler)
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        bloc = wx.BoxSizer(wx.VERTICAL)
        bloc.Add(label, 0, wx.EXPAND)
        bloc.AddSpacer(gap)
        bloc.Add(ctrl, 1, wx.EXPAND)
        bloc.AddSpacer(gap)
        bloc.Add(bouton, 0)
        return label, ctrl, bouton, bloc

    def _creer_poste(self, parent):
        self.label_fonction, self.ctrl_fonction, self.bouton_fonctions, fonctions = self._liste_geree(
            parent, _(u"Fonctions"), self.Importation_fonctions(), self.OnGestionFonctions
        )
        self.label_affectation, self.ctrl_affectations, self.bouton_affectations, affectations = self._liste_geree(
            parent, _(u"Affectations"), self.Importation_affectations(), self.OnGestionAffectations
        )
        self.label_poste_remarques = CTRL_Texte.Label(parent, _(u"Remarques"))
        self.ctrl_poste_remarques = self._input_height(wx.TextCtrl(parent, -1, ""))

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        listes = wx.BoxSizer(wx.HORIZONTAL)
        listes.Add(fonctions, 1, wx.EXPAND | wx.RIGHT, gap)
        listes.Add(affectations, 1, wx.EXPAND)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(listes, 1, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.label_poste_remarques, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.ctrl_poste_remarques, 0, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_diffusion(self, parent):
        self.label_diffuseurs, self.ctrl_diffuseurs, self.bouton_diffuseurs, bloc = self._liste_geree(
            parent, _(u"Diffuseurs"), self.Importation_diffuseurs(), self.OnGestionDiffuseurs
        )
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(bloc, 1, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_commandes(self):
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_(u"Annuler"))

    def _installer_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        control_gap = UTILS_Styles.GetLayoutSpacing("control_gap")

        gauche = wx.BoxSizer(wx.VERTICAL)
        gauche.Add(self.section_generalites, 2, wx.EXPAND)
        gauche.AddSpacer(gap)
        gauche.Add(self.section_disponibilites, 1, wx.EXPAND)
        droite = wx.BoxSizer(wx.VERTICAL)
        droite.Add(self.section_poste, 2, wx.EXPAND)
        droite.AddSpacer(gap)
        droite.Add(self.section_diffusion, 1, wx.EXPAND)
        contenu = wx.BoxSizer(wx.HORIZONTAL)
        contenu.Add(gauche, 1, wx.EXPAND | wx.RIGHT, gap)
        contenu.Add(droite, 1, wx.EXPAND)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, control_gap)
        actions.Add(self.bouton_annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(contenu, 1, wx.EXPAND | wx.ALL, padding)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)

    def _set_properties(self):
        self.ctrl_date_debut.SetToolTip(wx.ToolTip(_(u"Date de lancement de l'offre")))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip(_(u"Date de clôture du recrutement")))
        self.ctrl_intitule.SetToolTip(wx.ToolTip(_(u"Intitulé de l'offre")))
        self.ctrl_detail.SetToolTip(wx.ToolTip(_(u"Description détaillée de l'offre")))
        self.ctrl_reference.SetToolTip(wx.ToolTip(_(u"Référence externe de l'offre, si elle existe")))

    def _bind_events(self):
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)
        self.Bind(wx.EVT_BUTTON, self.OnAjouterPeriode, self.bouton_ajouter_periode)
        self.Bind(wx.EVT_BUTTON, self.OnModifierPeriode, self.bouton_modifier_periode)
        self.Bind(wx.EVT_BUTTON, self.OnSupprimerPeriode, self.bouton_supprimer_periode)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)


class Dialog(wx.Dialog):
    def __init__(self, parent, IDemploi=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.panel = Panel(self, IDemploi=IDemploi)
        self.SetTitle(
            _(u"Saisie d'une offre d'emploi")
            if IDemploi is None
            else _(u"Modification d'une offre d'emploi")
        )
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def Fermer(self):
        self.MAJparents()
        self.EndModal(wx.ID_CANCEL)

    def MAJparents(self):
        parent = self.GetParent()
        try:
            if parent.GetName() == "config_emploi":
                parent.MAJpanel()
            if parent.GetName() == "OL_emplois":
                parent.MAJ()
        except Exception:
            pass


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, IDemploi=None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
