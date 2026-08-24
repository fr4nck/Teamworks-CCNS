#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Coque moderne de la saisie d'une candidature Recrutement."""

import datetime
import wx

import GestionDB
from Ctrl import CTRL_Bouton_image, CTRL_Section, CTRL_Texte
from Dlg import DLG_Saisie_candidature_core as CORE
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _

if "phoenix" in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else:
    from wx import DatePickerCtrl, DP_DROPDOWN


DEPOT_TYPES = (
    _(u"De vive voix"), _(u"Courrier"), _(u"Téléphone"), _(u"Main à main"),
    _(u"Email"), _(u"France Travail"), _(u"Organisateur"), _(u"Fédération"), _(u"Autre"),
)
DECISIONS = (_(u"Décision non prise"), _(u"Oui"), _(u"Non"))
REPONSE_TYPES = (
    _(u"De vive voix"), _(u"Courrier"), _(u"Téléphone"), _(u"Main à main"), _(u"Email"), _(u"Autre"),
)


def _ancestor_named(window, name):
    current = window
    while current is not None:
        try:
            if current.GetName() == name:
                return current
        except Exception:
            pass
        try:
            current = current.GetParent()
        except Exception:
            current = None
    return None


class ListBoxDisponibilites(wx.ListBox):
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
            self.Append(_(u"Du %s au %s") % (date_debut.strftime("%d/%m/%Y"), date_fin.strftime("%d/%m/%Y")))
            self.dictIndexes[index] = IDdisponibilite

    def GetIDselection(self):
        return self.dictIndexes.get(self.GetSelection())

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


class ChoiceEmploi(wx.Choice):
    """Sélecteur d'offre découplé du parent wx direct."""

    def __init__(self, parent, owner):
        wx.Choice.__init__(self, parent, choices=[])
        self.owner = owner
        self.dictIndexes = {}
        self.Bind(wx.EVT_CHOICE, self.OnChoice)

    def Remplissage(self, listeDonnees=None):
        if listeDonnees is None:
            listeDonnees = []
        self.dictIndexes = {}
        self.Clear()
        self.Append(_(u"Candidature spontanée"))
        for index, (IDemploi, intitule, date_debut, date_fin) in enumerate(listeDonnees, start=1):
            self.Append(intitule or _(u"Offre sans intitulé"))
            self.dictIndexes[index] = IDemploi
        self.Select(0)

    def GetIDselection(self):
        index = self.GetSelection()
        if index in (-1, 0):
            return 0
        return self.dictIndexes.get(index, 0)

    def SetIDselection(self, IDemploi):
        if not IDemploi:
            self.Select(0)
            return
        for index, IDemp in self.dictIndexes.items():
            if IDemploi == IDemp:
                self.Select(index)
                return
        self.Select(0)

    def OnChoice(self, event):
        index = self.GetSelection()
        if index in (-1, 0):
            return
        IDemploi = self.dictIndexes[index]

        DB = GestionDB.DB()
        req = """SELECT IDdisponibilite, date_debut, date_fin
        FROM emplois_dispo WHERE IDemploi=%d ORDER BY date_debut, date_fin; """ % IDemploi
        DB.ExecuterReq(req)
        liste = DB.ResultatReq()
        DB.Close()
        for IDdisponibilite, date_debut, date_fin in liste:
            date_debut = datetime.date(int(date_debut[:4]), int(date_debut[5:7]), int(date_debut[8:10]))
            date_fin = datetime.date(int(date_fin[:4]), int(date_fin[5:7]), int(date_fin[8:10]))
            self.owner.listeDisponibilites.append((None, date_debut, date_fin))
        self.owner.ctrl_periodes.Remplissage(self.owner.listeDisponibilites)

        DB = GestionDB.DB()
        req = """SELECT IDemploi_fonction, IDfonction FROM emplois_fonctions WHERE IDemploi=%d; """ % IDemploi
        DB.ExecuterReq(req)
        fonctions = [row[1] for row in DB.ResultatReq()]
        DB.Close()
        self.owner.ctrl_fonction.CocheListe(fonctions)

        DB = GestionDB.DB()
        req = """SELECT IDemploi_affectation, IDaffectation FROM emplois_affectations WHERE IDemploi=%d; """ % IDemploi
        DB.ExecuterReq(req)
        affectations = [row[1] for row in DB.ResultatReq()]
        DB.Close()
        self.owner.ctrl_affectations.CocheListe(affectations)


