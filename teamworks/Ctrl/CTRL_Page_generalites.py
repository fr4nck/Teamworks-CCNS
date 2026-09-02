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
import wx.lib.masked as masked
import sqlite3
import datetime
import sys

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Dlg import DLG_Saisie_coords
from Dlg import DLG_Config_situations
from Dlg import DLG_Config_pays
from Utils import UTILS_Adaptations, UTILS_Dates
from Utils import UTILS_Interface
from Utils import UTILS_Styles
import FonctionsPerso
import GestionDB


class Panel_general(wx.Panel):
    def __init__(self, parent, id, IDpersonne=0):
        wx.Panel.__init__(
            self,
            parent,
            id,
            name="panel_generalites",
            style=wx.TAB_TRAVERSAL,
        )
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.remplissageEnCours = True
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.IDpays_naiss = 0
        self.IDpays_nation = 0
        france = self.Recherche_Pays(nomPays="France")
        IDfrance = france[0] if france else 0
        if IDfrance:
            self.IDpays_naiss = IDfrance
            self.IDpays_nation = IDfrance

        # ------------------------------------------------------------------
        # Identité
        self.section_identite = CTRL_Section.Section(
            self, titre=_(u"Identité"), niveau=2
        )
        panel_identite = self.section_identite.GetContentPanel()

        self.label_civilite = CTRL_Texte.Label(panel_identite, _(u"Civilité"))
        self.combo_box_civilite = wx.Choice(
            panel_identite, -1, choices=["Mr", "Melle", "Mme"]
        )
        self.label_nomjf = CTRL_Texte.Label(
            panel_identite, _(u"Nom de jeune fille")
        )
        self.text_ctrl_nomjf = wx.TextCtrl(panel_identite, -1, "")
        self.label_nom = CTRL_Texte.Label(panel_identite, _(u"Nom"))
        self.text_nom = wx.TextCtrl(panel_identite, -1, "")
        self.label_prenom = CTRL_Texte.Label(panel_identite, _(u"Prénom"))
        self.text_prenom = wx.TextCtrl(panel_identite, -1, "")

        self.label_date_naiss = CTRL_Texte.Label(
            panel_identite, _(u"Date de naissance")
        )
        self.text_date_naiss = masked.TextCtrl(
            panel_identite,
            -1,
            "",
            style=wx.TE_CENTRE,
            mask="##/##/####",
        )
        self.text_age = wx.TextCtrl(
            panel_identite,
            -1,
            "",
            style=wx.TE_CENTRE | wx.TE_READONLY | wx.BORDER_NONE,
        )
        self.text_age.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )

        self.label_pays = CTRL_Texte.Label(
            panel_identite, _(u"Pays de naissance")
        )
        self.image_pays = wx.StaticBitmap(panel_identite, -1, wx.NullBitmap)
        self.bouton_pays = CTRL_Bouton_image.CTRL(
            panel_identite, texte=_(u"Choisir")
        )

        self.label_cp_naiss = CTRL_Texte.Label(
            panel_identite, _(u"Code postal de naissance")
        )
        self.text_cp_naiss = masked.TextCtrl(
            panel_identite, 100, "", style=wx.TE_CENTRE, mask="#####"
        )
        self.label_ville_naiss = CTRL_Texte.Label(
            panel_identite, _(u"Ville de naissance")
        )
        self.text_ville_naiss = wx.TextCtrl(panel_identite, 200)
        self.bouton_options_ville_naiss = CTRL_Bouton_image.CTRL(
            panel_identite, texte=_(u"Rechercher")
        )

        self.label_numsecu = CTRL_Texte.Label(
            panel_identite, _(u"Numéro de sécurité sociale")
        )
        self.text_numsecu = masked.TextCtrl(
            panel_identite,
            -1,
            "",
            style=wx.TE_CENTRE,
            mask="# ## ## ## ### ### ##",
        )
        self.ctrl_etat_numsecu = CTRL_Texte.Caption(
            panel_identite, _(u"Non renseigné")
        )
        self.label_nation = CTRL_Texte.Label(
            panel_identite, _(u"Nationalité")
        )
        self.image_nation = wx.StaticBitmap(panel_identite, -1, wx.NullBitmap)
        self.bouton_nation = CTRL_Bouton_image.CTRL(
            panel_identite, texte=_(u"Choisir")
        )

        # ------------------------------------------------------------------
        # Situation sociale
        self.section_situation = CTRL_Section.Section(
            self, titre=_(u"Situation sociale"), niveau=2
        )
        panel_situation = self.section_situation.GetContentPanel()
        self.combo_box_situation = wx.Choice(panel_situation, -1, choices=[])
        self.bouton_situations = CTRL_Bouton_image.CTRL(
            panel_situation, texte=_(u"Gérer")
        )
        self.ImportListeSituations()

        # ------------------------------------------------------------------
        # Adresse
        self.section_adresse = CTRL_Section.Section(
            self, titre=_(u"Adresse postale"), niveau=2
        )
        panel_adresse = self.section_adresse.GetContentPanel()
        self.label_adresse = CTRL_Texte.Label(panel_adresse, _(u"Adresse"))
        self.text_adresse = wx.TextCtrl(
            panel_adresse, -1, "", style=wx.TE_MULTILINE
        )
        self.label_cp = CTRL_Texte.Label(panel_adresse, _(u"Code postal"))
        self.text_cp = masked.TextCtrl(
            panel_adresse, 300, "", style=wx.TE_CENTRE, mask="#####"
        )
        self.label_ville = CTRL_Texte.Label(panel_adresse, _(u"Ville"))
        self.text_ville = wx.TextCtrl(panel_adresse, 400)
        self.bouton_options_ville = CTRL_Bouton_image.CTRL(
            panel_adresse, texte=_(u"Rechercher")
        )

        # ------------------------------------------------------------------
        # Téléphones et e-mails
        # Cette information appartient à la fiche Généralités : le dialogue
        # DLG_Saisie_coords reste pour l'instant un éditeur de compatibilité,
        # mais il ne constitue pas une page métier autonome.
        self.section_coords = CTRL_Section.Section(
            self, titre=_(u"Téléphones et e-mails"), niveau=2
        )
        panel_coords = self.section_coords.GetContentPanel()
        self.list_ctrl_coords = ListCtrlCoords(
            panel_coords, -1, owner=self
        )
        self.list_ctrl_coords.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.button_coords_ajout = CTRL_Bouton_image.CTRL(
            panel_coords,
            texte=_(u"Ajouter"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Ajouter.png"),
        )
        self.button_coords_modif = CTRL_Bouton_image.CTRL(
            panel_coords,
            texte=_(u"Modifier"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Modifier.png"),
        )
        self.button_coords_suppr = CTRL_Bouton_image.CTRL(
            panel_coords,
            texte=_(u"Supprimer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Supprimer.png"),
        )

        # ------------------------------------------------------------------
        # Mémo
        self.section_memo = CTRL_Section.Section(
            self, titre=_(u"Mémo"), niveau=2
        )
        panel_memo = self.section_memo.GetContentPanel()
        self.text_memo = wx.TextCtrl(
            panel_memo, -1, "", style=wx.TE_MULTILINE
        )

        if "linux" in sys.platform:
            self.text_ville_naiss.Enable(False)
            self.text_ville.Enable(False)

        self.__set_properties()
        self.__do_layout(
            panel_identite,
            panel_situation,
            panel_adresse,
            panel_coords,
            panel_memo,
        )

        # Événements
        self.Bind(wx.EVT_BUTTON, self.OnOptionsVille, self.bouton_options_ville)
        self.Bind(
            wx.EVT_BUTTON,
            self.OnOptionsVilleNaiss,
            self.bouton_options_ville_naiss,
        )
        self.Bind(wx.EVT_BUTTON, self.OnAjoutTel, self.button_coords_ajout)
        self.Bind(wx.EVT_BUTTON, self.OnModifTel, self.button_coords_modif)
        self.Bind(wx.EVT_BUTTON, self.OnSupprTel, self.button_coords_suppr)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSituations, self.bouton_situations)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonPays, self.bouton_pays)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonNation, self.bouton_nation)
        self.ctrl_etat_numsecu.Bind(wx.EVT_LEFT_DOWN, self.OnImageNumSecu)

        self.Bind(wx.EVT_CHOICE, self.OnTextCivilite, self.combo_box_civilite)
        self.Bind(wx.EVT_TEXT, self.OnTextNomJF, self.text_ctrl_nomjf)
        self.Bind(wx.EVT_TEXT, self.OnTextNom, self.text_nom)
        self.Bind(wx.EVT_TEXT, self.OnTextPrenom, self.text_prenom)
        self.Bind(wx.EVT_TEXT, self.OnTextDateNaiss, self.text_date_naiss)
        self.Bind(wx.EVT_TEXT, self.OnTextNumSecu, self.text_numsecu)
        self.Bind(wx.EVT_TEXT, self.OnTextAdresse, self.text_adresse)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)

        self.combo_box_civilite.Bind(
            wx.EVT_KILL_FOCUS, self.OnKillFocusCivilite
        )
        self.text_ctrl_nomjf.Bind(
            wx.EVT_KILL_FOCUS, self.OnKillFocusNomJFille
        )
        self.text_nom.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusNom)
        self.text_prenom.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusPrenom)
        self.text_date_naiss.Bind(
            wx.EVT_KILL_FOCUS, self.OnKillFocusDateNaiss
        )
        self.text_numsecu.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusNumSecu)
        self.text_adresse.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusAdresse)
        self.combo_box_situation.Bind(
            wx.EVT_KILL_FOCUS, self.OnKillFocusSituation
        )

        self.text_ville_naiss.ignoreEvtText = False
        self.text_ville.ignoreEvtText = False
        self.autoComplete = True

        con = sqlite3.connect(Chemins.GetStaticPath("Databases/Villes.db3"))
        cur = con.cursor()
        cur.execute("SELECT ville, cp FROM villes")
        self.listeVillesTmp = cur.fetchall()
        cur.execute("SELECT num_dep, num_region, departement FROM departements")
        listeDepartements = cur.fetchall()
        cur.execute("SELECT num_region, region FROM regions")
        listeRegions = cur.fetchall()
        con.close()

        self.listeNomsVilles = []
        self.listeVilles = []
        for nom, cp in self.listeVillesTmp:
            self.listeVilles.append((nom, "%05d" % cp))
            self.listeNomsVilles.append(nom)

        self.dictRegions = {
            num_region: region for num_region, region in listeRegions
        }
        self.dictDepartements = {
            num_dep: (departement, num_region)
            for num_dep, num_region, departement in listeDepartements
        }

        self.text_ville_naiss.Bind(wx.EVT_TEXT, self.VilleText1)
        self.text_ville_naiss.Bind(wx.EVT_CHAR, self.VilleChar1)
        self.text_ville_naiss.Bind(
            wx.EVT_KILL_FOCUS, self.Ville_KillFocus1
        )
        self.text_cp_naiss.Bind(wx.EVT_KILL_FOCUS, self.Code_KillFocus1)
        self.text_ville.Bind(wx.EVT_TEXT, self.VilleText2)
        self.text_ville.Bind(wx.EVT_CHAR, self.VilleChar2)
        self.text_ville.Bind(wx.EVT_KILL_FOCUS, self.Ville_KillFocus2)
        self.text_cp.Bind(wx.EVT_KILL_FOCUS, self.Code_KillFocus2)

        if IDfrance:
            self.SetPaysNaiss(IDfrance)
            self.SetNationalite(IDfrance)

        if self.IDpersonne != 0:
            self.Importation()

        self.SetEtatNumSecu()
        self.MAJ_Photo()
        self.MaJ_Adresse_Fiche()
        self.MaJ_DateNaiss_Fiche()
        self.remplissageEnCours = False

    # ----------------------------------------------------------------------
    # Propriétés et layout
    def __set_properties(self):
        self.combo_box_civilite.SetToolTip(
            wx.ToolTip(_(u"Choisissez la civilité"))
        )
        self.label_nomjf.Enable(False)
        self.text_ctrl_nomjf.SetToolTip(
            wx.ToolTip(_(u"Saisissez un nom de jeune fille"))
        )
        self.text_ctrl_nomjf.Enable(False)
        self.text_nom.SetToolTip(wx.ToolTip(_(u"Saisissez le nom de famille")))
        self.text_prenom.SetToolTip(wx.ToolTip(_(u"Saisissez le prénom")))
        self.text_date_naiss.SetMinSize((UTILS_Styles.Scale(120), -1))
        self.text_date_naiss.SetToolTip(
            wx.ToolTip(_(u"Saisissez la date de naissance"))
        )
        self.text_numsecu.SetMinSize((UTILS_Styles.Scale(210), -1))
        self.text_adresse.SetMinSize((-1, UTILS_Styles.Scale(72)))
        self.text_adresse.SetToolTip(wx.ToolTip(_(u"Saisissez l'adresse")))
        self.text_age.SetMinSize((UTILS_Styles.Scale(88), -1))
        self.text_cp_naiss.SetMinSize((UTILS_Styles.Scale(82), -1))
        self.text_cp_naiss.SetToolTip(
            wx.ToolTip(_(u"Saisissez le code postal"))
        )
        self.text_cp.SetMinSize((UTILS_Styles.Scale(82), -1))
        self.text_cp.SetToolTip(wx.ToolTip(_(u"Saisissez le code postal")))
        self.text_ville_naiss.SetToolTip(
            wx.ToolTip(_(u"Choisissez une ville dans la liste proposée"))
        )
        self.text_ville.SetToolTip(
            wx.ToolTip(_(u"Choisissez une ville dans la liste proposée"))
        )
        self.bouton_options_ville_naiss.SetToolTip(
            wx.ToolTip(_(u"Rechercher ou saisir une ville de naissance"))
        )
        self.bouton_options_ville.SetToolTip(
            wx.ToolTip(_(u"Rechercher ou saisir une ville de résidence"))
        )
        self.button_coords_ajout.SetToolTip(
            wx.ToolTip(_(u"Créer un téléphone ou un e-mail"))
        )
        self.button_coords_modif.SetToolTip(
            wx.ToolTip(_(u"Modifier le téléphone ou l'e-mail sélectionné"))
        )
        self.button_coords_suppr.SetToolTip(
            wx.ToolTip(_(u"Supprimer le téléphone ou l'e-mail sélectionné"))
        )
        self.bouton_situations.SetToolTip(
            wx.ToolTip(_(u"Gérer les situations sociales"))
        )
        self.bouton_pays.SetToolTip(
            wx.ToolTip(_(u"Sélectionner un autre pays de naissance"))
        )
        self.bouton_nation.SetToolTip(
            wx.ToolTip(_(u"Sélectionner une autre nationalité"))
        )
        self.ctrl_etat_numsecu.SetToolTip(
            wx.ToolTip(
                _(u"État du numéro de sécurité sociale. Cliquez pour afficher les règles de constitution.")
            )
        )

        texteNumSecu = u"""
        Numéro de sécurité sociale : A BB CC DD EEE FFF GG

        A : Sexe (1=homme | 2=femme)
        BB : Année de naissance
        CC : Mois de naissance
        DD : Département de naissance (99 si né à l'étranger)
        EEE : Code INSEE de la commune de naissance ou du pays si né à l'étranger
        FFF : Numéro d'ordre INSEE
        GG : Clé
        """
        self.text_numsecu.SetToolTip(wx.ToolTip(texteNumSecu))
        self.combo_box_civilite.SetFocus()

    def _champ_vertical(self, label, ctrl, proportion=1):
        gap = UTILS_Styles.GetSpacing("xs")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.EXPAND | wx.BOTTOM, gap)
        sizer.Add(ctrl, proportion, wx.EXPAND)
        return sizer

    def __do_layout(
        self,
        panel_identite,
        panel_situation,
        panel_adresse,
        panel_coords,
        panel_memo,
    ):
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        xs = UTILS_Styles.GetSpacing("xs")

        # Identité ---------------------------------------------------------
        identite = wx.BoxSizer(wx.VERTICAL)

        ligne_civilite = wx.BoxSizer(wx.HORIZONTAL)
        champ_civilite = self._champ_vertical(
            self.label_civilite, self.combo_box_civilite, 0
        )
        champ_nomjf = self._champ_vertical(
            self.label_nomjf, self.text_ctrl_nomjf, 0
        )
        ligne_civilite.Add(champ_civilite, 1, wx.RIGHT, field_gap)
        ligne_civilite.Add(champ_nomjf, 2, wx.EXPAND)
        identite.Add(ligne_civilite, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        ligne_nom = wx.BoxSizer(wx.HORIZONTAL)
        ligne_nom.Add(
            self._champ_vertical(self.label_nom, self.text_nom, 0),
            1,
            wx.RIGHT,
            field_gap,
        )
        ligne_nom.Add(
            self._champ_vertical(self.label_prenom, self.text_prenom, 0),
            1,
            wx.EXPAND,
        )
        identite.Add(ligne_nom, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        ligne_naissance = wx.BoxSizer(wx.HORIZONTAL)
        ligne_naissance.Add(
            self._champ_vertical(self.label_date_naiss, self.text_date_naiss, 0),
            0,
            wx.RIGHT,
            field_gap,
        )
        ligne_naissance.Add(
            self.text_age,
            0,
            wx.ALIGN_BOTTOM | wx.RIGHT,
            field_gap,
        )
        pays_bloc = wx.BoxSizer(wx.VERTICAL)
        pays_bloc.Add(self.label_pays, 0, wx.BOTTOM, xs)
        pays_ligne = wx.BoxSizer(wx.HORIZONTAL)
        pays_ligne.Add(self.image_pays, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        pays_ligne.Add(self.bouton_pays, 0)
        pays_bloc.Add(pays_ligne, 0)
        ligne_naissance.Add(pays_bloc, 1, wx.EXPAND)
        identite.Add(ligne_naissance, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        ligne_lieu = wx.BoxSizer(wx.HORIZONTAL)
        ligne_lieu.Add(
            self._champ_vertical(self.label_cp_naiss, self.text_cp_naiss, 0),
            0,
            wx.RIGHT,
            field_gap,
        )
        ligne_lieu.Add(
            self._champ_vertical(self.label_ville_naiss, self.text_ville_naiss, 0),
            1,
            wx.RIGHT,
            field_gap,
        )
        ligne_lieu.Add(
            self.bouton_options_ville_naiss,
            0,
            wx.ALIGN_BOTTOM,
        )
        identite.Add(ligne_lieu, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        ligne_secu = wx.BoxSizer(wx.HORIZONTAL)
        secu_bloc = wx.BoxSizer(wx.VERTICAL)
        secu_bloc.Add(self.label_numsecu, 0, wx.BOTTOM, xs)
        secu_ligne = wx.BoxSizer(wx.HORIZONTAL)
        secu_ligne.Add(self.text_numsecu, 1, wx.RIGHT, field_gap)
        secu_ligne.Add(self.ctrl_etat_numsecu, 0, wx.ALIGN_CENTER_VERTICAL)
        secu_bloc.Add(secu_ligne, 0, wx.EXPAND)
        ligne_secu.Add(secu_bloc, 2, wx.RIGHT, field_gap)

        nation_bloc = wx.BoxSizer(wx.VERTICAL)
        nation_bloc.Add(self.label_nation, 0, wx.BOTTOM, xs)
        nation_ligne = wx.BoxSizer(wx.HORIZONTAL)
        nation_ligne.Add(self.image_nation, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        nation_ligne.Add(self.bouton_nation, 0)
        nation_bloc.Add(nation_ligne, 0)
        ligne_secu.Add(nation_bloc, 1, wx.EXPAND)
        identite.Add(ligne_secu, 0, wx.EXPAND)
        panel_identite.SetSizer(identite)
        self.grid_sizer_identite = identite

        # Situation --------------------------------------------------------
        situation = wx.BoxSizer(wx.HORIZONTAL)
        situation.Add(self.combo_box_situation, 1, wx.RIGHT, field_gap)
        situation.Add(self.bouton_situations, 0)
        panel_situation.SetSizer(situation)

        # Adresse ----------------------------------------------------------
        adresse = wx.BoxSizer(wx.VERTICAL)
        adresse.Add(self.label_adresse, 0, wx.BOTTOM, xs)
        adresse.Add(self.text_adresse, 1, wx.EXPAND | wx.BOTTOM, field_gap)
        ligne_ville = wx.BoxSizer(wx.HORIZONTAL)
        ligne_ville.Add(
            self._champ_vertical(self.label_cp, self.text_cp, 0),
            0,
            wx.RIGHT,
            field_gap,
        )
        ligne_ville.Add(
            self._champ_vertical(self.label_ville, self.text_ville, 0),
            1,
            wx.RIGHT,
            field_gap,
        )
        ligne_ville.Add(self.bouton_options_ville, 0, wx.ALIGN_BOTTOM)
        adresse.Add(ligne_ville, 0, wx.EXPAND)
        panel_adresse.SetSizer(adresse)

        # Téléphones et e-mails -------------------------------------------
        coords = wx.BoxSizer(wx.VERTICAL)
        actions_coords = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (
            self.button_coords_ajout,
            self.button_coords_modif,
            self.button_coords_suppr,
        ):
            actions_coords.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, toolbar_gap)
        coords.Add(actions_coords, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        self.list_ctrl_coords.SetMinSize((-1, UTILS_Styles.Scale(150)))
        coords.Add(self.list_ctrl_coords, 1, wx.EXPAND)
        panel_coords.SetSizer(coords)

        # Mémo -------------------------------------------------------------
        memo = wx.BoxSizer(wx.VERTICAL)
        self.text_memo.SetMinSize((-1, UTILS_Styles.Scale(130)))
        memo.Add(self.text_memo, 1, wx.EXPAND)
        panel_memo.SetSizer(memo)

        # Page -------------------------------------------------------------
        colonne_gauche = wx.BoxSizer(wx.VERTICAL)
        colonne_gauche.Add(self.section_identite, 3, wx.EXPAND | wx.BOTTOM, section_gap)
        colonne_gauche.Add(self.section_adresse, 2, wx.EXPAND)

        colonne_droite = wx.BoxSizer(wx.VERTICAL)
        colonne_droite.Add(self.section_situation, 0, wx.EXPAND | wx.BOTTOM, section_gap)
        colonne_droite.Add(self.section_coords, 3, wx.EXPAND | wx.BOTTOM, section_gap)
        colonne_droite.Add(self.section_memo, 2, wx.EXPAND)

        colonnes = wx.BoxSizer(wx.HORIZONTAL)
        colonnes.Add(colonne_gauche, 3, wx.EXPAND | wx.RIGHT, section_gap)
        colonnes.Add(colonne_droite, 2, wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(colonnes, 1, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)

    # ----------------------------------------------------------------------
    # Actions
    def MAJ_barre_problemes(self):
        self.parent.GetGrandParent().MAJ_barre_problemes()

    def OnImageNumSecu(self, event):
        message = u"""
        Numéro de sécurité sociale : A BB CC DD EEE FFF GG

        A : Sexe (1=homme | 2=femme)
        BB : Année de naissance
        CC : Mois de naissance
        DD : Département de naissance (99 si né à l'étranger)
        EEE : Code INSEE de la commune de naissance ou du pays si né à l'étranger
        FFF : Numéro d'ordre INSEE
        GG : Clé
        """
        dlg = wx.MessageDialog(
            self,
            message,
            _(u"Constitution d'un numéro de sécurité sociale"),
            wx.OK | wx.ICON_INFORMATION,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonPays(self, event):
        dlg = DLG_Config_pays.Dialog(
            self,
            "",
            IDpays=self.IDpays_naiss,
            saisie="FicheIndiv_pays_naiss",
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonNation(self, event):
        dlg = DLG_Config_pays.Dialog(
            self,
            "",
            IDpays=self.IDpays_nation,
            saisie="FicheIndiv_nationalite",
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonSituations(self, event):
        dlg = DLG_Config_situations.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.ImportListeSituations()

    def OnActivate(self, event):
        event.Skip()

    def OnOptionsVilleNaiss(self, event):
        self.AppelGestionVilles(
            "text_cp_naiss", "text_ville_naiss", _(u"Lieu de naissance")
        )
        event.Skip()

    def OnOptionsVille(self, event):
        self.AppelGestionVilles(
            "text_cp", "text_ville", _(u"Lieu de résidence")
        )
        event.Skip()

    def AppelGestionVilles(self, controleCP, controleVille, nomChamp):
        from Dlg import DLG_Gestion_villes
        dlg = DLG_Gestion_villes.Dialog(
            self,
            "Titre",
            exportCP=controleCP,
            exportVille=controleVille,
            exportChamp=nomChamp,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OnAjoutTel(self, event):
        self.AjouterCoord()
        event.Skip()

    def AjouterCoord(self):
        dlg = DLG_Saisie_coords.Dialog(
            self, IDcoord=0, IDpersonne=self.IDpersonne
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OnModifTel(self, event):
        self.ModifierCoord()
        event.Skip()

    def ModifierCoord(self):
        index = self.list_ctrl_coords.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un item à modifier dans la liste des téléphones et e-mails"),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        varIDcoord = self.list_ctrl_coords.GetItemData(index)
        dlg = DLG_Saisie_coords.Dialog(
            self, IDcoord=varIDcoord, IDpersonne=self.IDpersonne
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OnSupprTel(self, event):
        self.SupprimerCoord()
        event.Skip()

    def SupprimerCoord(self):
        index = self.list_ctrl_coords.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner un item à supprimer dans la liste des téléphones et e-mails"),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        texteCoord = self.list_ctrl_coords.GetItemText(index)
        dlgConfirm = wx.MessageDialog(
            self,
            six.text_type(
                _(u"Voulez-vous vraiment supprimer cette coordonnée ? \n\n> ")
                + texteCoord
            ),
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return

        varIDcoord = self.list_ctrl_coords.GetItemData(index)
        DB = GestionDB.DB()
        DB.ReqDEL("coordonnees", "IDcoord", varIDcoord)
        DB.Close()
        self.list_ctrl_coords.Remplissage()
        self.MAJ_barre_problemes()

    # ----------------------------------------------------------------------
    # Mise à jour / validations de champs
    def MaJ_Civilite(self):
        valeur = self.combo_box_civilite.GetStringSelection()
        if valeur == "Mr" or valeur == "Melle":
            self.label_nomjf.Enable(False)
            self.text_ctrl_nomjf.Enable(False)
            self.text_nom.SetFocus()
        elif valeur == "Mme":
            self.label_nomjf.Enable(True)
            self.text_ctrl_nomjf.Enable(True)

    def MaJ_DateNaiss(self):
        if self.text_date_naiss.GetValue() == "  /  /    ":
            self.text_age.SetValue("")
            self.MaJ_DateNaiss_Fiche()
            self.MAJ_barre_problemes()
            return
        validation = ValideDate(
            texte=self.text_date_naiss.GetValue(),
            date_min="01/01/1910",
            date_max="01/01/2030",
        )
        if validation is False:
            self.text_date_naiss.SetFocus()
            return

        valeurDate = self.text_date_naiss.GetValue()
        jour = int(valeurDate[:2])
        mois = int(valeurDate[3:5])
        annee = int(valeurDate[6:10])
        bday = datetime.date(annee, mois, jour)
        datedujour = datetime.date.today()
        age = (datedujour.year - bday.year) - int(
            (datedujour.month, datedujour.day) < (bday.month, bday.day)
        )
        self.text_age.SetValue(str(age) + " ans")
        self.MaJ_DateNaiss_Fiche()

    def OnTextCivilite(self, event):
        self.MaJ_Civilite()
        self.MaJ_DateNaiss_Fiche()
        self.MAJ_Photo()
        event.Skip()

    def MAJ_Photo(self):
        if self.GetGrandParent().GetParent().photo is not None:
            return
        valeur = self.combo_box_civilite.GetStringSelection()
        if valeur == "Mr":
            img = "Homme.png"
        elif valeur == "Mme" or valeur == "Melle":
            img = "Femme.png"
        else:
            img = "Personne.png"
        nomFichier = Chemins.GetStaticPath("Images/128x128/" + img)
        self.GetGrandParent().GetParent().bitmap_photo.SetPhoto(
            self.IDpersonne, nomFichier, taillePhoto=(128, 128), qualite=100
        )

    def OnTextNomJF(self, event):
        event.Skip()

    def OnTextNom(self, event):
        self.MaJ_NomPrenom_Fiche()
        event.Skip()

    def OnTextPrenom(self, event):
        self.MaJ_NomPrenom_Fiche()
        event.Skip()

    def OnTextDateNaiss(self, event):
        self.MaJ_DateNaiss_Fiche()
        event.Skip()

    def OnTextLieuNaiss(self, event):
        self.MaJ_DateNaiss_Fiche()
        event.Skip()

    def OnTextNumSecu(self, event):
        event.Skip()

    def OnTextAdresse(self, event):
        self.MaJ_Adresse_Fiche()
        event.Skip()

    def OnTextCP(self, event):
        self.MaJ_Adresse_Fiche()
        event.Skip()

    def OnTextVille(self, event):
        self.MaJ_Adresse_Fiche()
        event.Skip()

    def CouleurSiVide(self, controle, typeControle):
        """Compatibilité historique, sans couleur locale arbitraire."""
        try:
            vide = len(controle.GetValue()) == 0
        except Exception:
            vide = False
        controle.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        controle.SetForegroundColour(
            UTILS_Interface.GetToken("danger" if vide else "on_surface")
        )
        controle.Refresh()
        if vide:
            controle.SetFocus()
            return False
        return True

    def AfficheAutresPages(self):
        try:
            afficher = (
                self.combo_box_civilite.GetStringSelection() != ""
                and self.text_nom.GetValue() != ""
                and self.text_prenom.GetValue() != ""
            )
            self.GetParent().AfficheAutresPages(afficher)
        except Exception:
            pass

    def OnKillFocusCivilite(self, event):
        valeur = self.combo_box_civilite.GetStringSelection()
        if valeur not in ("Mr", "Mme", "Melle", ""):
            dlg = wx.MessageDialog(
                self,
                _(u"Vous ne pouvez saisir ici que les valeur 'Mr', 'Melle' ou 'Mme'."),
                "Erreur de saisie",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.combo_box_civilite.SetFocus()
            event.Skip()
            return
        self.MAJ_barre_problemes()
        self.AfficheAutresPages()
        event.Skip()

    def OnKillFocusNom(self, event):
        texte = self.text_nom.GetValue()
        if len(texte) != 0:
            self.text_nom.SetValue(texte.upper())
        self.MAJ_barre_problemes()
        self.AfficheAutresPages()
        event.Skip()

    def OnKillFocusNomJFille(self, event):
        nomJF = self.text_ctrl_nomjf.GetValue()
        if nomJF != "":
            self.text_ctrl_nomjf.SetValue(nomJF.upper())
        self.MAJ_barre_problemes()
        event.Skip()

    def OnKillFocusPrenom(self, event):
        texte = self.text_prenom.GetValue()
        if len(texte) > 1:
            texte = texte[:1].upper() + texte[1:]
            self.text_prenom.SetValue(texte)
        self.MAJ_barre_problemes()
        self.AfficheAutresPages()
        event.Skip()

    def OnKillFocusDateNaiss(self, event):
        self.MaJ_DateNaiss()
        self.MAJ_barre_problemes()
        event.Skip()

    def OnKillFocusNumSecu(self, event):
        self.SetEtatNumSecu()
        self.MAJ_barre_problemes()
        event.Skip()

    def SetEtatNumSecu(self):
        validation, message = ValideNumSecu(
            self.text_numsecu.GetValue(),
            self.combo_box_civilite.GetStringSelection(),
            self.text_date_naiss.GetValue(),
            self.text_cp_naiss.GetValue(),
        )
        if validation is False:
            self.ctrl_etat_numsecu.SetLabel(_(u"À vérifier"))
            self.ctrl_etat_numsecu.SetForegroundColour(
                UTILS_Interface.GetToken("danger")
            )
            if self.remplissageEnCours is False:
                wx.MessageBox(
                    message, _(u"Numéro de sécurité sociale erroné")
                )
        elif validation is None:
            self.ctrl_etat_numsecu.SetLabel(_(u"Non renseigné"))
            self.ctrl_etat_numsecu.SetForegroundColour(
                UTILS_Interface.GetToken("on_surface_variant")
            )
        else:
            self.ctrl_etat_numsecu.SetLabel(_(u"Valide"))
            self.ctrl_etat_numsecu.SetForegroundColour(
                UTILS_Interface.GetToken("success")
            )
        self.grid_sizer_identite.Layout()

    def OnKillFocusAdresse(self, event):
        txtAdresse = self.text_adresse.GetValue()
        if txtAdresse != "" and txtAdresse.endswith("\n"):
            self.text_adresse.SetValue(txtAdresse[:-1])
        self.MAJ_barre_problemes()
        event.Skip()

    def OnKillFocusSituation(self, event):
        self.MAJ_barre_problemes()
        event.Skip()

    # ----------------------------------------------------------------------
    # CP / villes
    def SetInfobulleVille(self, controle, nomControle):
        if nomControle == "cp" or nomControle == "cp_naiss":
            cp = controle.GetValue()
        elif nomControle == "ville":
            cp = self.text_cp.GetValue()
        else:
            cp = self.text_cp_naiss.GetValue()

        if cp == "" or cp == "     ":
            if nomControle == "cp" or nomControle == "cp_naiss":
                controle.SetToolTip(wx.ToolTip(_(u"Saisissez un code postal")))
            else:
                controle.SetToolTip(wx.ToolTip(_(u"Saisissez un nom de ville")))
            return

        try:
            num_dep = cp[:2]
            nomDepartement, num_region = self.dictDepartements[num_dep]
            nomRegion = self.dictRegions[num_region]
            texte = _(u"Département : %s (%s)\nRégion : %s") % (
                nomDepartement,
                num_dep,
                nomRegion,
            )
            controle.SetToolTip(wx.ToolTip(texte))
        except Exception:
            if nomControle == "cp" or nomControle == "cp_naiss":
                controle.SetToolTip(
                    wx.ToolTip(
                        _(u"Le code postal saisi ne figure pas dans la base de données de Teamworks-CCNS")
                    )
                )
            else:
                controle.SetToolTip(
                    wx.ToolTip(
                        _(u"Le nom de ville saisi ne figure pas dans la base de données de Teamworks-CCNS")
                    )
                )

    def Code_KillFocus1(self, event):
        self.MAJ_barre_problemes()
        if self.autoComplete is False:
            return
        textCode = self.text_cp_naiss.GetValue()
        villeSelect = self.text_ville_naiss.GetValue()
        if villeSelect != '':
            for ville, cp in self.listeVilles:
                if ville == villeSelect and cp == textCode:
                    self.SetInfobulleVille(self.text_cp_naiss, "cp_naiss")
                    return

        ReponsesVilles = [
            ville for ville, cp in self.listeVilles if cp == textCode
        ]
        nbreReponses = len(ReponsesVilles)
        if nbreReponses == 0:
            if textCode.strip() != '':
                dlg = wx.MessageDialog(
                    self,
                    _(u"Ce code postal n'est pas répertorié dans la base de données. \nVérifiez que vous n'avez pas fait d'erreur de saisie."),
                    "Information",
                    wx.OK | wx.ICON_INFORMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
            self.SetInfobulleVille(self.text_cp_naiss, "cp_naiss")
            return
        if nbreReponses == 1:
            resultat = ReponsesVilles[0]
            self.text_ville_naiss.SetValue(resultat)
        else:
            resultat = self.ChoixVilles(textCode, ReponsesVilles)
            if resultat != '':
                self.text_ville_naiss.SetValue(resultat)
        self.text_ville_naiss.SetSelection(0, len(resultat))
        self.MaJ_DateNaiss_Fiche()
        self.SetInfobulleVille(self.text_cp_naiss, "cp_naiss")
        event.Skip()

    def Ville_KillFocus1(self, event):
        self.MAJ_barre_problemes()
        if self.autoComplete is False:
            return
        villeSelect = self.text_ville_naiss.GetValue()
        if villeSelect == '':
            self.MaJ_DateNaiss_Fiche()
            self.SetInfobulleVille(self.text_ville_naiss, "ville_naiss")
            self.SetInfobulleVille(self.text_cp_naiss, "cp_naiss")
            return

        nbreCodes = self.listeNomsVilles.count(villeSelect)
        if nbreCodes > 1:
            listeCodes = [
                cp for ville, cp in self.listeVilles if villeSelect == ville
            ]
            resultat = self.ChoixCodes(villeSelect, listeCodes)
            if resultat != '':
                self.text_cp_naiss.SetValue(resultat)
        if nbreCodes == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Cette ville n'est pas répertoriée dans la base de données. \nVérifiez que vous n'avez pas fait d'erreur de saisie."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
        self.SetInfobulleVille(self.text_ville_naiss, "ville_naiss")
        self.SetInfobulleVille(self.text_cp_naiss, "cp_naiss")
        self.MaJ_DateNaiss_Fiche()
        event.Skip()

    def VilleChar1(self, event):
        if event.GetKeyCode() == 8:
            self.text_ville_naiss.ignoreEvtText = True
            self.MaJ_DateNaiss_Fiche()
        event.Skip()

    def VilleText1(self, event):
        if self.autoComplete is False:
            return
        if self.text_ville_naiss.ignoreEvtText:
            self.text_ville_naiss.ignoreEvtText = False
            self.MaJ_DateNaiss_Fiche()
            return
        currentText = event.GetString().upper()
        found = False
        for ville, cp in self.listeVilles:
            if ville.startswith(currentText):
                self.text_ville_naiss.ignoreEvtText = True
                self.text_ville_naiss.SetValue(ville)
                self.text_ville_naiss.SetInsertionPoint(len(currentText))
                self.text_ville_naiss.SetSelection(
                    len(currentText), len(ville)
                )
                self.text_cp_naiss.SetValue(str(cp))
                self.MaJ_DateNaiss_Fiche()
                self.SetInfobulleVille(
                    self.text_ville_naiss, "ville_naiss"
                )
                self.SetInfobulleVille(self.text_cp_naiss, "cp_naiss")
                found = True
                break
        if not found:
            self.text_cp_naiss.SetValue('')
            self.MaJ_DateNaiss_Fiche()
            self.SetInfobulleVille(self.text_ville_naiss, "ville_naiss")
            self.SetInfobulleVille(self.text_cp_naiss, "cp_naiss")
            event.Skip()

    def Code_KillFocus2(self, event):
        self.MAJ_barre_problemes()
        if self.autoComplete is False:
            return
        textCode = self.text_cp.GetValue()
        self.MaJ_Adresse_Fiche()
        villeSelect = self.text_ville.GetValue()
        if villeSelect != '':
            for ville, cp in self.listeVilles:
                if ville == villeSelect and str(cp) == str(textCode):
                    self.SetInfobulleVille(self.text_cp, "cp")
                    return

        ReponsesVilles = [
            ville
            for ville, cp in self.listeVilles
            if str(cp) == str(textCode)
        ]
        nbreReponses = len(ReponsesVilles)
        if nbreReponses == 0:
            if textCode.strip() != '':
                dlg = wx.MessageDialog(
                    self,
                    _(u"Ce code postal n'est pas répertorié dans la base de données. \nVérifiez que vous n'avez pas fait d'erreur de saisie."),
                    "Information",
                    wx.OK | wx.ICON_INFORMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
            self.SetInfobulleVille(self.text_cp, "cp")
            return
        if nbreReponses == 1:
            resultat = ReponsesVilles[0]
            self.text_ville.SetValue(resultat)
        else:
            resultat = self.ChoixVilles(textCode, ReponsesVilles)
            if resultat != '':
                self.text_ville.SetValue(resultat)
        self.text_ville.SetSelection(0, len(resultat))
        self.MaJ_Adresse_Fiche()
        self.SetInfobulleVille(self.text_cp, "cp")
        event.Skip()

    def Ville_KillFocus2(self, event):
        self.MAJ_barre_problemes()
        if self.autoComplete is False:
            return
        villeSelect = self.text_ville.GetValue()
        if villeSelect == '':
            self.MaJ_Adresse_Fiche()
            self.SetInfobulleVille(self.text_ville, "ville")
            self.SetInfobulleVille(self.text_cp, "cp")
            return

        nbreCodes = self.listeNomsVilles.count(villeSelect)
        if nbreCodes > 1:
            listeCodes = [
                cp for ville, cp in self.listeVilles if villeSelect == ville
            ]
            resultat = self.ChoixCodes(villeSelect, listeCodes)
            if resultat != '':
                self.text_cp.SetValue(resultat)
        if nbreCodes == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Cette ville n'est pas répertoriée dans la base de données. \nVérifiez que vous n'avez pas fait d'erreur de saisie."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
        self.SetInfobulleVille(self.text_ville, "ville")
        self.SetInfobulleVille(self.text_cp, "cp")
        self.MaJ_Adresse_Fiche()
        event.Skip()

    def VilleChar2(self, event):
        if event.GetKeyCode() == 8:
            self.text_ville.ignoreEvtText = True
            self.MaJ_Adresse_Fiche()
        event.Skip()

    def VilleText2(self, event):
        if self.autoComplete is False:
            return
        if self.text_ville.ignoreEvtText:
            self.text_ville.ignoreEvtText = False
            self.MaJ_Adresse_Fiche()
            return
        currentText = event.GetString().upper()
        found = False
        try:
            for ville, cp in self.listeVilles:
                if ville.startswith(currentText):
                    self.text_ville.ignoreEvtText = True
                    self.text_ville.SetValue(ville)
                    self.text_ville.SetInsertionPoint(len(currentText))
                    self.text_ville.SetSelection(
                        len(currentText), len(ville)
                    )
                    self.text_cp.SetValue(str(cp))
                    self.MaJ_Adresse_Fiche()
                    self.SetInfobulleVille(self.text_ville, "ville")
                    self.SetInfobulleVille(self.text_cp, "cp")
                    found = True
                    break
        except Exception:
            pass
        if not found:
            self.text_cp.SetValue('')
            self.MaJ_Adresse_Fiche()
            self.SetInfobulleVille(self.text_ville, "ville")
            self.SetInfobulleVille(self.text_cp, "cp")
            event.Skip()

    def ChoixVilles(self, cp, listeReponses):
        resultat = ""
        titre = _(u"Sélection d'une ville")
        listeReponses.sort()
        message = (
            str(len(listeReponses))
            + _(u" villes possèdent le code postal ")
            + str(cp)
            + _(u". Double-cliquez sur\nle nom d'une ville pour la sélectionner :")
        )
        dlg = wx.SingleChoiceDialog(
            self, message, titre, listeReponses, wx.CHOICEDLG_STYLE
        )
        if dlg.ShowModal() == wx.ID_OK:
            resultat = dlg.GetStringSelection()
        dlg.Destroy()
        return resultat

    def ChoixCodes(self, ville, listeReponses):
        resultat = ""
        titre = _(u"Sélection d'une ville")
        listeReponses.sort()
        message = (
            str(len(listeReponses))
            + _(u" villes portent le nom ")
            + str(ville)
            + _(u". Double-cliquez sur\nle code postal d'une ville pour la sélectionner :")
        )
        dlg = wx.SingleChoiceDialog(
            self, message, titre, listeReponses, wx.CHOICEDLG_STYLE
        )
        if dlg.ShowModal() == wx.ID_OK:
            resultat = dlg.GetStringSelection()
        dlg.Destroy()
        return resultat

    # ----------------------------------------------------------------------
    # Sauvegarde / import
    def Sauvegarde(self):
        varCivilite = self.combo_box_civilite.GetStringSelection()
        varNom = self.text_nom.GetValue()
        varNom_JFille = self.text_ctrl_nomjf.GetValue()
        varPrenom = self.text_prenom.GetValue()

        temp = self.text_date_naiss.GetValue()
        if temp == "  /  /    ":
            varDate_Naiss = None
        else:
            jour = int(temp[:2])
            mois = int(temp[3:5])
            annee = int(temp[6:10])
            varDate_Naiss = datetime.date(annee, mois, jour)

        varCp_Naiss = self.text_cp_naiss.GetValue()
        if varCp_Naiss == "     ":
            varCp_Naiss = None
        varVille_Naiss = self.text_ville_naiss.GetValue()
        varPays_Naiss = self.IDpays_naiss
        varNationalite = self.IDpays_nation
        varNum_Secu = self.text_numsecu.GetValue()
        varAdresse_resid = self.text_adresse.GetValue()
        varCp_Resid = self.text_cp.GetValue()
        if varCp_Resid == "     ":
            varCp_Resid = None
        varVille_Resid = self.text_ville.GetValue()
        varMemo = self.text_memo.GetValue()

        try:
            temp = self.combo_box_situation.GetClientData(
                self.combo_box_situation.GetSelection()
            )
            varIDSituation = 0 if temp in (None, '') else temp
        except Exception:
            varIDSituation = 0

        listeDonnees = [
            ("civilite", varCivilite),
            ("nom", varNom),
            ("nom_jfille", varNom_JFille),
            ("prenom", varPrenom),
            ("date_naiss", varDate_Naiss),
            ("cp_naiss", varCp_Naiss),
            ("ville_naiss", varVille_Naiss),
            ("pays_naiss", varPays_Naiss),
            ("nationalite", varNationalite),
            ("num_secu", varNum_Secu),
            ("adresse_resid", varAdresse_resid),
            ("cp_resid", varCp_Resid),
            ("ville_resid", varVille_Resid),
            ("memo", varMemo),
            ("IDsituation", varIDSituation),
        ]

        DB = GestionDB.DB()
        if self.IDpersonne == 0:
            newID = DB.ReqInsert("personnes", listeDonnees)
            self.IDpersonne = newID
            self.GetGrandParent().GetParent().IDpersonne = newID
            self.MaJ_Header_Fiche()
        else:
            DB.ReqMAJ(
                "personnes", listeDonnees, "IDpersonne", self.IDpersonne
            )
        DB.Close()

    def MaJ_Header_Fiche(self):
        self.parent.GetGrandParent().MaJ_header()

    def MaJ_NomPrenom_Fiche(self):
        nom = self.text_nom.GetValue() or "NOM"
        prenom = self.text_prenom.GetValue() or _(u"Prénom")
        self.GetParent().GetGrandParent().label_hd_nomPrenom.SetLabel(
            nom + ", " + prenom
        )

    def MaJ_Adresse_Fiche(self):
        adresse = self.text_adresse.GetValue()
        cp = self.text_cp.GetValue()
        ville = self.text_ville.GetValue()
        if adresse == "" and cp == "     " and ville == "":
            texte = _(u"Adresse inconnue")
        else:
            texte = _(u"Résidant ") + adresse + " " + cp + " " + ville
        self.GetParent().GetGrandParent().label_hd_adresse.SetLabel(texte)

    def MaJ_DateNaiss_Fiche(self):
        dateNaiss = self.text_date_naiss.GetValue()
        villeNaiss = self.text_ville_naiss.GetValue()
        civilite = self.combo_box_civilite.GetStringSelection()
        age = self.text_age.GetValue()
        if civilite == "Mr":
            txtCivilite = u"Né"
        elif civilite == "Mme" or civilite == "Melle":
            txtCivilite = _(u"Née")
        else:
            return
        if dateNaiss == "  /  /    " and villeNaiss == "":
            texte = _(u"Date et lieu de naissance inconnus.")
        elif dateNaiss != "  /  /    " and villeNaiss == "":
            texte = txtCivilite + " le " + dateNaiss + ", " + age
        elif dateNaiss == "  /  /    " and villeNaiss != "":
            texte = txtCivilite + u" à " + villeNaiss + _(u" (date inconnue)")
        else:
            texte = (
                txtCivilite
                + " le "
                + dateNaiss
                + u" à "
                + villeNaiss
                + ", "
                + age
            )
        self.GetParent().GetGrandParent().label_hd_naiss.SetLabel(texte)

    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT civilite, nom, nom_jfille, prenom, date_naiss,
        cp_naiss, ville_naiss, pays_naiss, nationalite, num_secu,
        adresse_resid, cp_resid, ville_resid, memo, IDsituation
        FROM personnes WHERE IDpersonne = %d""" % self.IDpersonne
        DB.ExecuterReq(req)
        resultats = DB.ResultatReq()
        DB.Close()
        if not resultats:
            return
        donnees = resultats[0]

        (
            civilite,
            nom,
            nom_jfille,
            prenom,
            date_naiss,
            cp_naiss,
            ville_naiss,
            pays_naiss,
            nationalite,
            num_secu,
            adresse_resid,
            cp_resid,
            ville_resid,
            memo,
            IDsituation,
        ) = donnees

        self.autoComplete = False
        self.text_ctrl_nomjf.SetValue(nom_jfille or "")
        self.text_nom.SetValue(nom or "")
        self.text_prenom.SetValue(prenom or "")
        self.text_ville_naiss.SetValue(ville_naiss or "")
        self.text_adresse.SetValue(adresse_resid or "")
        self.text_ville.SetValue(ville_resid or "")
        self.text_memo.SetValue(memo or "")
        self.text_numsecu.SetValue(num_secu or "")

        try:
            if cp_resid not in ("", None, "     "):
                if isinstance(cp_resid, six.text_type):
                    cp_resid = int(cp_resid)
                self.text_cp.SetValue("%05d" % cp_resid)
            if cp_naiss not in ("", None, "     "):
                if isinstance(cp_naiss, six.text_type):
                    cp_naiss = int(cp_naiss)
                self.text_cp_naiss.SetValue("%05d" % cp_naiss)
        except Exception:
            dlg = wx.MessageDialog(
                self,
                _(u"Erreur dans l'importation des codes postaux."),
                "Erreur",
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()

        self.text_date_naiss.SetValue(
            UTILS_Dates.DateEngFr(date_naiss) or "  /  /    "
        )
        self.combo_box_civilite.SetStringSelection(civilite or "")
        for IDsitu, situation in self.listeSituations:
            if IDsituation is not None and int(IDsitu) == int(IDsituation):
                self.combo_box_situation.SetStringSelection(situation)

        if pays_naiss:
            self.SetPaysNaiss(IDpays=pays_naiss)
        if nationalite:
            self.SetNationalite(IDpays=nationalite)

        self.autoComplete = True
        self.MaJ_Civilite()
        self.MaJ_DateNaiss()
        self.SetInfobulleVille(self.text_cp_naiss, "cp_naiss")
        self.SetInfobulleVille(self.text_cp, "cp")
        self.SetInfobulleVille(self.text_ville_naiss, "ville_naiss")
        self.SetInfobulleVille(self.text_ville, "ville")

    def _bitmap_drapeau(self, code):
        path = Chemins.GetStaticPath("Images/Drapeaux/%s.png" % code)
        bitmap = wx.Bitmap(path, wx.BITMAP_TYPE_PNG)
        largeur = UTILS_Styles.Scale(28)
        hauteur = UTILS_Styles.Scale(18)
        if bitmap.IsOk() and (
            bitmap.GetWidth() != largeur or bitmap.GetHeight() != hauteur
        ):
            bitmap = wx.Bitmap(
                bitmap.ConvertToImage().Scale(
                    largeur, hauteur, wx.IMAGE_QUALITY_HIGH
                )
            )
        return bitmap

    def SetPaysNaiss(self, IDpays):
        if not IDpays:
            return
        pays = self.Recherche_Pays(IDpays=IDpays)
        if not pays:
            return
        self.image_pays.SetBitmap(self._bitmap_drapeau(pays[1]))
        self.image_pays.SetToolTip(
            wx.ToolTip(_(u"Pays de naissance : %s" % pays[2]))
        )
        self.IDpays_naiss = IDpays

    def SetNationalite(self, IDpays):
        if not IDpays:
            return
        pays = self.Recherche_Pays(IDpays=IDpays)
        if not pays:
            return
        self.image_nation.SetBitmap(self._bitmap_drapeau(pays[1]))
        self.image_nation.SetToolTip(
            wx.ToolTip(_(u"Nationalité : %s" % pays[3]))
        )
        self.IDpays_nation = IDpays

    def ImportListeSituations(self):
        try:
            temp = self.combo_box_situation.GetClientData(
                self.combo_box_situation.GetSelection()
            )
            IDSituation = 0 if temp in (None, '') else temp
        except Exception:
            IDSituation = 0

        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT * FROM situations")
        self.listeSituations = DB.ResultatReq()
        DB.Close()
        self.combo_box_situation.Clear()
        for key, valeur in self.listeSituations:
            self.combo_box_situation.Append(valeur, key)
        if IDSituation != 0:
            try:
                for IDsitu, situation in self.listeSituations:
                    if int(IDsitu) == int(IDSituation):
                        self.combo_box_situation.SetStringSelection(situation)
            except Exception:
                pass

    def Recherche_Pays(self, IDpays=0, nomPays=""):
        DB = GestionDB.DB()
        if nomPays == "":
            req = (
                "SELECT IDpays, code_drapeau, nom, nationalite "
                "FROM pays WHERE IDpays=%d" % IDpays
            )
        else:
            req = (
                "SELECT IDpays, code_drapeau, nom, nationalite "
                "FROM pays WHERE nom='%s'" % nomPays
            )
        DB.ExecuterReq(req)
        listePays = DB.ResultatReq()
        DB.Close()
        if len(listePays) == 0:
            return None
        return listePays[0]


# --------------------------------------------------------------------------
# Validations historiques

def ValideNumSecu(texte, civilite, date_naiss, dep_naiss):
    texteSansEsp = "".join(lettre for lettre in texte if lettre != " ")
    nbreChiffres = len(texteSansEsp)
    if nbreChiffres == 0:
        return None, ""
    if nbreChiffres < 15:
        return (
            False,
            _(u"Il manque ")
            + str(15 - nbreChiffres)
            + _(u" chiffre(s) au numéro de sécurité sociale que vous venez de saisir. Veuillez le vérifier."),
        )

    if nbreChiffres == 15:
        if civilite == "Mr" and int(texteSansEsp[0]) != 1:
            return (
                False,
                _(u"Le numéro de sécurité sociale ne correspond pas à la civilité de la personne (le premier chiffre devrait être 1)."),
            )
        if (civilite == "Melle" or civilite == "Mme") and int(
            texteSansEsp[0]
        ) != 2:
            return (
                False,
                _(u"Le numéro de sécurité sociale ne correspond pas à la civilité de la personne (le premier chiffre devrait être 2)."),
            )

        if date_naiss != "  /  /    ":
            mois = str(date_naiss[3:5])
            annee = str(date_naiss[8:10])
            if annee != str(texteSansEsp[1:3]) or mois != str(
                texteSansEsp[3:5]
            ):
                return (
                    False,
                    _(u"Le numéro de sécurité sociale ne correspond pas à la date de naissance de la personne."),
                )

        if dep_naiss != "":
            dep = dep_naiss[0:2]
            if str(dep) != str(texteSansEsp[5:7]):
                return (
                    False,
                    _(u"Le numéro de sécurité sociale ne correspond pas au lieu de naissance de la personne."),
                )

        cle = int(texteSansEsp[13:15])
        cle_calculee = 97 - (int(texteSansEsp[:13]) % 97)
        if cle != cle_calculee:
            return (
                False,
                _(u"La clé du numéro de sécurité sociale ne semble pas cohérente. \nD'après mes calculs, la bonne clé devrait être %02d. \n\nVeuillez vérifier votre saisie...")
                % cle_calculee,
            )
        return True, ""
    return False, _(u"Le numéro de sécurité sociale n'est pas valide.")


def ValideDate(texte, date_min="01/01/1900", date_max="01/01/2090"):
    listeErreurs = []
    if texte[0] == " " or texte[1] == " ":
        listeErreurs.append(_(u"le jour"))
    if texte[3] == " " or texte[4] == " ":
        listeErreurs.append(_(u"le mois"))
    if (
        texte[6] == " "
        or texte[7] == " "
        or texte[8] == " "
        or texte[9] == " "
    ):
        listeErreurs.append(_(u"l'année"))

    if texte == "  /  /    ":
        return True

    if _(u"le jour") not in listeErreurs:
        jour = int(texte[:2])
        if jour == 0 or jour > 31:
            listeErreurs.append(_(u"le jour"))
    if _(u"le mois") not in listeErreurs:
        mois = int(texte[3:5])
        if mois == 0 or mois > 12:
            listeErreurs.append(_(u"le mois"))
    if _(u"l'année") not in listeErreurs:
        annee = int(texte[6:10])
        if annee < 1900 or annee > 2999:
            listeErreurs.append(_(u"l'année"))

    if len(listeErreurs) != 0:
        if len(listeErreurs) == 1:
            message = _(u"Une incohérence a été détectée dans ") + listeErreurs[0]
        elif len(listeErreurs) == 2:
            message = (
                _(u"Des incohérences ont été détectées dans ")
                + listeErreurs[0]
                + " et "
                + listeErreurs[1]
            )
        else:
            message = (
                _(u"Des incohérences ont été détectées dans ")
                + listeErreurs[0]
                + ", "
                + listeErreurs[1]
                + " et "
                + listeErreurs[2]
            )
        wx.MessageBox(
            message
            + _(u" de la date que vous venez de saisir. Veuillez la vérifier."),
            "Erreur de date",
        )
        return False

    date_min_int = int(
        str(date_min[6:10]) + str(date_min[3:5]) + str(date_min[:2])
    )
    date_max_int = int(
        str(date_max[6:10]) + str(date_max[3:5]) + str(date_max[:2])
    )
    date_sel = int(str(texte[6:10]) + str(texte[3:5]) + str(texte[:2]))
    if date_sel < date_min_int:
        wx.MessageBox(
            _(u"La date que vous venez de saisir semble trop ancienne. Veuillez la vérifier."),
            "Erreur de date",
        )
        return False
    if date_sel > date_max_int:
        wx.MessageBox(
            _(u"La date que vous venez de saisir semble trop élevée. Veuillez la vérifier."),
            "Erreur de date",
        )
        return False
    return True


# --------------------------------------------------------------------------
# Liste des coordonnées

class ListCtrlCoords(wx.ListCtrl):
    def __init__(self, parent, id, owner=None):
        wx.ListCtrl.__init__(
            self,
            parent,
            id,
            style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL | wx.BORDER_NONE,
        )
        self.parent = parent
        self.owner = owner or parent
        self.popupIndex = -1
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )

        self.Bind(wx.EVT_SIZE, self.OnSize)
        taille = UTILS_Styles.GetIconSize("medium")[0]
        self.il = wx.ImageList(taille, taille)
        self.imgMaison = self.il.Add(self._bitmap("Maison.png", taille))
        self.imgMobile = self.il.Add(self._bitmap("Mobile.png", taille))
        self.imgFax = self.il.Add(self._bitmap("Fax.png", taille))
        self.imgMail = self.il.Add(self._bitmap("Mail.png", taille))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.InsertColumn(0, "")
        self.Remplissage()

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

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

    def Remplissage(self):
        self.Importation()
        self.DeleteAllItems()
        for index, (key, valeurs) in enumerate(self.DictCoords.items()):
            categorie = valeurs[2]
            texte = valeurs[3]
            self.InsertItem(index, texte)
            image = {
                "Fixe": self.imgMaison,
                "Mobile": self.imgMobile,
                "Fax": self.imgFax,
                "Email": self.imgMail,
            }.get(categorie)
            if image is not None:
                self.SetItemImage(index, image)
            self.SetItemData(index, key)
        wx.CallAfter(self._ajuster_colonne)

    def Importation(self):
        DB = GestionDB.DB()
        req = "SELECT * FROM coordonnees WHERE IDpersonne = %d" % self.owner.IDpersonne
        DB.ExecuterReq(req)
        self.DictCoords = self.listeEnDict(DB.ResultatReq())
        DB.Close()

    def listeEnDict(self, liste):
        return {ligne[0]: ligne for ligne in liste}

    def OnItemSelected(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
        event.Skip()

    def OnItemActivated(self, event):
        self.DestroyPopup()
        self.owner.ModifierCoord()
        event.Skip()

    def OnSize(self, event):
        self._ajuster_colonne()
        event.Skip()

    def _ajuster_colonne(self):
        largeur = self.GetClientSize().GetWidth()
        if largeur > 0:
            self.SetColumnWidth(0, max(0, largeur - UTILS_Styles.GetSpacing("xs")))

    def OnMouseMotion(self, event):
        index = self.HitTest(event.GetPosition())[0]
        if index == -1:
            if self.popupIndex != -1:
                self.DestroyPopup()
            return
        pos = self.ClientToScreen(event.GetPosition())
        decalage = (-UTILS_Styles.Scale(130), -UTILS_Styles.Scale(70))
        posInListCtrl = event.GetPosition()
        if self.popupIndex != -1 and (
            posInListCtrl[0] < 4 or posInListCtrl[1] < 4
        ):
            self.DestroyPopup()
            return
        if self.popupIndex == index:
            self.Popup.Position(pos, decalage)
        if self.popupIndex != index and self.popupIndex != -1:
            self.DestroyPopup()
        if (
            self.popupIndex != index
            and posInListCtrl[0] > 3
            and posInListCtrl[1] > 3
        ):
            key = self.GetItemData(index)
            self.popupIndex = index
            self.Popup = TestPopup(self, key=key)
            self.Popup.Position(pos, decalage)
            self.Popup.Show(True)
            self.CaptureMouse()

    def DestroyPopup(self):
        if self.HasCapture():
            self.ReleaseMouse()
        try:
            self.Popup.Destroy()
        except Exception:
            pass
        self.popupIndex = -1

    def OnContextMenu(self, event):
        self.DestroyPopup()
        if self.GetFirstSelected() == -1:
            return False
        index = self.GetFirstSelected()
        key = self.GetItemData(index)
        menuPop = UTILS_Adaptations.Menu()

        for identifiant, label, callback in (
            (10, _(u"Ajouter"), self.Menu_Ajouter),
            (20, _(u"Modifier"), self.Menu_Modifier),
            (30, _(u"Supprimer"), self.Menu_Supprimer),
        ):
            item = wx.MenuItem(menuPop, identifiant, label)
            menuPop.AppendItem(item)
            self.Bind(wx.EVT_MENU, callback, id=identifiant)
            if identifiant == 10:
                menuPop.AppendSeparator()

        if self.DictCoords[key][2] == "Email":
            menuPop.AppendSeparator()
            item = wx.MenuItem(menuPop, 40, _(u"Envoyer un e-mail"))
            menuPop.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.Menu_Envoyer_Email, id=40)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.owner.AjouterCoord()

    def Menu_Modifier(self, event):
        self.owner.ModifierCoord()

    def Menu_Supprimer(self, event):
        self.owner.SupprimerCoord()

    def Menu_Envoyer_Email(self, event):
        index = self.GetFirstSelected()
        key = self.GetItemData(index)
        FonctionsPerso.EnvoyerMail(adresses=(self.DictCoords[key][3],))


class TestPopup(wx.PopupWindow):
    def __init__(self, parent, style=wx.SIMPLE_BORDER, key=0):
        wx.PopupWindow.__init__(self, parent, style)
        self.parent = parent
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_high")
        )
        valeurs = self.parent.DictCoords[key]
        categorie = valeurs[2]
        texte = valeurs[3]
        intitule = valeurs[4]

        image_name = {
            "Fixe": "Maison.png",
            "Mobile": "Mobile.png",
            "Fax": "Fax.png",
            "Email": "Mail.png",
        }.get(categorie, "Maison.png")
        bitmap = wx.Bitmap(
            Chemins.GetStaticPath("Images/32x32/" + image_name),
            wx.BITMAP_TYPE_PNG,
        )
        taille = UTILS_Styles.GetIconSize("hero")[0]
        if bitmap.IsOk() and (
            bitmap.GetWidth() != taille or bitmap.GetHeight() != taille
        ):
            bitmap = wx.Bitmap(
                bitmap.ConvertToImage().Scale(
                    taille, taille, wx.IMAGE_QUALITY_HIGH
                )
            )

        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_high")
        )
        image = wx.StaticBitmap(panel, -1, bitmap)
        label_coords = CTRL_Texte.H5(panel, texte)
        label_intitule = CTRL_Texte.Caption(panel, intitule or "")

        textes = wx.BoxSizer(wx.VERTICAL)
        textes.Add(label_coords, 0, wx.EXPAND)
        textes.Add(label_intitule, 0, wx.EXPAND | wx.TOP, UTILS_Styles.GetSpacing("xs"))
        contenu = wx.BoxSizer(wx.HORIZONTAL)
        contenu.Add(image, 0, wx.ALL | wx.ALIGN_TOP, UTILS_Styles.GetSpacing("sm"))
        contenu.Add(textes, 1, wx.EXPAND | wx.TOP | wx.RIGHT | wx.BOTTOM, UTILS_Styles.GetSpacing("sm"))
        panel.SetSizer(contenu)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)
        wx.CallAfter(self.Refresh)
