#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Saisie et modification d'un entretien Recrutement."""

import datetime
import wx
import wx.lib.masked as masked

import GestionDB
from Ctrl import CTRL_Bouton_image, CTRL_Section, CTRL_Texte
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _

if "phoenix" in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN
else:
    from wx import DatePickerCtrl, DP_DROPDOWN


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


class MyBitmapComboBox(wx.Choice):
    """Compatibilité historique : mêmes choix/index, sans pictogrammes décoratifs."""

    def __init__(self, parent, listeImages=None, size=(-1, -1)):
        if listeImages is None:
            listeImages = []
        choices = [texte for texte, _nomImage in listeImages]
        wx.Choice.__init__(self, parent, -1, choices=choices, size=size)
        if choices:
            self.SetSelection(0)


class Dialog(wx.Dialog):
    def __init__(self, parent, IDentretien=None, IDcandidat=None, IDpersonne=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.IDentretien = IDentretien
        self.IDcandidat = IDcandidat
        self.IDpersonne = IDpersonne

        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.section = CTRL_Section.Section(
            self.panel,
            titre=_(u"Entretien"),
            niveau=2,
            description=_(u"Renseignez la date, l'heure et l'évaluation de l'entretien."),
        )
        contenu = self.section.GetContentPanel()

        self.label_date = CTRL_Texte.Label(contenu, _(u"Date"))
        self.ctrl_date = DatePickerCtrl(contenu, -1, style=DP_DROPDOWN)
        self.label_heure = CTRL_Texte.Label(contenu, _(u"Heure"))
        self.ctrl_heure = masked.TextCtrl(
            contenu,
            -1,
            "",
            style=wx.TE_CENTRE,
            mask="##:##",
            validRegex="[0-2][0-9]:[0-5][0-9]",
        )
        self.ctrl_heure.SetCtrlParameters(
            invalidBackgroundColour=UTILS_Interface.GetToken("danger")
        )
        self.ctrl_heure.SetMinSize(
            (UTILS_Styles.Scale(110), UTILS_Styles.GetControlMetric("input_min_height"))
        )
        self.ctrl_heure.SetFont(UTILS_Styles.GetFont("data-large"))

        self.label_avis = CTRL_Texte.Label(contenu, _(u"Avis"))
        liste_avis = [
            (_(u"Avis inconnu"), ""),
            (_(u"Pas convaincant"), ""),
            (_(u"Mitigé"), ""),
            (_(u"Bien"), ""),
            (_(u"Très bien"), ""),
        ]
        self.ctrl_avis = MyBitmapComboBox(contenu, listeImages=liste_avis)
        self.ctrl_avis.SetMinSize((-1, UTILS_Styles.GetControlMetric("input_min_height")))

        self.label_remarques = CTRL_Texte.Label(contenu, _(u"Commentaire"))
        self.ctrl_remarques = wx.TextCtrl(contenu, -1, "", style=wx.TE_MULTILINE)
        self.ctrl_remarques.SetMinSize((-1, UTILS_Styles.Scale(150)))

        self.bouton_aide = CTRL_Bouton_image.CTRL(self.panel, texte=_(u"Aide"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self.panel, texte=_(u"Valider"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self.panel, texte=_(u"Annuler"))

        self._layout_contenu(contenu)
        self._layout_dialogue()
        self._set_properties()

        if self.IDentretien is not None:
            self.Importation()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def _layout_contenu(self, contenu):
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")

        bloc_date = wx.BoxSizer(wx.VERTICAL)
        bloc_date.Add(self.label_date, 0, wx.EXPAND | wx.BOTTOM, gap)
        bloc_date.Add(self.ctrl_date, 0, wx.EXPAND)

        bloc_heure = wx.BoxSizer(wx.VERTICAL)
        bloc_heure.Add(self.label_heure, 0, wx.EXPAND | wx.BOTTOM, gap)
        bloc_heure.Add(self.ctrl_heure, 0, wx.EXPAND)

        ligne_horaire = wx.BoxSizer(wx.HORIZONTAL)
        ligne_horaire.Add(bloc_date, 2, wx.EXPAND | wx.RIGHT, gap)
        ligne_horaire.Add(bloc_heure, 1, wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(ligne_horaire, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.label_avis, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.ctrl_avis, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.label_remarques, 0, wx.EXPAND)
        sizer.AddSpacer(gap)
        sizer.Add(self.ctrl_remarques, 1, wx.EXPAND)
        contenu.SetSizer(sizer)

    def _layout_dialogue(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("control_gap")

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, gap)
        actions.Add(self.bouton_annuler, 0)

        sizer_panel = wx.BoxSizer(wx.VERTICAL)
        sizer_panel.Add(self.section, 1, wx.EXPAND | wx.ALL, padding)
        sizer_panel.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.panel.SetSizer(sizer_panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "standard")

    def _set_properties(self):
        nom_complet = self.GetNomCandidat(self.IDcandidat, self.IDpersonne)
        action = _(u"Saisie") if self.IDentretien is None else _(u"Modification")
        if nom_complet:
            self.SetTitle(_(u"%s d'un entretien pour %s") % (action, nom_complet))
        else:
            self.SetTitle(_(u"%s d'un entretien") % action)

        self.ctrl_date.SetToolTip(wx.ToolTip(_(u"Saisissez la date de l'entretien")))
        self.ctrl_heure.SetToolTip(wx.ToolTip(_(u"Saisissez l'heure de l'entretien")))
        self.ctrl_avis.SetToolTip(wx.ToolTip(_(u"Sélectionnez une appréciation de l'entretien")))
        self.ctrl_remarques.SetToolTip(wx.ToolTip(_(u"Saisissez l'avis complet émis après l'entretien")))

    def OnContextMenu(self, event):
        pass

    def SetDatePicker(self, controle, date):
        valeur = wx.DateTime()
        valeur.Set(int(date.day), int(date.month) - 1, int(date.year))
        controle.SetValue(valeur)

    def GetDatePickerValue(self, controle):
        valeur = controle.GetValue()
        return datetime.date(valeur.GetYear(), valeur.GetMonth() + 1, valeur.GetDay())

    def Importation(self):
        DB = GestionDB.DB()
        req = (
            "SELECT IDentretien, IDcandidat, IDpersonne, date, heure, avis, remarques "
            "FROM entretiens WHERE IDentretien=%d" % self.IDentretien
        )
        DB.ExecuterReq(req)
        resultats = DB.ResultatReq()
        DB.Close()
        if not resultats:
            return

        _IDentretien, _IDcandidat, _IDpersonne, date, heure, avis, remarques = resultats[0]
        self.SetDatePicker(
            self.ctrl_date,
            datetime.date(year=int(date[:4]), month=int(date[5:7]), day=int(date[8:10])),
        )
        self.ctrl_heure.SetValue(heure)
        self.ctrl_avis.SetSelection(avis)
        self.ctrl_remarques.SetValue(remarques or "")

    def Sauvegarde(self):
        date = self.GetDatePickerValue(self.ctrl_date)
        heure = self.ctrl_heure.GetValue()
        avis = self.ctrl_avis.GetSelection()
        remarques = self.ctrl_remarques.GetValue()

        DB = GestionDB.DB()
        listeDonnees = [
            ("IDcandidat", self.IDcandidat),
            ("IDpersonne", self.IDpersonne),
            ("date", date),
            ("heure", heure),
            ("avis", avis),
            ("remarques", remarques),
        ]
        if self.IDentretien is None:
            ID = DB.ReqInsert("entretiens", listeDonnees)
        else:
            DB.ReqMAJ("entretiens", listeDonnees, "IDentretien", self.IDentretien)
            ID = self.IDentretien
        DB.Commit()
        DB.Close()
        return ID

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        heure = self.ctrl_heure.GetValue()
        if heure in ("", "  :  "):
            wx.MessageBox(
                _(u"Vous devez obligatoirement saisir une heure"),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            self.ctrl_heure.SetFocus()
            return

        self.Sauvegarde()
        parent = self.GetParent()
        try:
            if parent.GetName() in ("OL_entretiens", "OL_gadget_entretiens"):
                parent.MAJ()
        except Exception:
            pass

        recrutement = _ancestor_named(parent, "Recrutement")
        if recrutement is not None:
            recrutement.gadget_entretiens.MAJ()
            recrutement.gadget_informations.MAJ()

        resume = _ancestor_named(parent, "panel_resume")
        if resume is not None:
            resume.MAJlabelsPages("entretiens")
            if recrutement is not None:
                recrutement.MAJpanel(MAJpanelResume=False)

        self.EndModal(wx.ID_OK)

    def GetNomCandidat(self, IDcandidat=None, IDpersonne=None):
        DB = GestionDB.DB()
        if IDpersonne in (None, 0):
            if IDcandidat in (None, 0):
                DB.Close()
                return ""
            req = "SELECT civilite, nom, prenom FROM candidats WHERE IDcandidat=%d;" % IDcandidat
        else:
            req = "SELECT civilite, nom, prenom FROM personnes WHERE IDpersonne=%d;" % IDpersonne
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if not listeDonnees:
            return ""
        _civilite, nom, prenom = listeDonnees[0]
        return u"%s %s" % (nom or "", prenom or "")


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, IDentretien=None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
