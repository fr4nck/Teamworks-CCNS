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
import datetime
import decimal
import sqlite3
import sys
import wx.lib.masked as masked

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from infrastructure.persistence.person_reader import PersonReader
import FonctionsPerso
import GestionDB

if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else:
    from wx import DatePickerCtrl, DP_DROPDOWN



def _dialog_parent(window):
    current = window
    while current is not None and not isinstance(current, SaisieDeplacement):
        current = current.GetParent()
    return current


class SaisieDeplacement(wx.Dialog):
    """Saisie d'un déplacement pour les frais de déplacement."""

    def __init__(self, parent, id=-1, title=_(u"Saisie d'un déplacement"), IDdeplacement=None, IDpersonne=None):
        wx.Dialog.__init__(
            self,
            parent,
            id,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.IDdeplacement = IDdeplacement
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        con = sqlite3.connect(Chemins.GetStaticPath("Databases/Villes.db3"))
        cur = con.cursor()
        cur.execute("SELECT ville, cp FROM villes")
        self.listeVillesTmp = cur.fetchall()
        con.close()

        self.listeNomsVilles = []
        self.listeVilles = []
        for nom, cp in self.listeVillesTmp:
            self.listeVilles.append((nom, "%05d" % cp))
            self.listeNomsVilles.append(nom)

        self.ImportationDistances()

        # Généralités
        self.section_generalites = CTRL_Section.Section(
            self,
            titre=_(u"Généralités"),
            niveau=2,
        )
        panel_generalites = self.section_generalites.GetContentPanel()
        self.label_date = CTRL_Texte.Label(panel_generalites, _(u"Date"))
        self.ctrl_date = DatePickerCtrl(panel_generalites, -1, style=DP_DROPDOWN)
        self.label_utilisateur = CTRL_Texte.Label(panel_generalites, _(u"Utilisateur"))
        self.ImportationPersonnes()
        self.ctrl_utilisateur = AdvancedComboBox(
            panel_generalites,
            "",
            choices=self.listePersonnes,
        )
        self.label_objet = CTRL_Texte.Label(panel_generalites, _(u"Objet"))
        self.ctrl_objet = wx.TextCtrl(panel_generalites, -1, "", style=wx.TE_MULTILINE)
        self.ctrl_objet.SetMinSize((-1, UTILS_Styles.Scale(72)))

        # Trajet
        self.section_trajet = CTRL_Section.Section(
            self,
            titre=_(u"Trajet"),
            niveau=2,
        )
        panel_trajet = self.section_trajet.GetContentPanel()
        self.label_depart = CTRL_Texte.Label(panel_trajet, _(u"Ville de départ"))
        self.ctrl_cp_depart = TextCtrlCp(
            panel_trajet,
            value="",
            listeVilles=self.listeVilles,
            style=wx.TE_CENTRE,
            mask="#####",
        )
        self.ctrl_ville_depart = TextCtrlVille(
            panel_trajet,
            value="",
            ctrlCp=self.ctrl_cp_depart,
            listeVilles=self.listeVilles,
            listeNomsVilles=self.listeNomsVilles,
        )
        self.ctrl_cp_depart.ctrlVille = self.ctrl_ville_depart
        self.bouton_options_depart = CTRL_Bouton_image.CTRL(
            panel_trajet,
            texte=_(u"Rechercher"),
        )

        self.label_arrivee = CTRL_Texte.Label(panel_trajet, _(u"Ville d'arrivée"))
        self.ctrl_cp_arrivee = TextCtrlCp(
            panel_trajet,
            value="",
            listeVilles=self.listeVilles,
            style=wx.TE_CENTRE,
            mask="#####",
        )
        self.ctrl_ville_arrivee = TextCtrlVille(
            panel_trajet,
            value="",
            ctrlCp=self.ctrl_cp_arrivee,
            listeVilles=self.listeVilles,
            listeNomsVilles=self.listeNomsVilles,
        )
        self.ctrl_cp_arrivee.ctrlVille = self.ctrl_ville_arrivee
        self.bouton_options_arrivee = CTRL_Bouton_image.CTRL(
            panel_trajet,
            texte=_(u"Rechercher"),
        )

        self.label_distance = CTRL_Texte.Label(panel_trajet, _(u"Distance"))
        self.ctrl_distance = wx.TextCtrl(panel_trajet, -1, "0")
        self.label_km = CTRL_Texte.BodySecondary(panel_trajet, _(u"Km (aller simple)"))
        self.label_aller_retour = CTRL_Texte.Label(panel_trajet, _(u"Aller / retour"))
        self.ctrl_aller_retour = wx.CheckBox(panel_trajet, -1, u"")

        if "linux" in sys.platform:
            self.ctrl_ville_depart.Enable(False)
            self.ctrl_ville_arrivee.Enable(False)

        # Remboursement
        self.section_remboursement = CTRL_Section.Section(
            self,
            titre=_(u"Remboursement"),
            niveau=2,
        )
        panel_remboursement = self.section_remboursement.GetContentPanel()
        self.label_tarif = CTRL_Texte.Label(panel_remboursement, _(u"Tarif du km"))
        self.ctrl_tarif = wx.TextCtrl(panel_remboursement, -1, "0.00")
        self.label_euro_tarif = CTRL_Texte.Body(panel_remboursement, u"€")
        self.label_montant = CTRL_Texte.Label(panel_remboursement, _(u"Montant"))
        self.ctrl_montant = CTRL_Texte.DataLarge(panel_remboursement, u"0.00 €")
        self.label_remboursement = CTRL_Texte.Label(panel_remboursement, _(u"Remboursement associé"))
        self.ctrl_remboursement = CTRL_Texte.BodySecondary(
            panel_remboursement,
            _(u"Aucun remboursement."),
        )

        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_OK,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )
        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )

        if self.IDpersonne is not None:
            self.SetPersonne(self.IDpersonne)
        if self.IDdeplacement is not None:
            self.SetTitle(_(u"Modification d'un déplacement"))
            self.Importation()
        else:
            self.ImportDernierTarif()
        if self.IDpersonne is not None:
            self.label_utilisateur.Hide()
            self.ctrl_utilisateur.Hide()

        self.__set_properties()
        self.__do_layout(panel_generalites, panel_trajet, panel_remboursement)

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOptionsDepart, self.bouton_options_depart)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOptionsArrivee, self.bouton_options_arrivee)
        self.Bind(wx.EVT_CHECKBOX, self.OnAllerRetour, self.ctrl_aller_retour)
        self.ctrl_distance.Bind(wx.EVT_KILL_FOCUS, self.distance_EvtKillFocus)
        self.ctrl_tarif.Bind(wx.EVT_KILL_FOCUS, self.tarif_EvtKillFocus)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Valider le déplacement")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Annuler la saisie")))
        self.ctrl_date.SetToolTip(wx.ToolTip(_(u"Sélectionnez ici la date du déplacement")))
        self.ctrl_utilisateur.SetToolTip(wx.ToolTip(_(u"Sélectionnez ici l'utilisateur pour ce déplacement")))
        self.ctrl_objet.SetToolTip(wx.ToolTip(_(u"Saisissez ici l'objet du déplacement. Ex : réunion, formation, etc...")))
        self.ctrl_cp_depart.SetToolTip(wx.ToolTip(_(u"Saisissez ici le code postal de la ville de départ")))
        self.ctrl_ville_depart.SetToolTip(wx.ToolTip(_(u"Saisissez ici le nom de la ville de départ")))
        self.ctrl_cp_arrivee.SetToolTip(wx.ToolTip(_(u"Saisissez ici le code postal de la ville d'arrivée")))
        self.ctrl_ville_arrivee.SetToolTip(wx.ToolTip(_(u"Saisissez ici le nom de la ville d'arrivée")))
        self.ctrl_distance.SetToolTip(wx.ToolTip(_(u"Saisissez ici la distance en Km entre les deux villes. Si Teamworks la connaît, il l'indiquera automatiquement.")))
        self.ctrl_aller_retour.SetToolTip(wx.ToolTip(_(u"Cochez cette case si le déplacement comporte un aller et un retour.")))
        self.ctrl_tarif.SetToolTip(wx.ToolTip(_(u"Saisissez ici le tarif kilométrique permettant de calculer le remboursement.")))
        self.bouton_options_depart.SetToolTip(wx.ToolTip(_(u"Rechercher ou saisir une ville de départ")))
        self.bouton_options_arrivee.SetToolTip(wx.ToolTip(_(u"Rechercher ou saisir une ville d'arrivée")))
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def __do_layout(self, panel_generalites, panel_trajet, panel_remboursement):
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")
        xs = UTILS_Styles.GetSpacing("xs")

        generalites = wx.BoxSizer(wx.VERTICAL)
        ligne_date = wx.BoxSizer(wx.HORIZONTAL)
        ligne_date.Add(self.label_date, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_date.Add(self.ctrl_date, 0)
        generalites.Add(ligne_date, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        ligne_utilisateur = wx.BoxSizer(wx.HORIZONTAL)
        ligne_utilisateur.Add(self.label_utilisateur, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_utilisateur.Add(self.ctrl_utilisateur, 1, wx.EXPAND)
        generalites.Add(ligne_utilisateur, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        generalites.Add(self.label_objet, 0, wx.EXPAND | wx.BOTTOM, xs)
        generalites.Add(self.ctrl_objet, 1, wx.EXPAND)
        panel_generalites.SetSizer(generalites)

        trajet = wx.BoxSizer(wx.VERTICAL)
        trajet.Add(self.label_depart, 0, wx.EXPAND | wx.BOTTOM, xs)
        ligne_depart = wx.BoxSizer(wx.HORIZONTAL)
        self.ctrl_cp_depart.SetMinSize((UTILS_Styles.Scale(82), -1))
        ligne_depart.Add(self.ctrl_cp_depart, 0, wx.RIGHT, field_gap)
        ligne_depart.Add(self.ctrl_ville_depart, 1, wx.RIGHT, field_gap)
        ligne_depart.Add(self.bouton_options_depart, 0)
        trajet.Add(ligne_depart, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        trajet.Add(self.label_arrivee, 0, wx.EXPAND | wx.BOTTOM, xs)
        ligne_arrivee = wx.BoxSizer(wx.HORIZONTAL)
        self.ctrl_cp_arrivee.SetMinSize((UTILS_Styles.Scale(82), -1))
        ligne_arrivee.Add(self.ctrl_cp_arrivee, 0, wx.RIGHT, field_gap)
        ligne_arrivee.Add(self.ctrl_ville_arrivee, 1, wx.RIGHT, field_gap)
        ligne_arrivee.Add(self.bouton_options_arrivee, 0)
        trajet.Add(ligne_arrivee, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        ligne_distance = wx.BoxSizer(wx.HORIZONTAL)
        ligne_distance.Add(self.label_distance, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        self.ctrl_distance.SetMinSize((UTILS_Styles.Scale(100), -1))
        ligne_distance.Add(self.ctrl_distance, 0, wx.RIGHT, field_gap)
        ligne_distance.Add(self.label_km, 0, wx.ALIGN_CENTER_VERTICAL)
        ligne_distance.AddStretchSpacer(1)
        ligne_distance.Add(self.label_aller_retour, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_distance.Add(self.ctrl_aller_retour, 0, wx.ALIGN_CENTER_VERTICAL)
        trajet.Add(ligne_distance, 0, wx.EXPAND)
        panel_trajet.SetSizer(trajet)

        remboursement = wx.BoxSizer(wx.VERTICAL)
        ligne_tarif = wx.BoxSizer(wx.HORIZONTAL)
        ligne_tarif.Add(self.label_tarif, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        self.ctrl_tarif.SetMinSize((UTILS_Styles.Scale(100), -1))
        ligne_tarif.Add(self.ctrl_tarif, 0, wx.RIGHT, xs)
        ligne_tarif.Add(self.label_euro_tarif, 0, wx.ALIGN_CENTER_VERTICAL)
        ligne_tarif.AddStretchSpacer(1)
        ligne_tarif.Add(self.label_montant, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_tarif.Add(self.ctrl_montant, 0, wx.ALIGN_CENTER_VERTICAL)
        remboursement.Add(ligne_tarif, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        ligne_rattachement = wx.BoxSizer(wx.HORIZONTAL)
        ligne_rattachement.Add(self.label_remboursement, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_rattachement.Add(self.ctrl_remboursement, 1, wx.ALIGN_CENTER_VERTICAL)
        remboursement.Add(ligne_rattachement, 0, wx.EXPAND)
        panel_remboursement.SetSizer(remboursement)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, toolbar_gap)
        actions.Add(self.bouton_annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.section_generalites, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, page_gap)
        sizer.Add(self.section_trajet, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, section_gap)
        sizer.Add(self.section_remboursement, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, section_gap)
        sizer.Add(actions, 0, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)
        self.Layout()

    def ImportDernierTarif(self):
        DB = GestionDB.DB()
        req = "SELECT cp_depart, ville_depart, tarif_km FROM deplacements ORDER BY IDdeplacement DESC LIMIT 1;"
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return
        cp_depart, ville_depart, tarif_km = listeDonnees[0]
        self.ctrl_cp_depart.autoComplete = False
        self.ctrl_ville_depart.autoComplete = False
        self.ctrl_cp_depart.SetValue(str(cp_depart))
        self.ctrl_ville_depart.SetValue(ville_depart)
        self.ctrl_cp_depart.autoComplete = True
        self.ctrl_ville_depart.autoComplete = True
        self.ctrl_tarif.SetValue(str(tarif_km))

    def OnBoutonOptionsDepart(self, event):
        print("options ville depart")

    def OnBoutonOptionsArrivee(self, event):
        print("options ville arrivee")

    def ImportationPersonnes(self):
        reader = PersonReader()
        listeDonnees = reader.lire_identites()
        reader.close()
        self.listePersonnes = []
        self.dictPersonnes = {}
        for index, (IDpersonne, nom, prenom) in enumerate(listeDonnees):
            self.listePersonnes.append(nom + " " + prenom)
            self.dictPersonnes[index] = IDpersonne

    def ImportationDistances(self):
        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT * FROM distances")
        self.listeDistances = DB.ResultatReq()
        DB.Close()

    def Importation(self):
        DB = GestionDB.DB()
        req = "SELECT * FROM deplacements WHERE IDdeplacement=%d;" % self.IDdeplacement
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return
        self.IDpersonne = listeDonnees[0][1]
        self.SetPersonne(self.IDpersonne)
        date = listeDonnees[0][2]
        self.SetDate(datetime.date(year=int(date[:4]), month=int(date[5:7]), day=int(date[8:10])))
        self.ctrl_objet.SetValue(listeDonnees[0][3])
        self.SetVilleDepart(str(listeDonnees[0][4]), listeDonnees[0][5])
        self.SetVilleArrivee(str(listeDonnees[0][6]), listeDonnees[0][7])
        self.ctrl_distance.SetValue(str(listeDonnees[0][8]))
        self.SetAllerRetour(listeDonnees[0][9] == "True")
        self.ctrl_tarif.SetValue(str(listeDonnees[0][10]))
        self.CalcMontantRmbst()
        self.SetRemboursement(listeDonnees[0][11])

    def SetRemboursement(self, IDremboursement=None):
        if IDremboursement is None or IDremboursement == 0 or IDremboursement == "":
            self.ctrl_remboursement.SetLabel(_(u"Aucun remboursement."))
            self.ctrl_remboursement.SetForegroundColour(
                UTILS_Interface.GetToken("on_surface_variant")
            )
            return
        DB = GestionDB.DB()
        req = "SELECT date FROM remboursements WHERE IDremboursement=%d;" % IDremboursement
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if not listeDonnees:
            return
        dateRemboursement = self.DateEngFr(listeDonnees[0][0])
        self.ctrl_remboursement.SetLabel(
            "N°" + str(IDremboursement) + " du " + dateRemboursement
        )
        self.ctrl_remboursement.SetForegroundColour(UTILS_Interface.GetToken("success"))

    def DateEngFr(self, textDate):
        return str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])

    def SetAllerRetour(self, etat=False):
        self.ctrl_aller_retour.SetValue(etat)
        if etat is False:
            self.label_km.SetLabel(_(u"Km (aller simple)"))
        else:
            self.label_km.SetLabel(_(u"Km (aller / retour)"))

    def OnAllerRetour(self, event):
        if self.ValideControleFloat(self.ctrl_distance) is False:
            return
        distanceActuelle = float(self.ctrl_distance.GetValue())
        if self.ctrl_aller_retour.GetValue() is False:
            self.label_km.SetLabel(_(u"Km (aller simple)"))
            self.ctrl_distance.SetValue(str(distanceActuelle / 2.0))
        else:
            self.label_km.SetLabel(_(u"Km (aller / retour)"))
            self.ctrl_distance.SetValue(str(distanceActuelle * 2.0))
        self.CalcMontantRmbst()

    def CalcMontantRmbst(self):
        if self.ValideControleFloat(self.ctrl_distance) is False:
            return
        if self.ValideControleFloat(self.ctrl_tarif) is False:
            return
        distance = decimal.Decimal(self.ctrl_distance.GetValue())
        tarif = decimal.Decimal(self.ctrl_tarif.GetValue())
        montant = distance * tarif
        self.ctrl_montant.SetLabel(u"%.2f €" % montant)

    def distance_EvtKillFocus(self, event):
        if self.ValideControleFloat(self.ctrl_distance) is False:
            dlg = wx.MessageDialog(
                self,
                _(u"La distance saisie n'est pas correcte. \nElle doit être sous la forme '32.50' ou '54' par exemple..."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_distance.SetFocus()
            return
        self.CalcMontantRmbst()
        event.Skip()

    def tarif_EvtKillFocus(self, event):
        if self.ValideControleFloat(self.ctrl_tarif) is False:
            dlg = wx.MessageDialog(
                self,
                _(u"Le tarif n'est pas valide. \nIl doit être sous la forme '0.32' ou '1.53' par exemple..."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_tarif.SetFocus()
            return
        self.CalcMontantRmbst()
        event.Skip()

    def ValideControleFloat(self, controle=None):
        valeur = controle.GetValue()
        if any(lettre not in "0123456789." for lettre in valeur):
            return False
        try:
            float(valeur)
        except Exception:
            controle.SetValue("0.0")
            self.CalcMontantRmbst()
            return False
        return True

    def MajDistance(self):
        depart = (self.ctrl_cp_depart.GetValue(), self.ctrl_ville_depart.GetValue())
        arrivee = (self.ctrl_cp_arrivee.GetValue(), self.ctrl_ville_arrivee.GetValue())
        for IDdistance, cp_depart, ville_depart, cp_arrivee, ville_arrivee, distance in self.listeDistances:
            depart_temp = (str(cp_depart), ville_depart)
            arrivee_temp = (str(cp_arrivee), ville_arrivee)
            if (depart == depart_temp and arrivee == arrivee_temp) or (
                depart == arrivee_temp and arrivee == depart_temp
            ):
                if self.ctrl_aller_retour.GetValue() is True:
                    self.ctrl_distance.SetValue(str(distance * 2.0))
                else:
                    self.ctrl_distance.SetValue(str(distance * 1.0))
                break
        self.CalcMontantRmbst()

    def SetVilleDepart(self, cp=None, ville=None):
        if cp is not None:
            self.ctrl_cp_depart.autoComplete = False
            self.ctrl_cp_depart.SetValue(cp)
            self.ctrl_cp_depart.autoComplete = True
        if ville is not None:
            self.ctrl_ville_depart.autoComplete = False
            self.ctrl_ville_depart.SetValue(ville.upper())
            self.ctrl_ville_depart.autoComplete = True

    def SetVilleArrivee(self, cp=None, ville=None):
        if cp is not None:
            self.ctrl_cp_arrivee.autoComplete = False
            self.ctrl_cp_arrivee.SetValue(cp)
            self.ctrl_cp_arrivee.autoComplete = True
        if ville is not None:
            self.ctrl_ville_arrivee.autoComplete = False
            self.ctrl_ville_arrivee.SetValue(ville.upper())
            self.ctrl_ville_arrivee.autoComplete = True

    def SetPersonne(self, IDpersonne=None):
        for index, IDpers in self.dictPersonnes.items():
            if IDpersonne == IDpers:
                self.ctrl_utilisateur.Select(index)
                break

    def SetDate(self, date):
        self.SetDatePicker(self.ctrl_date, date)

    def SetDatePicker(self, controle, date):
        date_wx = wx.DateTime()
        date_wx.Set(int(date.day), int(date.month) - 1, int(date.year))
        controle.SetValue(date_wx)

    def GetDatePickerValue(self, controle):
        date_tmp = controle.GetValue()
        return datetime.date(
            date_tmp.GetYear(),
            date_tmp.GetMonth() + 1,
            date_tmp.GetDay(),
        )

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Enregistrerundplacement")

    def OnBoutonOk(self, event):
        valeur = self.ctrl_utilisateur.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez obligatoirement sélectionner un utilisateur."),
                "Erreur",
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_utilisateur.SetFocus()
            return

        valeur = self.ctrl_objet.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous n'avez pas saisi d'objet pour ce déplacement. \n\nVoulez-vous quand même valider ce déplacement ?\n(Cliquez sur 'Non' ou 'Annuler' pour modifier maintenant l'objet)"),
                _(u"Erreur de saisie"),
                wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION,
            )
            reponse = dlg.ShowModal()
            if reponse == wx.ID_NO or reponse == wx.ID_CANCEL:
                dlg.Destroy()
                self.ctrl_objet.SetFocus()
                return
            dlg.Destroy()

        valeur = self.ctrl_cp_depart.GetValue()
        if valeur == "" or valeur == "     ":
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir un code postal pour la ville de départ."), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_cp_depart.SetFocus()
            return
        valeur = self.ctrl_ville_depart.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir un nom de ville de départ."), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_ville_depart.SetFocus()
            return
        valeur = self.ctrl_cp_arrivee.GetValue()
        if valeur == "" or valeur == "     ":
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir un code postal pour la ville d'arrivée."), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_cp_arrivee.SetFocus()
            return
        valeur = self.ctrl_ville_arrivee.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir un nom de ville d'arrivée"), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_ville_arrivee.SetFocus()
            return

        valeur = self.ctrl_distance.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir une distance en Km pour le trajet."), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_distance.SetFocus()
            return
        if self.ValideControleFloat(self.ctrl_distance) is False:
            dlg = wx.MessageDialog(
                self,
                _(u"La distance saisie n'est pas correcte. \nElle doit être sous la forme '32.50' ou '54' par exemple..."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_distance.SetFocus()
            return
        if float(valeur) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"La distance est de 0 Km. \n\nVoulez-vous quand même valider ce déplacement ?\n(Cliquez sur 'Non' ou 'Annuler' pour modifier maintenant la distance)"),
                _(u"Erreur de saisie"),
                wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION,
            )
            reponse = dlg.ShowModal()
            if reponse == wx.ID_NO or reponse == wx.ID_CANCEL:
                dlg.Destroy()
                self.ctrl_distance.SetFocus()
                return
            dlg.Destroy()

        valeur = self.ctrl_tarif.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir la valeur du tarif du Km en euros."), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_tarif.SetFocus()
            return
        if self.ValideControleFloat(self.ctrl_tarif) is False:
            dlg = wx.MessageDialog(
                self,
                _(u"Le tarif n'est pas valide. \nIl doit être sous la forme '0.32' ou '1.53' par exemple..."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_tarif.SetFocus()
            return
        if float(valeur) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Le tarif du Km est de 0 €. \n\nVoulez-vous quand même valider ce déplacement ?\n(Cliquez sur 'Non' ou 'Annuler' pour modifier maintenant ce tarif)"),
                _(u"Erreur de saisie"),
                wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION,
            )
            reponse = dlg.ShowModal()
            if reponse == wx.ID_NO or reponse == wx.ID_CANCEL:
                dlg.Destroy()
                self.ctrl_distance.SetFocus()
                return
            dlg.Destroy()

        self.SauvegardeDeplacement()
        self.SauvegardeDistance()
        self.EndModal(wx.ID_OK)

    def SauvegardeDeplacement(self):
        date = str(self.GetDatePickerValue(self.ctrl_date))
        IDpersonne = self.dictPersonnes[self.ctrl_utilisateur.GetCurrentSelection()]
        objet = self.ctrl_objet.GetValue()
        cp_depart = self.ctrl_cp_depart.GetValue()
        ville_depart = self.ctrl_ville_depart.GetValue()
        cp_arrivee = self.ctrl_cp_arrivee.GetValue()
        ville_arrivee = self.ctrl_ville_arrivee.GetValue()
        distance = float(self.ctrl_distance.GetValue())
        aller_retour = str(self.ctrl_aller_retour.GetValue())
        tarif_km = float(self.ctrl_tarif.GetValue())

        DB = GestionDB.DB()
        listeDonnees = [
            ("date", date),
            ("IDpersonne", IDpersonne),
            ("objet", objet),
            ("cp_depart", cp_depart),
            ("ville_depart", ville_depart),
            ("cp_arrivee", cp_arrivee),
            ("ville_arrivee", ville_arrivee),
            ("distance", distance),
            ("aller_retour", aller_retour),
            ("tarif_km", tarif_km),
        ]
        if self.IDdeplacement is None:
            listeDonnees.append(("IDremboursement", 0))
            ID = DB.ReqInsert("deplacements", listeDonnees)
        else:
            DB.ReqMAJ("deplacements", listeDonnees, "IDdeplacement", self.IDdeplacement)
            ID = self.IDdeplacement
        DB.Commit()
        DB.Close()
        return ID

    def SauvegardeDistance(self):
        depart = (self.ctrl_cp_depart.GetValue(), self.ctrl_ville_depart.GetValue())
        arrivee = (self.ctrl_cp_arrivee.GetValue(), self.ctrl_ville_arrivee.GetValue())
        distanceExiste = False
        distanceID = None
        for IDdistance, cp_depart, ville_depart, cp_arrivee, ville_arrivee, distance in self.listeDistances:
            depart_temp = (str(cp_depart), ville_depart)
            arrivee_temp = (str(cp_arrivee), ville_arrivee)
            if (depart == depart_temp and arrivee == arrivee_temp) or (
                depart == arrivee_temp and arrivee == depart_temp
            ):
                distanceExiste = True
                distanceID = IDdistance
                break

        cp_depart = int(self.ctrl_cp_depart.GetValue())
        ville_depart = self.ctrl_ville_depart.GetValue()
        cp_arrivee = int(self.ctrl_cp_arrivee.GetValue())
        ville_arrivee = self.ctrl_ville_arrivee.GetValue()
        distance = float(self.ctrl_distance.GetValue())
        if self.ctrl_aller_retour.GetValue() is True:
            distance = distance / 2

        DB = GestionDB.DB()
        listeDonnees = [
            ("cp_depart", cp_depart),
            ("ville_depart", ville_depart),
            ("cp_arrivee", cp_arrivee),
            ("ville_arrivee", ville_arrivee),
            ("distance", distance),
        ]
        if distanceExiste is False:
            DB.ReqInsert("distances", listeDonnees)
        else:
            DB.ReqMAJ("distances", listeDonnees, "IDdistance", distanceID)
        DB.Commit()
        DB.Close()


class AdvancedComboBox(wx.ComboBox):
    """ComboBox avec auto-complétion limitée à la liste donnée."""

    def __init__(self, parent, value, choices=None, style=0, **par):
        if choices is None:
            choices = []
        wx.ComboBox.__init__(
            self,
            parent,
            wx.ID_ANY,
            value,
            style=style | wx.CB_DROPDOWN,
            choices=choices,
            **par
        )
        self.parent = parent
        self.choices = choices
        self.Bind(wx.EVT_TEXT, self.EvtText)
        self.Bind(wx.EVT_CHAR, self.EvtChar)
        self.Bind(wx.EVT_COMBOBOX, self.EvtCombobox)
        self.Bind(wx.EVT_KILL_FOCUS, self.EvtKillFocus)
        self.ignoreEvtText = False

    def EvtCombobox(self, event):
        self.ignoreEvtText = True
        event.Skip()

    def EvtChar(self, event):
        if event.GetKeyCode() == 8 and self.GetValue() != u"":
            self.ignoreEvtText = True
        event.Skip()

    def EvtText(self, event):
        if self.ignoreEvtText:
            self.ignoreEvtText = False
            return
        currentText = event.GetString()
        found = False
        for choice in self.choices:
            if choice.startswith(currentText):
                self.SetValue(choice)
                self.SetInsertionPoint(len(currentText))
                self.SetMark(len(currentText), len(choice))
                found = True
                break
        if not found and currentText != "":
            ancienTexte = currentText[:-1]
            if len(ancienTexte) == 0:
                self.SetValue("")
            else:
                for choice in self.choices:
                    if choice.startswith(ancienTexte):
                        self.SetValue(choice)
                        self.SetInsertionPoint(len(ancienTexte))
                        self.SetMark(len(ancienTexte), len(choice))
                        break
            event.Skip()

    def EvtKillFocus(self, event):
        if self.GetValue() not in self.choices and self.GetValue() != u"":
            self.Undo()
        if self.GetValue() in self.choices:
            self.SetStringSelection(self.GetValue())
        event.Skip()


class TextCtrlCp(masked.TextCtrl):
    def __init__(self, parent, id=-1, value=None, ctrlVille=None, listeVilles=None, **par):
        masked.TextCtrl.__init__(self, parent, id, value, **par)
        self.parent = parent
        self.dialog = _dialog_parent(parent)
        self.ctrlVille = ctrlVille
        self.listeVilles = listeVilles
        self.autoComplete = True
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def OnKillFocus(self, event):
        if self.autoComplete is False:
            return
        textCode = self.GetValue()
        villeSelect = self.ctrlVille.GetValue()
        if villeSelect != '':
            for ville, cp in self.listeVilles:
                if ville == villeSelect and cp == textCode:
                    return

        reponses = [ville for ville, cp in self.listeVilles if cp == textCode]
        if len(reponses) == 0:
            if textCode.strip() != '':
                dlg = wx.MessageDialog(
                    self,
                    _(u"Ce code postal n'est pas répertorié dans la base de données. \nVérifiez que vous n'avez pas fait d'erreur de saisie."),
                    "Information",
                    wx.OK | wx.ICON_INFORMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
            return

        if len(reponses) == 1:
            resultat = reponses[0]
            self.ctrlVille.SetValue(resultat)
        else:
            resultat = self.ChoixVilles(textCode, reponses)
            if resultat != '':
                self.ctrlVille.SetValue(resultat)

        self.ctrlVille.SetSelection(0, len(resultat))
        if self.dialog is not None:
            self.dialog.MajDistance()
        event.Skip()

    def ChoixVilles(self, cp, listeReponses):
        resultat = ""
        titre = _(u"Sélection d'une ville")
        listeReponses.sort()
        message = str(len(listeReponses)) + _(u" villes possèdent le code postal ") + str(cp) + _(u". Double-cliquez sur\nle nom d'une ville pour la sélectionner :")
        dlg = wx.SingleChoiceDialog(self, message, titre, listeReponses, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            resultat = dlg.GetStringSelection()
        dlg.Destroy()
        return resultat


class TextCtrlVille(wx.TextCtrl):
    def __init__(self, parent, id=-1, value=None, ctrlCp=None, listeVilles=None, listeNomsVilles=None, **par):
        wx.TextCtrl.__init__(self, parent, id, value, **par)
        self.parent = parent
        self.dialog = _dialog_parent(parent)
        self.ctrlCp = ctrlCp
        self.listeVilles = listeVilles
        self.listeNomsVilles = listeNomsVilles
        self.ignoreEvtText = False
        self.autoComplete = True
        self.Bind(wx.EVT_TEXT, self.OnText)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def OnKillFocus(self, event):
        if self.autoComplete is False:
            return
        villeSelect = self.GetValue()
        if villeSelect == '':
            return

        nbreCodes = self.listeNomsVilles.count(villeSelect)
        if nbreCodes > 1:
            listeCodes = [cp for ville, cp in self.listeVilles if villeSelect == ville]
            resultat = self.ChoixCodes(villeSelect, listeCodes)
            if resultat != '':
                self.ctrlCp.SetValue(resultat)

        if nbreCodes == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Cette ville n'est pas répertoriée dans la base de données. \nVérifiez que vous n'avez pas fait d'erreur de saisie."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()

        if self.dialog is not None:
            self.dialog.MajDistance()
        event.Skip()

    def OnChar(self, event):
        if event.GetKeyCode() == 8:
            self.ignoreEvtText = True
        event.Skip()

    def OnText(self, event):
        if self.autoComplete is False:
            return
        if self.ignoreEvtText:
            self.ignoreEvtText = False
            return
        currentText = event.GetString().upper()
        found = False
        for ville, cp in self.listeVilles:
            if ville.startswith(currentText):
                self.ignoreEvtText = True
                self.SetValue(ville)
                self.SetInsertionPoint(len(currentText))
                self.SetSelection(len(currentText), len(ville))
                self.ctrlCp.SetValue(cp)
                found = True
                break
        if self.dialog is not None:
            self.dialog.MajDistance()
        if not found:
            self.ctrlCp.SetValue('')
            event.Skip()

    def ChoixCodes(self, ville, listeReponses):
        resultat = ""
        titre = _(u"Sélection d'une ville")
        listeReponses.sort()
        message = str(len(listeReponses)) + _(u" villes portent le nom ") + str(ville) + _(u". Double-cliquez sur\nle code postal d'une ville pour la sélectionner :")
        dlg = wx.SingleChoiceDialog(self, message, titre, listeReponses, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            resultat = dlg.GetStringSelection()
        dlg.Destroy()
        return resultat


if __name__ == "__main__":
    app = wx.App(0)
    frm = SaisieDeplacement(None, IDdeplacement=None, IDpersonne=None)
    frm.ShowModal()
    app.MainLoop()
