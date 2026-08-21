#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Coque moderne de la fiche Candidat du module Recrutement."""

import sqlite3
import wx
import wx.lib.masked as masked

import Chemins
import GestionDB
from Ctrl import CTRL_Bouton_image, CTRL_Section, CTRL_Texte
from Ctrl import CTRL_Recrutement_core as RECRUTEMENT_CORE
from Dlg import DLG_Gestion_villes
from Dlg import DLG_Saisie_candidat_core as CORE
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


class ListCtrlCoords(wx.ListCtrl):
    """Coordonnées textuelles : la catégorie est une donnée, pas une couleur."""

    def __init__(self, parent, owner):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES)
        self.owner = owner
        self.parent = owner
        self.DictCoords = {}
        self.InsertColumn(0, _(u"Type"))
        self.InsertColumn(1, _(u"Coordonnée"))
        self.InsertColumn(2, _(u"Intitulé"))
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Remplissage()

    def Remplissage(self):
        self.DeleteAllItems()
        self.DictCoords = {}
        DB = GestionDB.DB()
        req = """SELECT IDcoord, IDcandidat, categorie, texte, intitule
        FROM coords_candidats WHERE IDcandidat=%d ORDER BY categorie, texte;""" % (self.owner.IDcandidat or 0)
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()
        for index, row in enumerate(rows):
            IDcoord, IDcandidat, categorie, texte, intitule = row
            self.DictCoords[IDcoord] = row
            self.InsertItem(index, categorie or "")
            self.SetItem(index, 1, texte or "")
            self.SetItem(index, 2, intitule or "")
            self.SetItemData(index, IDcoord)
        self._ajuster_colonnes()

    def _ajuster_colonnes(self):
        largeur = max(300, self.GetClientSize().width)
        self.SetColumnWidth(0, max(80, int(largeur * 0.18)))
        self.SetColumnWidth(1, max(140, int(largeur * 0.48)))
        self.SetColumnWidth(2, max(100, largeur - self.GetColumnWidth(0) - self.GetColumnWidth(1) - 8))

    def OnSize(self, event):
        self._ajuster_colonnes()
        event.Skip()

    def OnItemActivated(self, event):
        self.owner.ModifierCoord(None)

    def OnContextMenu(self, event):
        index = self.GetFirstSelected()
        menu = wx.Menu()
        id_add = wx.NewIdRef()
        menu.Append(id_add, _(u"Ajouter une coordonnée"))
        self.Bind(wx.EVT_MENU, lambda evt: self.owner.AjouterCoord(None), id=id_add)
        if index != -1:
            menu.AppendSeparator()
            id_edit = wx.NewIdRef()
            id_delete = wx.NewIdRef()
            menu.Append(id_edit, _(u"Modifier"))
            menu.Append(id_delete, _(u"Supprimer"))
            self.Bind(wx.EVT_MENU, lambda evt: self.owner.ModifierCoord(None), id=id_edit)
            self.Bind(wx.EVT_MENU, lambda evt: self.owner.SupprimerCoord(None), id=id_delete)
            IDcoord = self.GetItemData(index)
            row = self.DictCoords.get(IDcoord)
            if row and row[2] == "Email":
                menu.AppendSeparator()
                id_mail = wx.NewIdRef()
                menu.Append(id_mail, _(u"Envoyer un email"))
                self.Bind(wx.EVT_MENU, lambda evt, adresse=row[3]: CORE.FonctionsPerso.EnvoyerMail(adresses=(adresse,)), id=id_mail)
        self.PopupMenu(menu)
        menu.Destroy()


