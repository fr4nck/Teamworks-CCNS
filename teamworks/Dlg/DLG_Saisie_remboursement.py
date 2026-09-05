#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import sys
import Chemins
from Utils.UTILS_Traduction import _
import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Utils import UTILS_Interface
from Utils import UTILS_Styles
import FonctionsPerso
import GestionDB
import datetime

if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else:
    from wx import DatePickerCtrl, DP_DROPDOWN


_PHOENIX = 'phoenix' in wx.PlatformInfo
_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin


class SaisieRemboursement(wx.Dialog):
    """Saisie d'un remboursement pour les frais de déplacement."""

    def __init__(self, parent, id=-1, title=_(u"Saisie d'un remboursement"), IDremboursement=None, IDpersonne=None):
        wx.Dialog.__init__(
            self,
            parent,
            id,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.IDremboursement = IDremboursement
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        # Caractéristiques
        self.section_generalites = CTRL_Section.Section(
            self,
            titre=_(u"Caractéristiques"),
            niveau=2,
        )
        panel_generalites = self.section_generalites.GetContentPanel()
        self.label_date = CTRL_Texte.Label(panel_generalites, _(u"Date"))
        self.ctrl_date = DatePickerCtrl(panel_generalites, -1, style=DP_DROPDOWN)
        self.label_montant = CTRL_Texte.Label(panel_generalites, _(u"Montant"))
        self.ctrl_montant = wx.TextCtrl(panel_generalites, -1, u"")
        self.label_euro_montant = CTRL_Texte.Body(panel_generalites, u"€")
        self.label_utilisateur = CTRL_Texte.Label(panel_generalites, _(u"Utilisateur"))
        self.ImportationPersonnes()
        self.ctrl_utilisateur = AdvancedComboBox(
            panel_generalites,
            "",
            choices=self.listePersonnes,
        )

        # Déplacements rattachés
        self.section_deplacements = CTRL_Section.Section(
            self,
            titre=_(u"Déplacements rattachés"),
            niveau=2,
        )
        panel_deplacements = self.section_deplacements.GetContentPanel()
        self.label_rattachement = CTRL_Texte.BodySecondary(panel_deplacements, u"")
        self.ctrl_deplacements = ListCtrl_deplacements(
            panel_deplacements,
            IDremboursement=IDremboursement,
            IDpersonne=self.IDpersonne,
        )
        self.ctrl_deplacements.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )

        # Actions
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
        if self.IDremboursement is not None:
            self.SetTitle(_(u"Modification d'un remboursement"))
            self.Importation()
        if self.IDpersonne is not None:
            self.label_utilisateur.Hide()
            self.ctrl_utilisateur.Hide()

        self.__set_properties()
        self.__do_layout(panel_generalites, panel_deplacements)

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.ctrl_montant.Bind(wx.EVT_KILL_FOCUS, self.montant_EvtKillFocus)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Valider le remboursement")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Annuler la saisie")))
        self.ctrl_date.SetToolTip(wx.ToolTip(_(u"Sélectionnez ici la date du remboursement")))
        self.ctrl_utilisateur.SetToolTip(wx.ToolTip(_(u"Sélectionnez ici l'utilisateur pour ce remboursement")))
        self.ctrl_montant.SetToolTip(wx.ToolTip(_(u"Saisissez le montant du remboursement en euros")))
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def __do_layout(self, panel_generalites, panel_deplacements):
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        generalites = wx.BoxSizer(wx.VERTICAL)

        ligne_date = wx.BoxSizer(wx.HORIZONTAL)
        ligne_date.Add(self.label_date, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_date.Add(self.ctrl_date, 0, wx.RIGHT, section_gap)
        ligne_date.Add(self.label_montant, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, field_gap)
        ligne_date.Add(self.ctrl_montant, 1, wx.RIGHT, field_gap)
        ligne_date.Add(self.label_euro_montant, 0, wx.ALIGN_CENTER_VERTICAL)
        generalites.Add(ligne_date, 0, wx.EXPAND | wx.BOTTOM, field_gap)

        ligne_utilisateur = wx.BoxSizer(wx.HORIZONTAL)
        ligne_utilisateur.Add(
            self.label_utilisateur,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            field_gap,
        )
        ligne_utilisateur.Add(self.ctrl_utilisateur, 1, wx.EXPAND)
        generalites.Add(ligne_utilisateur, 0, wx.EXPAND)
        panel_generalites.SetSizer(generalites)

        deplacements = wx.BoxSizer(wx.VERTICAL)
        deplacements.Add(self.label_rattachement, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        deplacements.Add(self.ctrl_deplacements, 1, wx.EXPAND)
        panel_deplacements.SetSizer(deplacements)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, toolbar_gap)
        actions.Add(self.bouton_annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.section_generalites, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, page_gap)
        sizer.Add(self.section_deplacements, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, section_gap)
        sizer.Add(actions, 0, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)
        self.Layout()

    def ImportationPersonnes(self):
        DB = GestionDB.DB()
        req = "SELECT IDpersonne, nom, prenom FROM personnes ORDER BY nom, prenom;"
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        self.listePersonnes = []
        self.dictPersonnes = {}
        for index, (IDpersonne, nom, prenom) in enumerate(listeDonnees):
            self.listePersonnes.append(nom + " " + prenom)
            self.dictPersonnes[index] = IDpersonne

    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT IDremboursement, IDpersonne, date, montant
        FROM remboursements WHERE IDremboursement=%d;""" % self.IDremboursement
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return

        self.IDpersonne = listeDonnees[0][1]
        self.SetPersonne(self.IDpersonne)
        date = listeDonnees[0][2]
        self.SetDate(
            datetime.date(
                year=int(date[:4]),
                month=int(date[5:7]),
                day=int(date[8:10]),
            )
        )
        self.ctrl_montant.SetValue(str(listeDonnees[0][3]))
        self.MajIDpersonne()
        self.MajLabelRattachement(float(self.ctrl_montant.GetValue()))

    # Méthodes historiques conservées pour compatibilité d'API.
    def SetRemboursement(self, IDremboursement=None):
        if IDremboursement is None or IDremboursement == 0 or IDremboursement == "":
            if hasattr(self, "ctrl_remboursement"):
                self.ctrl_remboursement.SetLabel("Aucun remboursement.")
            return
        DB = GestionDB.DB()
        req = "SELECT date FROM remboursements WHERE IDremboursement=%d;" % IDremboursement
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if hasattr(self, "ctrl_remboursement") and listeDonnees:
            dateRemboursement = self.DateEngFr(listeDonnees[0][0])
            self.ctrl_remboursement.SetLabel("N°" + str(IDremboursement) + " du " + dateRemboursement)

    def DateEngFr(self, textDate):
        return str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])

    def SetAllerRetour(self, etat=False):
        if not hasattr(self, "ctrl_aller_retour"):
            return
        self.ctrl_aller_retour.SetValue(etat)
        self.label_km.SetLabel("Km  (Aller/retour)" if etat else "Km  (Aller simple)")

    def CalcMontantRmbst(self):
        if not hasattr(self, "ctrl_distance") or not hasattr(self, "ctrl_tarif"):
            return
        if self.ValideControleFloat(self.ctrl_distance) is False:
            return
        if self.ValideControleFloat(self.ctrl_tarif) is False:
            return
        distance = float(self.ctrl_distance.GetValue())
        tarif = float(self.ctrl_tarif.GetValue())
        self.ctrl_montant.SetValue(u"%.2f" % (distance * tarif))

    def montant_EvtKillFocus(self, event):
        if self.ValideControleFloat(self.ctrl_montant) is False:
            dlg = wx.MessageDialog(
                self,
                _(u"Le montant n'est pas valide. \nIl doit être sous la forme '1.32' ou '100.50' par exemple..."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_deplacements.Enable(False)
            self.ctrl_montant.SetFocus()
            return
        if self.ctrl_utilisateur.GetCurrentSelection() != -1:
            self.MajLabelRattachement(float(self.ctrl_montant.GetValue()))
        event.Skip()

    def MajIDpersonne(self):
        self.IDpersonne = self.GetPersonne()
        self.ctrl_deplacements.IDpersonne = self.IDpersonne
        self.ctrl_deplacements.MAJListeCtrl()

    def MajLabelRattachement(self, montant=None):
        if montant is not None:
            self.ctrl_deplacements.montantRemboursement = montant
        self.ctrl_deplacements.MajLabelRattachement()

    def ValideControleFloat(self, controle=None):
        valeur = controle.GetValue()
        if valeur == "":
            return True
        if any(lettre not in "0123456789." for lettre in valeur):
            return False
        try:
            float(valeur)
        except Exception:
            return False
        return True

    def MajDistance(self):
        if not all(hasattr(self, nom) for nom in ("ctrl_cp_depart", "ctrl_ville_depart", "ctrl_cp_arrivee", "ctrl_ville_arrivee", "listeDistances")):
            return
        depart = (self.ctrl_cp_depart.GetValue(), self.ctrl_ville_depart.GetValue())
        arrivee = (self.ctrl_cp_arrivee.GetValue(), self.ctrl_ville_arrivee.GetValue())
        for IDdistance, cp_depart, ville_depart, cp_arrivee, ville_arrivee, distance in self.listeDistances:
            depart_temp = (str(cp_depart), ville_depart)
            arrivee_temp = (str(cp_arrivee), ville_arrivee)
            if (depart == depart_temp and arrivee == arrivee_temp) or (depart == arrivee_temp and arrivee == depart_temp):
                if self.ctrl_aller_retour.GetValue() is True:
                    self.ctrl_distance.SetValue(str(distance * 2))
                else:
                    self.ctrl_distance.SetValue(str(distance))
                break

    def GetPersonne(self):
        index = self.ctrl_utilisateur.GetCurrentSelection()
        if index == -1:
            return None
        return self.dictPersonnes[index]

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
        UTILS_Aide.Aide("Enregistrerunremboursement")

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

        valeur = self.ctrl_montant.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez obligatoirement saisir un montant en euros pour ce remboursement."),
                "Erreur",
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_montant.SetFocus()
            return
        if self.ValideControleFloat(self.ctrl_montant) is False:
            dlg = wx.MessageDialog(
                self,
                _(u"Le montant saisi n'est pas valide \nIl doit être sous la forme '32.50' ou '54' par exemple..."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_montant.SetFocus()
            return
        if float(valeur) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Le montant que vous avez saisi est de 0 €\n\nSouhaitez-vous conserver ce montant ?\n(Cliquez sur 'Non' ou 'Annuler' pour modifier maintenant le montant)"),
                _(u"Erreur de saisie"),
                wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION,
            )
            reponse = dlg.ShowModal()
            if reponse == wx.ID_NO or reponse == wx.ID_CANCEL:
                dlg.Destroy()
                self.ctrl_montant.SetFocus()
                return
            dlg.Destroy()

        listeIDcoches, listeIDdecoches = self.ctrl_deplacements.ListeItemsCoches()
        if len(listeIDcoches) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous n'avez coché aucun déplacement dans la liste.\n\nSouhaitez-vous quand même valider ?\n(Cliquez sur 'Non' ou 'Annuler' pour cocher maintenant des déplacements)"),
                _(u"Erreur de saisie"),
                wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION,
            )
            reponse = dlg.ShowModal()
            if reponse == wx.ID_NO or reponse == wx.ID_CANCEL:
                dlg.Destroy()
                return
            dlg.Destroy()

        self.Sauvegarde()
        self.EndModal(wx.ID_OK)

    def Sauvegarde(self):
        date = str(self.GetDatePickerValue(self.ctrl_date))
        IDpersonne = self.dictPersonnes[self.ctrl_utilisateur.GetCurrentSelection()]
        montant = float(self.ctrl_montant.GetValue())
        listeIDcoches, listeIDdecoches = self.ctrl_deplacements.ListeItemsCoches()
        texteID = "-".join(str(ID) for ID in listeIDcoches)

        DB = GestionDB.DB()
        try:
            listeDonnees = [
                ("date", date),
                ("IDpersonne", IDpersonne),
                ("montant", montant),
                ("listeIDdeplacement", texteID),
            ]
            if self.IDremboursement is None:
                ID = DB.ReqInsert("remboursements", listeDonnees, commit=False)
            else:
                DB.ReqMAJ(
                    "remboursements",
                    listeDonnees,
                    "IDremboursement",
                    self.IDremboursement,
                    commit=False,
                )
                ID = self.IDremboursement

            for IDdeplacement in listeIDcoches:
                DB.ReqMAJ(
                    "deplacements",
                    [("IDremboursement", ID)],
                    "IDdeplacement",
                    IDdeplacement,
                    commit=False,
                )
            for IDdeplacement in listeIDdecoches:
                DB.ReqMAJ(
                    "deplacements",
                    [("IDremboursement", 0)],
                    "IDdeplacement",
                    IDdeplacement,
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
        return ID


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
        self.parent = parent.GetParent().GetParent() if parent.GetParent() is not None else parent
        # Le dialogue reste l'autorité métier ; retrouver proprement le parent
        # même lorsque le champ vit dans une section sémantique.
        while self.parent is not None and not isinstance(self.parent, SaisieRemboursement):
            self.parent = self.parent.GetParent()
        self.choices = choices
        self.Bind(wx.EVT_TEXT, self.EvtText)
        self.Bind(wx.EVT_CHAR, self.EvtChar)
        self.Bind(wx.EVT_COMBOBOX, self.EvtCombobox)
        self.Bind(wx.EVT_KILL_FOCUS, self.EvtKillFocus)
        self.ignoreEvtText = False

    def EvtCombobox(self, event):
        self.ignoreEvtText = True
        if self.parent is not None:
            self.parent.MajIDpersonne()
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
        if self.parent is not None:
            self.parent.MajIDpersonne()
        event.Skip()

    def EvtKillFocus(self, event):
        if self.GetValue() not in self.choices and self.GetValue() != u"":
            self.Undo()
        if self.GetValue() in self.choices:
            self.SetStringSelection(self.GetValue())
        if self.parent is not None:
            self.parent.MajIDpersonne()
        event.Skip()


class ListCtrl_deplacements(wx.ListCtrl, _CheckboxFallback):
    def __init__(self, parent, size=(-1, -1), IDremboursement=None, IDpersonne=None):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES | wx.BORDER_NONE,
        )
        if _PHOENIX:
            self.EnableCheckBoxes(True)
        else:
            CheckListCtrlMixin.__init__(self)
        self.parent = parent
        self.dialog = parent
        while self.dialog is not None and not isinstance(self.dialog, SaisieRemboursement):
            self.dialog = self.dialog.GetParent()
        self.IDpersonne = IDpersonne
        self.IDremboursement = IDremboursement
        self.montantRemboursement = 0
        self._ajustement_en_cours = False
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))

        self.MAJListeCtrl()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        if _PHOENIX:
            if hasattr(wx, "EVT_LIST_ITEM_CHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnNativeCheckItem)
            if hasattr(wx, "EVT_LIST_ITEM_UNCHECKED"):
                self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnNativeCheckItem)

    def _label_rattachement(self):
        return self.dialog.label_rattachement if self.dialog is not None else None

    def _is_checked(self, index):
        if _PHOENIX:
            return self.IsItemChecked(index)
        return self.IsChecked(index)

    def _set_checked(self, index, etat=True):
        self.CheckItem(index, etat)

    def OnSize(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        if self._ajustement_en_cours or self.GetColumnCount() < 7:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return
        gap = UTILS_Styles.GetSpacing("sm")
        fixes = [
            UTILS_Styles.Scale(65),
            UTILS_Styles.Scale(100),
            None,
            None,
            UTILS_Styles.Scale(100),
            UTILS_Styles.Scale(105),
            UTILS_Styles.Scale(110),
        ]
        disponible = max(
            UTILS_Styles.Scale(360),
            largeur - sum(valeur or 0 for valeur in fixes) - 2 * gap,
        )
        fixes[2] = max(UTILS_Styles.Scale(140), int(disponible * 0.42))
        fixes[3] = max(UTILS_Styles.Scale(180), disponible - fixes[2])

        self._ajustement_en_cours = True
        try:
            for index, taille in enumerate(fixes):
                self.SetColumnWidth(index, taille)
        finally:
            self._ajustement_en_cours = False

    def Remplissage(self):
        self.Importation()
        self.InsertColumn(0, u"N°")
        self.InsertColumn(1, _(u"Date"))
        self.InsertColumn(2, _(u"Objet"))
        self.InsertColumn(3, _(u"Trajet"))
        self.InsertColumn(4, _(u"Distance"), wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(5, _(u"Tarif"), wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(6, _(u"Montant"), wx.LIST_FORMAT_RIGHT)

        self.remplissage = True
        for IDdeplacement, date, objet, trajet, dist, tarif_km, montant, remboursement in self.donnees:
            index = self.InsertItem(self.GetItemCount(), str(IDdeplacement))
            self.SetItem(index, 1, date)
            self.SetItem(index, 2, objet)
            self.SetItem(index, 3, trajet)
            self.SetItem(index, 4, dist)
            self.SetItem(index, 5, tarif_km)
            self.SetItem(index, 6, montant)
            self.SetItemData(index, IDdeplacement)
            if remboursement != 0:
                self._set_checked(index, True)
        self.remplissage = False
        wx.CallAfter(self.AjusterColonnes)

    def MAJListeCtrl(self):
        self.ClearAll()
        label = self._label_rattachement()
        if self.IDpersonne is None:
            self.Enable(False)
            if label is not None:
                label.SetLabel(_(u"Veuillez sélectionner un utilisateur dans la liste proposée."))
                label.AppliquerStyle("body-secondary")
            return
        self.Enable(True)
        self.Remplissage()
        self.MajLabelRattachement()

    def OnItemActivated(self, evt):
        self._set_checked(evt.Index, not self._is_checked(evt.Index))
        self.MajLabelRattachement()

    def OnCheckItem(self, index, flag):
        if not getattr(self, "remplissage", False):
            self.MajLabelRattachement()

    def OnNativeCheckItem(self, event):
        if not getattr(self, "remplissage", False):
            self.MajLabelRattachement()
        event.Skip()

    def MajLabelRattachement(self):
        label = self._label_rattachement()
        if label is None:
            return
        montantRattache = 0
        for index in range(self.GetItemCount()):
            montant = float(self.GetItem(index, 6).GetText()[:-2])
            if self._is_checked(index):
                montantRattache += montant

        montantNonRattache = self.montantRemboursement - montantRattache
        couleur = "on_surface_variant"
        if len(self.donnees) == 0:
            texte = _(u"Aucun déplacement n'est à rattacher pour cette personne.")
        elif montantNonRattache == 0:
            texte = _(u"Les déplacements cochés correspondent au montant du remboursement.")
            couleur = "success"
        elif montantNonRattache > 0:
            texte = _(u"Vous pouvez encore rattacher pour ") + u"%.2f €" % montantNonRattache + _(u" de déplacements.")
            couleur = "warning"
        else:
            texte = _(u"Attention ! Vous avez rattaché ") + u"%.2f €" % (-montantNonRattache) + _(u" de déplacements en trop !")
            couleur = "danger"
        label.SetLabel(texte)
        label.SetForegroundColour(UTILS_Interface.GetToken(couleur))

    def Importation(self):
        DB = GestionDB.DB()
        if self.IDremboursement is None:
            req = """SELECT IDdeplacement, date, objet, ville_depart, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement
            FROM deplacements WHERE IDpersonne=%d AND COALESCE(IDremboursement, 0)=0 ORDER BY date;""" % self.IDpersonne
        else:
            req = """SELECT IDdeplacement, date, objet, ville_depart, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement
            FROM deplacements WHERE IDpersonne=%d AND COALESCE(IDremboursement, 0) IN (0, %d) ORDER BY date;""" % (
                self.IDpersonne,
                self.IDremboursement,
            )
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        self.nbreLignes = len(listeDonnees)
        self.donnees = []
        self.montantRattache = 0
        self.montantNonRattache = 0

        for IDdeplacement, date, objet, ville_depart, ville_arrivee, distance, aller_retour, tarif_km, IDremboursement in listeDonnees:
            dateTmp = str(date[8:10]) + "/" + str(date[5:7]) + "/" + str(date[0:4])
            trajet = ville_depart + (" <--> " if aller_retour == "True" else " -> ") + ville_arrivee
            dist = str(distance) + _(u" Km")
            montant = float(distance) * float(tarif_km)
            montantStr = u"%.2f €" % montant
            tarif_str = str(tarif_km) + _(u" €/km")
            if IDremboursement not in (None, 0, ""):
                self.montantRattache += montant
            self.donnees.append(
                (
                    IDdeplacement,
                    dateTmp,
                    objet,
                    trajet,
                    dist,
                    tarif_str,
                    montantStr,
                    IDremboursement or 0,
                )
            )

    def ListeItemsCoches(self):
        listeIDcoches = []
        listeIDdecoches = []
        for index in range(self.GetItemCount()):
            ID = int(self.GetItem(index, 0).GetText())
            if self._is_checked(index):
                listeIDcoches.append(ID)
            else:
                listeIDdecoches.append(ID)
        return listeIDcoches, listeIDdecoches


if __name__ == "__main__":
    app = wx.App(0)
    frm = SaisieRemboursement(None, IDremboursement=1, IDpersonne=None)
    frm.ShowModal()
    app.MainLoop()