class Panel(CORE.Panel):
    """Interface moderne ; validation et persistance héritées du core."""

    def __init__(self, parent, IDcandidat=None, IDpersonne=None, IDcandidature=None):
        wx.Panel.__init__(self, parent, id=-1, name="panel_candidature", style=wx.TAB_TRAVERSAL)
        self.IDcandidat = IDcandidat
        self.IDpersonne = IDpersonne
        self.IDcandidature = IDcandidature
        self.listeDisponibilites = []
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.section_depot = CTRL_Section.Section(self, titre=_(u"Dépôt de candidature"), niveau=2, description=_(u"Date, canal de dépôt et remarques associées."))
        self.section_emploi = CTRL_Section.Section(self, titre=_(u"Offre d'emploi"), niveau=2, description=_(u"Offre liée à la candidature, ou candidature spontanée."))
        self.section_disponibilites = CTRL_Section.Section(self, titre=_(u"Disponibilités"), niveau=2, description=_(u"Périodes pendant lesquelles la personne est disponible."))
        self.section_poste = CTRL_Section.Section(self, titre=_(u"Poste souhaité"), niveau=2, description=_(u"Fonctions et affectations recherchées."))
        self.section_reponse = CTRL_Section.Section(self, titre=_(u"Réponse"), niveau=2, description=_(u"Décision et suivi de la réponse communiquée au candidat."))

        self._creer_depot(self.section_depot.GetContentPanel())
        self._creer_emploi(self.section_emploi.GetContentPanel())
        self._creer_disponibilites(self.section_disponibilites.GetContentPanel())
        self._creer_poste(self.section_poste.GetContentPanel())
        self._creer_reponse(self.section_reponse.GetContentPanel())
        self._creer_commandes()
        self._installer_layout()
        self._bind_events()
        self._set_properties()

        if self.IDcandidature is not None:
            self.Importation()
        self.OnCheckReponse(None)
        self.OnCheckReponseCommuniquee(None)

    def _input(self, control):
        control.SetMinSize((-1, UTILS_Styles.GetControlMetric("input_min_height")))
        return control

    def _creer_depot(self, parent):
        self.label_date = CTRL_Texte.Label(parent, _(u"Date"))
        self.ctrl_date = DatePickerCtrl(parent, -1, style=DP_DROPDOWN)
        self.label_type = CTRL_Texte.Label(parent, _(u"Canal de dépôt"))
        self.ctrl_type = wx.Choice(parent, choices=list(DEPOT_TYPES))
        self.ctrl_type.SetSelection(0)
        self.label_acte_remarques = CTRL_Texte.Label(parent, _(u"Remarques"))
        self.ctrl_acte_remarques = self._input(wx.TextCtrl(parent, -1, u""))
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        ligne = wx.BoxSizer(wx.HORIZONTAL)
        date_bloc = wx.BoxSizer(wx.VERTICAL)
        date_bloc.Add(self.label_date, 0, wx.EXPAND)
        date_bloc.AddSpacer(gap)
        date_bloc.Add(self.ctrl_date, 0, wx.EXPAND)
        type_bloc = wx.BoxSizer(wx.VERTICAL)
        type_bloc.Add(self.label_type, 0, wx.EXPAND)
        type_bloc.AddSpacer(gap)
        type_bloc.Add(self.ctrl_type, 0, wx.EXPAND)
        ligne.Add(date_bloc, 1, wx.EXPAND | wx.RIGHT, gap)
        ligne.Add(type_bloc, 2, wx.EXPAND)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(ligne, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.label_acte_remarques, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.ctrl_acte_remarques, 0, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_emploi(self, parent):
        self.label_emploi = CTRL_Texte.Label(parent, _(u"Offre"))
        self.ctrl_emploi = ChoiceEmploi(parent, self)
        self.ctrl_emploi.Remplissage(self.Importation_emplois())
        self.bouton_emplois = CTRL_Bouton_image.CTRL(parent, texte=_(u"Gérer les offres…"))
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_emploi, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.ctrl_emploi, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.bouton_emplois, 0)
        parent.SetSizer(sizer)

    def _creer_disponibilites(self, parent):
        self.label_periodes = CTRL_Texte.Label(parent, _(u"Périodes"))
        self.ctrl_periodes = ListBoxDisponibilites(parent, self)
        self.ctrl_periodes.SetMinSize((-1, UTILS_Styles.Scale(140)))
        self.bouton_ajouter_periode = CTRL_Bouton_image.CTRL(parent, texte=_(u"Ajouter"))
        self.bouton_modifier_periode = CTRL_Bouton_image.CTRL(parent, texte=_(u"Modifier"))
        self.bouton_supprimer_periode = CTRL_Bouton_image.CTRL(parent, texte=_(u"Supprimer"))
        self.label_periodes_remarques = CTRL_Texte.Label(parent, _(u"Remarques"))
        self.ctrl_periodes_remarques = self._input(wx.TextCtrl(parent, -1, u""))
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
        ctrl.SetMinSize((-1, UTILS_Styles.Scale(120)))
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
        self.label_fonction, self.ctrl_fonction, self.bouton_fonctions, fonctions = self._liste_geree(parent, _(u"Fonctions"), self.Importation_fonctions(), self.OnGestionFonctions)
        self.label_affectation, self.ctrl_affectations, self.bouton_affectations, affectations = self._liste_geree(parent, _(u"Affectations"), self.Importation_affectations(), self.OnGestionAffectations)
        self.label_poste_remarques = CTRL_Texte.Label(parent, _(u"Remarques"))
        self.ctrl_poste_remarques = self._input(wx.TextCtrl(parent, -1, ""))
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

    def _creer_reponse(self, parent):
        self.label_decision = CTRL_Texte.Label(parent, _(u"Décision"))
        self.ctrl_decision = wx.Choice(parent, choices=list(DECISIONS))
        self.ctrl_decision.SetSelection(0)
        self.label_reponse_remarques = CTRL_Texte.Label(parent, _(u"Remarques"))
        self.ctrl_reponse_remarques = self._input(wx.TextCtrl(parent, -1, ""))
        self.label_reponse = CTRL_Texte.Label(parent, _(u"Suivi de la réponse"))
        self.ctrl_reponse_obligatoire = wx.CheckBox(parent, -1, _(u"Réponse obligatoire"))
        self.ctrl_reponse_communiquee = wx.CheckBox(parent, -1, _(u"Réponse communiquée au candidat"))
        self.label_reponse1 = CTRL_Texte.BodySmall(parent, _(u"Date d'envoi"))
        self.date_envoi_reponse = DatePickerCtrl(parent, -1, style=DP_DROPDOWN)
        self.label_reponse2 = CTRL_Texte.BodySmall(parent, _(u"Canal"))
        self.ctrl_type_reponse = wx.Choice(parent, choices=list(REPONSE_TYPES))
        self.ctrl_type_reponse.SetSelection(0)
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        suivi = wx.BoxSizer(wx.HORIZONTAL)
        date_bloc = wx.BoxSizer(wx.VERTICAL)
        date_bloc.Add(self.label_reponse1, 0, wx.EXPAND)
        date_bloc.AddSpacer(gap)
        date_bloc.Add(self.date_envoi_reponse, 0, wx.EXPAND)
        type_bloc = wx.BoxSizer(wx.VERTICAL)
        type_bloc.Add(self.label_reponse2, 0, wx.EXPAND)
        type_bloc.AddSpacer(gap)
        type_bloc.Add(self.ctrl_type_reponse, 0, wx.EXPAND)
        suivi.Add(date_bloc, 1, wx.EXPAND | wx.RIGHT, gap)
        suivi.Add(type_bloc, 1, wx.EXPAND)
        sizer = wx.BoxSizer(wx.VERTICAL)
        for controle in (self.label_decision, self.ctrl_decision, self.label_reponse_remarques, self.ctrl_reponse_remarques, self.label_reponse, self.ctrl_reponse_obligatoire, self.ctrl_reponse_communiquee):
            if sizer.GetItemCount():
                sizer.AddSpacer(gap)
            sizer.Add(controle, 0, wx.EXPAND if isinstance(controle, (wx.Choice, wx.TextCtrl, wx.StaticText)) else 0)
        sizer.AddSpacer(gap)
        sizer.Add(suivi, 0, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_commandes(self):
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"))
        self.bouton_courrier = CTRL_Bouton_image.CTRL(self, texte=_(u"Courrier / email"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_(u"Annuler"))

    def _installer_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        control_gap = UTILS_Styles.GetLayoutSpacing("control_gap")
        gauche = wx.BoxSizer(wx.VERTICAL)
        gauche.Add(self.section_depot, 0, wx.EXPAND)
        gauche.AddSpacer(gap)
        gauche.Add(self.section_emploi, 0, wx.EXPAND)
        gauche.AddSpacer(gap)
        gauche.Add(self.section_disponibilites, 1, wx.EXPAND)
        droite = wx.BoxSizer(wx.VERTICAL)
        droite.Add(self.section_poste, 1, wx.EXPAND)
        droite.AddSpacer(gap)
        droite.Add(self.section_reponse, 1, wx.EXPAND)
        contenu = wx.BoxSizer(wx.HORIZONTAL)
        contenu.Add(gauche, 1, wx.EXPAND | wx.RIGHT, gap)
        contenu.Add(droite, 1, wx.EXPAND)
        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0, wx.RIGHT, control_gap)
        actions.Add(self.bouton_courrier, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, control_gap)
        actions.Add(self.bouton_annuler, 0)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(contenu, 1, wx.EXPAND | wx.ALL, padding)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)

    def _bind_events(self):
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_courrier, self.bouton_courrier)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)
        self.Bind(wx.EVT_BUTTON, self.OnAjouterPeriode, self.bouton_ajouter_periode)
        self.Bind(wx.EVT_BUTTON, self.OnModifierPeriode, self.bouton_modifier_periode)
        self.Bind(wx.EVT_BUTTON, self.OnSupprimerPeriode, self.bouton_supprimer_periode)
        self.Bind(wx.EVT_BUTTON, self.OnGestionEmplois, self.bouton_emplois)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckReponse, self.ctrl_reponse_obligatoire)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckReponseCommuniquee, self.ctrl_reponse_communiquee)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def _set_properties(self):
        self.ctrl_type.SetToolTip(wx.ToolTip(_(u"Canal par lequel la candidature a été déposée")))
        self.ctrl_emploi.SetToolTip(wx.ToolTip(_(u"Offre d'emploi associée à cette candidature")))
        self.ctrl_decision.SetToolTip(wx.ToolTip(_(u"Décision concernant cette candidature")))