class ListCtrlDiplomes(wx.ListCtrl):
    def __init__(self, parent, owner):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL | wx.LC_HRULES)
        self.owner = owner
        self.IDcandidat = owner.IDcandidat
        self.listeDiplomes = []
        self.DictDiplomes = {}
        self.InsertColumn(0, _(u"Qualification"))
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda evt: self.owner.OnBoutonQualifications(None))
        self.Remplissage()

    def Remplissage(self):
        self.DeleteAllItems()
        self.DictDiplomes = {}
        self.listeDiplomes = []
        DB = GestionDB.DB()
        req = """SELECT IDdiplome, diplomes_candidats.IDtype_diplome, nom_diplome
        FROM diplomes_candidats, types_diplomes
        WHERE diplomes_candidats.IDtype_diplome=types_diplomes.IDtype_diplome
        AND IDcandidat=%d ORDER BY nom_diplome;""" % self.IDcandidat
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()
        for index, (IDdiplome, IDtype_diplome, nom_diplome) in enumerate(rows):
            self.DictDiplomes[IDdiplome] = (IDtype_diplome, nom_diplome)
            self.listeDiplomes.append(IDtype_diplome)
            self.InsertItem(index, nom_diplome or "")
            self.SetItemData(index, IDdiplome)
        self.SetColumnWidth(0, max(120, self.GetClientSize().width - 8))

    def OnSize(self, event):
        self.SetColumnWidth(0, max(120, self.GetClientSize().width - 8))
        event.Skip()


