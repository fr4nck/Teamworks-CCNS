#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface, UTILS_Styles
import wx
from Ctrl import CTRL_Bouton_image, CTRL_Texte
import GestionDB
from Utils.UTILS_Coordonnees import normaliser_email, normaliser_telephone, normaliser_texte


class Dialog(wx.Dialog):
    def __init__(self, parent, ID=-1, title=_(u"Coordonnées"), size=(280, 290), IDcoord=0, IDpersonne=0):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.IDcoord = IDcoord
        self.SetTitle(title)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        parent_name = self.parent.GetName() if self.parent is not None else ""
        if parent_name == "panel_candidat":
            self.nomTable = "coords_candidats"
        else:
            self.nomTable = "coordonnees"

        self.panel_frame = wx.Panel(self, -1)
        self.panel_frame.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.categorieSelect = ""

        self.titre_categories = CTRL_Texte.H2(self.panel_frame, _(u"1. Sélectionnez une catégorie"))
        self.bouton_fixe = wx.ToggleButton(self.panel_frame, -1, _(u"Fixe"))
        self.bouton_mobile = wx.ToggleButton(self.panel_frame, -1, _(u"Mobile"))
        self.bouton_fax = wx.ToggleButton(self.panel_frame, -1, _(u"Fax"))
        self.bouton_email = wx.ToggleButton(self.panel_frame, -1, _(u"Email"))
        self._category_buttons = {
            "Fixe": self.bouton_fixe,
            "Mobile": self.bouton_mobile,
            "Fax": self.bouton_fax,
            "Email": self.bouton_email,
        }
        hauteur_action = UTILS_Styles.GetControlMetric("button_min_height")
        largeur_action = UTILS_Styles.Scale(104)
        for button in self._category_buttons.values():
            button.SetMinSize((largeur_action, hauteur_action))
            button.SetFont(UTILS_Styles.GetFont("label"))

        self.titre_infos = CTRL_Texte.H2(self.panel_frame, _(u"2. Saisissez les informations"))
        self.label_info_mail = CTRL_Texte.Label(self.panel_frame, _(u"Email"))
        self.text_info_mail = wx.TextCtrl(self.panel_frame, -1, "")
        self.label_info_tel = CTRL_Texte.Label(self.panel_frame, _(u"N° Fixe"))
        self.text_info_tel = wx.TextCtrl(self.panel_frame, -1, "", style=wx.TE_CENTRE)
        self.label_info_mail.Hide()
        self.text_info_mail.Hide()

        self.label_intitule = CTRL_Texte.Label(self.panel_frame, _(u"Intitulé"))
        self.text_intitule = wx.TextCtrl(self.panel_frame, -1, "")

        self.bouton_Ok = CTRL_Bouton_image.CTRL(
            self.panel_frame,
            id=wx.ID_OK,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_Annuler = CTRL_Bouton_image.CTRL(
            self.panel_frame,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )

        self.__set_properties()
        self.__do_layout()

        # wx.ToggleButton émet EVT_TOGGLEBUTTON (et non EVT_BUTTON sous Phoenix).
        # Avec EVT_BUTTON les boutons semblaient cliquables mais la catégorie
        # n'était jamais sélectionnée : les champs restaient donc désactivés.
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_Fixe, self.bouton_fixe)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_Mobile, self.bouton_mobile)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_Fax, self.bouton_fax)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnBouton_Email, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBouton_Ok, self.bouton_Ok)
        self.Bind(wx.EVT_BUTTON, self.OnBouton_Annuler, self.bouton_Annuler)

        if self.IDcoord != 0:
            self.Importation()
        else:
            self.ActivationChamps(False)
            # Premier contrôle logique pour une saisie clavier immédiate.
            self.bouton_fixe.SetFocus()
        self._update_category_buttons()

    def __set_properties(self):
        self.bouton_Ok.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour valider")))
        self.bouton_Annuler.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour annuler")))
        self.text_info_tel.SetToolTip(wx.ToolTip(_(u"Saisissez ici un numéro de téléphone")))
        self.text_info_mail.SetToolTip(wx.ToolTip(_(u"Saisissez ici une adresse Mail valide")))
        self.text_intitule.SetToolTip(wx.ToolTip(_(u"Vous pouvez, si vous le souhaitez, saisir ici un intitulé. Ex : 'Contact à Rennes' ou 'Domicile des parents'...")))
        UTILS_Styles.ApplyWindowProfile(self, "compact")

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")
        control_gap = UTILS_Styles.GetLayoutSpacing("control_gap")

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.titre_categories, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)

        sizer_categories = wx.WrapSizer(wx.HORIZONTAL)
        for button in (self.bouton_fixe, self.bouton_mobile, self.bouton_fax, self.bouton_email):
            sizer_categories.Add(button, 0, wx.RIGHT | wx.BOTTOM, toolbar_gap)
        sizer_base.Add(sizer_categories, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)

        sizer_base.Add(self.titre_infos, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, section_gap)
        self.sizer_infos = wx.BoxSizer(wx.VERTICAL)
        self.sizer_infos.Add(self.label_info_mail, 0, wx.BOTTOM, control_gap)
        self.sizer_infos.Add(self.text_info_mail, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        self.sizer_infos.Add(self.label_info_tel, 0, wx.BOTTOM, control_gap)
        self.sizer_infos.Add(self.text_info_tel, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        self.sizer_infos.Add(self.label_intitule, 0, wx.BOTTOM, control_gap)
        self.sizer_infos.Add(self.text_intitule, 0, wx.EXPAND)
        sizer_base.Add(self.sizer_infos, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)

        sizer_boutons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_boutons.AddStretchSpacer(1)
        sizer_boutons.Add(self.bouton_Ok, 0, wx.RIGHT, toolbar_gap)
        sizer_boutons.Add(self.bouton_Annuler, 0)
        sizer_base.Add(sizer_boutons, 0, wx.EXPAND | wx.ALL, padding)

        self.panel_frame.SetSizer(sizer_base)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self.panel_frame, 1, wx.EXPAND)
        self.SetSizer(outer)
        self.Layout()

    def _update_category_buttons(self):
        for categorie, button in self._category_buttons.items():
            selected = categorie == self.categorieSelect
            button.SetValue(selected)
            if selected:
                button.SetBackgroundColour(UTILS_Interface.GetToken("primary_container"))
                button.SetForegroundColour(UTILS_Interface.GetToken("on_primary_container"))
            else:
                button.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_low"))
                button.SetForegroundColour(UTILS_Interface.GetToken("on_surface"))
            button.Refresh()

    def _select_category(self, categorie, label, email=False):
        self.categorieSelect = categorie
        self.ActivationChamps(True)
        self.label_info_tel.SetLabel(label)
        self.label_info_mail.Show(email)
        self.text_info_mail.Show(email)
        self.label_info_tel.Show(not email)
        self.text_info_tel.Show(not email)
        self._update_category_buttons()
        self.sizer_infos.Layout()
        self.panel_frame.Layout()
        if email:
            self.text_info_mail.SetFocus()
        else:
            self.text_info_tel.SetFocus()

    def OnBouton_Fixe(self, event):
        self._select_category("Fixe", _(u"N° Fixe"))

    def OnBouton_Mobile(self, event):
        self._select_category("Mobile", _(u"N° Mobile"))

    def OnBouton_Fax(self, event):
        self._select_category("Fax", _(u"N° Fax"))

    def OnBouton_Email(self, event):
        self._select_category("Email", _(u"Email"), email=True)

    def ActivationChamps(self, etat=False):
        self.label_info_tel.Enable(etat)
        self.text_info_tel.Enable(etat)
        self.label_info_mail.Enable(etat)
        self.text_info_mail.Enable(etat)
        self.label_intitule.Enable(etat)
        self.text_intitule.Enable(etat)

    def OnBouton_Annuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBouton_Ok(self, event):
        if self.categorieSelect == "":
            wx.MessageBox(_(u"Vous devez commencer par sélectionner une catégorie."), "Erreur de saisie")
            return

        if self.categorieSelect == "Email":
            try:
                text = normaliser_email(self.text_info_mail.GetValue())
            except ValueError:
                text = ""
            if text == "":
                wx.MessageBox(_(u"L'adresse Email que vous avez saisie n'est pas valide."), "Erreur de saisie")
                self.text_info_mail.SetFocus()
                return
            self.text_info_mail.SetValue(text)
        else:
            try:
                text = normaliser_telephone(self.text_info_tel.GetValue())
            except ValueError:
                text = ""
            if text == "":
                wx.MessageBox(_(u"Le numéro de téléphone ne semble pas valide."), "Erreur de saisie")
                self.text_info_tel.SetFocus()
                return
            self.text_info_tel.SetValue(text)

        self.Sauvegarde()

        if self.parent is not None and self.parent.GetName() == "panel_candidat":
            self.parent.ctrl_coords.Remplissage()
        if self.parent is not None and self.parent.GetName() == "panel_generalites":
            self.parent.list_ctrl_coords.Remplissage()
            self.parent.MAJ_barre_problemes()

        self.EndModal(wx.ID_OK)

    def Sauvegarde(self):
        varIDpersonne = self.IDpersonne
        varCategorie = self.categorieSelect
        if varCategorie == "Email":
            varTexte = normaliser_email(self.text_info_mail.GetValue())
        else:
            varTexte = normaliser_telephone(self.text_info_tel.GetValue())
        varDIntitule = normaliser_texte(self.text_intitule.GetValue())

        if self.nomTable == "coordonnees":
            texte = "IDpersonne"
        else:
            texte = "IDcandidat"
        listeDonnees = [
            (texte, varIDpersonne),
            ("categorie", varCategorie),
            ("texte", varTexte),
            ("intitule", varDIntitule),
        ]

        DB = GestionDB.DB()
        if self.IDcoord == 0:
            DB.ReqInsert(self.nomTable, listeDonnees)
        else:
            DB.ReqMAJ(self.nomTable, listeDonnees, "IDcoord", self.IDcoord)
        DB.Close()

    def Importation(self):
        DB = GestionDB.DB()
        req = "SELECT * FROM %s WHERE IDcoord = %d" % (self.nomTable, self.IDcoord)
        DB.ExecuterReq(req)
        resultats = DB.ResultatReq()
        DB.Close()
        if not resultats:
            wx.MessageBox(
                _(u"Cette coordonnée n'existe plus dans la base de données."),
                _(u"Coordonnée introuvable"),
                wx.OK | wx.ICON_ERROR,
            )
            wx.CallAfter(self.EndModal, wx.ID_CANCEL)
            return
        donnees = resultats[0]

        self.categorieSelect = donnees[2]
        self.text_intitule.SetValue(donnees[4] or "")

        if self.categorieSelect == "Fixe":
            self.OnBouton_Fixe(None)
            self.text_info_tel.SetValue(donnees[3] or "")
        if self.categorieSelect == "Mobile":
            self.OnBouton_Mobile(None)
            self.text_info_tel.SetValue(donnees[3] or "")
        if self.categorieSelect == "Fax":
            self.OnBouton_Fax(None)
            self.text_info_tel.SetValue(donnees[3] or "")
        if self.categorieSelect == "Email":
            self.OnBouton_Email(None)
            self.text_info_mail.SetValue(donnees[3] or "")


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, -1, _(u"Coordonnées"))
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