class Dialog(wx.Dialog):
    def __init__(self, parent, IDcandidat=None, IDpersonne=None, IDcandidature=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.panel = Panel(self, IDcandidat=IDcandidat, IDpersonne=IDpersonne, IDcandidature=IDcandidature)
        nom = self.GetNomCandidat(IDcandidat, IDpersonne)
        action = _(u"Saisie") if IDcandidature is None else _(u"Modification")
        self.SetTitle(_(u"%s d'une candidature pour %s") % (action, nom) if nom else _(u"%s d'une candidature") % action)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "workspace")

    def Fermer(self):
        parent = self.GetParent()
        try:
            if parent.GetName() == "OL_candidatures":
                parent.MAJ()
        except Exception:
            pass
        resume = _ancestor_named(parent, "panel_resume")
        recrutement = _ancestor_named(parent, "Recrutement")
        if recrutement is not None:
            try:
                recrutement.MAJpanel(MAJpanelResume=False)
            except Exception:
                pass
            try:
                recrutement.gadget_informations.MAJ()
            except Exception:
                pass
        if resume is not None:
            try:
                resume.MAJlabelsPages("candidatures")
            except Exception:
                pass
        self.EndModal(wx.ID_CANCEL)

    def GetNomCandidat(self, IDcandidat=None, IDpersonne=None):
        DB = GestionDB.DB()
        if IDpersonne in (None, 0):
            if IDcandidat in (None, 0):
                DB.Close()
                return ""
            req = """SELECT civilite, nom, prenom FROM candidats WHERE IDcandidat=%d; """ % IDcandidat
        else:
            req = """SELECT civilite, nom, prenom FROM personnes WHERE IDpersonne=%d; """ % IDpersonne
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()
        if not rows:
            return ""
        civilite, nom, prenom = rows[0]
        return u"%s %s" % (nom or "", prenom or "")


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, IDcandidat=3, IDpersonne=None, IDcandidature=None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