class Panel(CORE.Panel):
    """Interface moderne ; toute la logique métier reste héritée du core."""

    def __init__(self, parent, IDcandidat=None):
        wx.Panel.__init__(self, parent, id=-1, name="panel_candidat", style=wx.TAB_TRAVERSAL)
        self.IDcandidat = IDcandidat
        if self.IDcandidat is None:
            self.IDcandidat = self.CreationIDfiche()
            self.nouvelleFiche = True
        else:
            self.nouvelleFiche = False
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        con = sqlite3.connect(Chemins.GetStaticPath("Databases/Villes.db3"))
        cur = con.cursor()
        cur.execute("SELECT ville, cp FROM villes")
        self.listeVillesTmp = cur.fetchall()
        con.close()
        self.listeVilles = [(nom, "%05d" % cp) for nom, cp in self.listeVillesTmp]
        self.listeNomsVilles = [nom for nom, cp in self.listeVillesTmp]

        self.section_identite = CTRL_Section.Section(self, titre=_(u"Identité"), niveau=2)
        self.section_adresse = CTRL_Section.Section(self, titre=_(u"Adresse"), niveau=2)
        self.section_coords = CTRL_Section.Section(self, titre=_(u"Coordonnées"), niveau=2)
        self.section_qualifications = CTRL_Section.Section(self, titre=_(u"Qualifications"), niveau=2)
        self.section_candidatures = CTRL_Section.Section(self, titre=_(u"Candidatures"), niveau=2)
        self.section_entretiens = CTRL_Section.Section(self, titre=_(u"Entretiens"), niveau=2)
        self.section_memo = CTRL_Section.Section(self, titre=_(u"Mémo"), niveau=2)

        self._creer_identite(self.section_identite.GetContentPanel())
        self._creer_adresse(self.section_adresse.GetContentPanel())
        self._creer_coords(self.section_coords.GetContentPanel())
        self._creer_qualifications(self.section_qualifications.GetContentPanel())
        self._creer_candidatures(self.section_candidatures.GetContentPanel())
        self._creer_entretiens(self.section_entretiens.GetContentPanel())
        self._creer_memo(self.section_memo.GetContentPanel())
        self._creer_commandes()
        self._installer_layout()
        self._bind_events()
        self._set_properties()

        if self.IDcandidat is not None and not self.nouvelleFiche:
            self.Importation()
            self.MaJ_DateNaiss()
        self.OnRadioDateNaiss(None)
        if self.nouvelleFiche:
            self.ctrl_nom.SetFocus()
        else:
            self.bouton_ok.SetFocus()

    def _input(self, controle):
        controle.SetMinSize((-1, UTILS_Styles.GetControlMetric("input_min_height")))
        return controle

    def _creer_identite(self, parent):
        self.label_civilite = CTRL_Texte.Label(parent, _(u"Civilité"))
        self.ctrl_civilite = wx.Choice(parent, -1, choices=[_(u"Mr"), _(u"Melle"), _(u"Mme")])
        self.ctrl_civilite.SetSelection(0)
        self.label_nom = CTRL_Texte.Label(parent, _(u"Nom"))
        self.ctrl_nom = self._input(wx.TextCtrl(parent, -1, u""))
        self.ctrl_nom.SetFont(UTILS_Styles.GetFont("body-large"))
        self.label_prenom = CTRL_Texte.Label(parent, _(u"Prénom"))
        self.ctrl_prenom = self._input(wx.TextCtrl(parent, -1, u""))
        self.ctrl_prenom.SetFont(UTILS_Styles.GetFont("body-large"))
        self.label_date_naiss = CTRL_Texte.Label(parent, _(u"Date de naissance"))
        self.ctrl_radio_1 = wx.RadioButton(parent, -1, _(u"Date connue"), style=wx.RB_GROUP)
        self.ctrl_date_naiss = masked.TextCtrl(parent, -1, "", mask="##/##/####")
        self.ctrl_age_1 = self._input(wx.TextCtrl(parent, -1, "", style=wx.TE_READONLY))
        self.ctrl_radio_2 = wx.RadioButton(parent, -1, _(u"Âge uniquement"))
        self.label_age = CTRL_Texte.Label(parent, _(u"Âge"))
        self.ctrl_age_2 = self._input(wx.TextCtrl(parent, -1, ""))
        self.label_ans = CTRL_Texte.BodySmall(parent, _(u"ans"))

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        ligne_noms = wx.BoxSizer(wx.HORIZONTAL)
        for label, ctrl in ((self.label_civilite, self.ctrl_civilite), (self.label_nom, self.ctrl_nom), (self.label_prenom, self.ctrl_prenom)):
            bloc = wx.BoxSizer(wx.VERTICAL)
            bloc.Add(label, 0, wx.EXPAND)
            bloc.AddSpacer(gap)
            bloc.Add(ctrl, 0, wx.EXPAND)
            ligne_noms.Add(bloc, 1 if ctrl is not self.ctrl_civilite else 0, wx.EXPAND | wx.RIGHT, gap)
        sizer.Add(ligne_noms, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.label_date_naiss, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        ligne_date = wx.BoxSizer(wx.HORIZONTAL)
        ligne_date.Add(self.ctrl_radio_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, gap)
        ligne_date.Add(self.ctrl_date_naiss, 1, wx.RIGHT, gap)
        ligne_date.Add(self.ctrl_age_1, 1)
        sizer.Add(ligne_date, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        ligne_age = wx.BoxSizer(wx.HORIZONTAL)
        ligne_age.Add(self.ctrl_radio_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, gap)
        ligne_age.Add(self.label_age, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, gap)
        ligne_age.Add(self.ctrl_age_2, 1, wx.RIGHT, gap)
        ligne_age.Add(self.label_ans, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(ligne_age, 0, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_adresse(self, parent):
        self.label_adresse = CTRL_Texte.Label(parent, _(u"Adresse"))
        self.ctrl_adresse = wx.TextCtrl(parent, -1, u"", style=wx.TE_MULTILINE)
        self.ctrl_adresse.SetMinSize((-1, UTILS_Styles.Scale(90)))
        self.label_cp = CTRL_Texte.Label(parent, _(u"Code postal"))
        self.ctrl_cp = CORE.TextCtrlCp(parent, value="", listeVilles=self.listeVilles, mask="#####")
        self.label_ville = CTRL_Texte.Label(parent, _(u"Ville"))
        self.ctrl_ville = CORE.TextCtrlVille(parent, value="", ctrlCp=self.ctrl_cp, listeVilles=self.listeVilles, listeNomsVilles=self.listeNomsVilles)
        self.ctrl_cp.ctrlVille = self.ctrl_ville
        self.bouton_villes = CTRL_Bouton_image.CTRL(parent, texte=_(u"Référentiel des villes…"))
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_adresse, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.ctrl_adresse, 1, wx.EXPAND)
        sizer.AddSpacer(gap)
        ligne = wx.BoxSizer(wx.HORIZONTAL)
        cp = wx.BoxSizer(wx.VERTICAL)
        cp.Add(self.label_cp, 0, wx.EXPAND)
        cp.AddSpacer(gap)
        cp.Add(self.ctrl_cp, 0, wx.EXPAND)
        ville = wx.BoxSizer(wx.VERTICAL)
        ville.Add(self.label_ville, 0, wx.EXPAND)
        ville.AddSpacer(gap)
        ville.Add(self.ctrl_ville, 0, wx.EXPAND)
        ligne.Add(cp, 1, wx.RIGHT, gap)
        ligne.Add(ville, 2, wx.EXPAND | wx.RIGHT, gap)
        ligne.Add(self.bouton_villes, 0, wx.ALIGN_BOTTOM)
        sizer.Add(ligne, 0, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_coords(self, parent):
        self.ctrl_coords = ListCtrlCoords(parent, self)
        self.ctrl_coords.SetMinSize((-1, UTILS_Styles.Scale(130)))
        self.bouton_ajouter_coord = CTRL_Bouton_image.CTRL(parent, texte=_(u"Ajouter"))
        self.bouton_modifier_coord = CTRL_Bouton_image.CTRL(parent, texte=_(u"Modifier"))
        self.bouton_supprimer_coord = CTRL_Bouton_image.CTRL(parent, texte=_(u"Supprimer"))
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        actions = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (self.bouton_ajouter_coord, self.bouton_modifier_coord, self.bouton_supprimer_coord):
            actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl_coords, 1, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(actions, 0, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_qualifications(self, parent):
        self.ctrl_qualifications = ListCtrlDiplomes(parent, self)
        self.ctrl_qualifications.SetMinSize((-1, UTILS_Styles.Scale(110)))
        self.bouton_qualifications = CTRL_Bouton_image.CTRL(parent, texte=_(u"Modifier les qualifications…"))
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl_qualifications, 1, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.bouton_qualifications, 0)
        parent.SetSizer(sizer)

    def _creer_candidatures(self, parent):
        self.ctrl_candidatures = CORE.OL_candidatures.ListView(parent, id=-1, name="OL_candidatures", IDcandidat=self.IDcandidat, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES)
        self.ctrl_candidatures.MAJ(IDpersonne=self.IDcandidat)
        self.bouton_ajouter_cand = CTRL_Bouton_image.CTRL(parent, texte=_(u"Ajouter"))
        self.bouton_modifier_cand = CTRL_Bouton_image.CTRL(parent, texte=_(u"Modifier"))
        self.bouton_supprimer_cand = CTRL_Bouton_image.CTRL(parent, texte=_(u"Supprimer"))
        self._layout_liste_actions(parent, self.ctrl_candidatures, (self.bouton_ajouter_cand, self.bouton_modifier_cand, self.bouton_supprimer_cand))

    def _creer_entretiens(self, parent):
        self.ctrl_entretiens = CORE.OL_entretiens.ListView(parent, id=-1, name="OL_entretiens", IDcandidat=self.IDcandidat, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES)
        self.ctrl_entretiens.MAJ(IDcandidat=self.IDcandidat)
        self.bouton_ajouter_entretien = CTRL_Bouton_image.CTRL(parent, texte=_(u"Ajouter"))
        self.bouton_modifier_entretien = CTRL_Bouton_image.CTRL(parent, texte=_(u"Modifier"))
        self.bouton_supprimer_entretien = CTRL_Bouton_image.CTRL(parent, texte=_(u"Supprimer"))
        self._layout_liste_actions(parent, self.ctrl_entretiens, (self.bouton_ajouter_entretien, self.bouton_modifier_entretien, self.bouton_supprimer_entretien))

    def _layout_liste_actions(self, parent, liste, boutons):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        actions = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in boutons:
            actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(liste, 1, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(actions, 0, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_memo(self, parent):
        self.ctrl_memo = wx.TextCtrl(parent, -1, u"", style=wx.TE_MULTILINE)
        self.ctrl_memo.SetMinSize((-1, UTILS_Styles.Scale(100)))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl_memo, 1, wx.EXPAND)
        parent.SetSizer(sizer)

    def _creer_commandes(self):
        self.bouton_convertir = CTRL_Bouton_image.CTRL(self, texte=_(u"Convertir en salarié…"))
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"))
        self.bouton_courrier = CTRL_Bouton_image.CTRL(self, texte=_(u"Courrier / email"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_(u"Annuler"))

    def _installer_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        control_gap = UTILS_Styles.GetLayoutSpacing("control_gap")
        col1 = wx.BoxSizer(wx.VERTICAL)
        col1.Add(self.section_identite, 0, wx.EXPAND)
        col1.AddSpacer(gap)
        col1.Add(self.section_adresse, 1, wx.EXPAND)
        col2 = wx.BoxSizer(wx.VERTICAL)
        col2.Add(self.section_coords, 1, wx.EXPAND)
        col2.AddSpacer(gap)
        col2.Add(self.section_qualifications, 1, wx.EXPAND)
        col2.AddSpacer(gap)
        col2.Add(self.section_memo, 1, wx.EXPAND)
        col3 = wx.BoxSizer(wx.VERTICAL)
        col3.Add(self.section_candidatures, 1, wx.EXPAND)
        col3.AddSpacer(gap)
        col3.Add(self.section_entretiens, 1, wx.EXPAND)
        contenu = wx.BoxSizer(wx.HORIZONTAL)
        contenu.Add(col1, 1, wx.EXPAND | wx.RIGHT, gap)
        contenu.Add(col2, 1, wx.EXPAND | wx.RIGHT, gap)
        contenu.Add(col3, 2, wx.EXPAND)
        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_convertir, 0, wx.RIGHT, control_gap)
        actions.Add(self.bouton_courrier, 0, wx.RIGHT, control_gap)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, control_gap)
        actions.Add(self.bouton_annuler, 0)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(contenu, 1, wx.EXPAND | wx.ALL, padding)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)

    def _bind_events(self):
        for bouton, handler in (
            (self.bouton_ajouter_coord, self.AjouterCoord), (self.bouton_modifier_coord, self.ModifierCoord), (self.bouton_supprimer_coord, self.SupprimerCoord),
            (self.bouton_qualifications, self.OnBoutonQualifications),
            (self.bouton_ajouter_cand, self.AjouterCand), (self.bouton_modifier_cand, self.ModifierCand), (self.bouton_supprimer_cand, self.SupprimerCand),
            (self.bouton_ajouter_entretien, self.AjouterEntretien), (self.bouton_modifier_entretien, self.ModifierEntretien), (self.bouton_supprimer_entretien, self.SupprimerEntretien),
            (self.bouton_aide, self.Onbouton_aide), (self.bouton_courrier, self.Onbouton_courrier),
            (self.bouton_ok, self.Onbouton_ok), (self.bouton_annuler, self.Onbouton_annuler), (self.bouton_convertir, self.OnBoutonConvertir),
        ):
            self.Bind(wx.EVT_BUTTON, handler, bouton)
        self.Bind(wx.EVT_BUTTON, self.OnGestionVilles, self.bouton_villes)
        self.ctrl_nom.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusNom)
        self.ctrl_date_naiss.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusDateNaiss)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioDateNaiss, self.ctrl_radio_1)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioDateNaiss, self.ctrl_radio_2)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def _set_properties(self):
        self.ctrl_civilite.SetToolTip(wx.ToolTip(_(u"Civilité du candidat")))
        self.ctrl_nom.SetToolTip(wx.ToolTip(_(u"Nom de famille")))
        self.ctrl_prenom.SetToolTip(wx.ToolTip(_(u"Prénom")))
        self.ctrl_date_naiss.SetToolTip(wx.ToolTip(_(u"Date de naissance")))
        self.ctrl_age_1.Enable(False)
        self.ctrl_age_2.SetToolTip(wx.ToolTip(_(u"Âge si la date de naissance n'est pas connue")))
        self.ctrl_cp.SetToolTip(wx.ToolTip(_(u"Code postal")))
        self.ctrl_ville.SetToolTip(wx.ToolTip(_(u"Ville")))

    def OnGestionVilles(self, event):
        dlg = DLG_Gestion_villes.Dialog(self, _(u"Gestion des villes"), exportCP=self.ctrl_cp, exportVille=self.ctrl_ville)
        dlg.ShowModal()
        dlg.Destroy()


class Dialog(wx.Dialog):
    def __init__(self, parent, IDcandidat=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.panel = Panel(self, IDcandidat=IDcandidat)
        self.SetTitle(_(u"Saisie d'un candidat") if IDcandidat is None else _(u"Modification d'un candidat"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "workspace")
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        self.panel.Onbouton_annuler(None)

    def Fermer(self):
        parent = self.GetParent()
        try:
            if parent.GetName() == "OL_candidats":
                parent.MAJ()
        except Exception:
            pass
        recrutement = parent
        while recrutement is not None:
            try:
                if recrutement.GetName() == "Recrutement":
                    break
                recrutement = recrutement.GetParent()
            except Exception:
                recrutement = None
        if recrutement is not None:
            try:
                recrutement.gadget_entretiens.MAJ()
                recrutement.gadget_informations.MAJ()
            except Exception:
                pass
        self.EndModal(wx.ID_CANCEL)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, IDcandidat=None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
