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

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Texte
from Utils import UTILS_Interface
from Utils import UTILS_Styles
import GestionDB
import FonctionsPerso


class Dialog(wx.Dialog):
    def __init__(self, parent, title="", IDpays=0):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.parent = parent
        self.IDpays = IDpays
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.panel_base = wx.Panel(self, -1)
        self.panel_base.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.titre = CTRL_Texte.H2(self.panel_base, _(u"Pays et nationalité"))
        self.label_nom = CTRL_Texte.Label(self.panel_base, _(u"Nom du pays"))
        self.text_nom = wx.TextCtrl(self.panel_base, -1, "")
        self.label_nation = CTRL_Texte.Label(self.panel_base, _(u"Nationalité"))
        self.text_nation = wx.TextCtrl(self.panel_base, -1, "")

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self.panel_base,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self.panel_base,
            id=wx.ID_OK,
            texte=_(u"Valider"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"),
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self.panel_base,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"),
        )

        if IDpays != 0:
            self.Importation()

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.SetTitle(_(u"Gestion des pays"))
        self.text_nom.SetToolTip(wx.ToolTip(_(u"Saisissez ici le nom du pays")))
        self.text_nation.SetToolTip(wx.ToolTip(_(u"Saisissez ici la nationalité du pays")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Annuler la saisie")))
        UTILS_Styles.ApplyWindowProfile(self, "compact")

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        toolbar_gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.titre, 0, wx.EXPAND | wx.BOTTOM, section_gap)
        contenu.Add(self.label_nom, 0, wx.EXPAND | wx.BOTTOM, UTILS_Styles.GetSpacing("xs"))
        contenu.Add(self.text_nom, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        contenu.Add(self.label_nation, 0, wx.EXPAND | wx.BOTTOM, UTILS_Styles.GetSpacing("xs"))
        contenu.Add(self.text_nation, 0, wx.EXPAND)

        boutons = wx.BoxSizer(wx.HORIZONTAL)
        boutons.Add(self.bouton_aide, 0)
        boutons.AddStretchSpacer(1)
        boutons.Add(self.bouton_ok, 0, wx.RIGHT, toolbar_gap)
        boutons.Add(self.bouton_annuler, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(contenu, 1, wx.EXPAND | wx.ALL, padding)
        sizer.Add(boutons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.panel_base.SetSizer(sizer)

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(self.panel_base, 1, wx.EXPAND)
        self.SetSizer(shell)
        self.Layout()

    def Importation(self):
        DB = GestionDB.DB()
        req = "SELECT nom, nationalite FROM pays WHERE IDpays=%d" % self.IDpays
        DB.ExecuterReq(req)
        resultats = DB.ResultatReq()
        DB.Close()
        if not resultats:
            return
        donnees = resultats[0]
        self.text_nom.SetValue(donnees[0])
        self.text_nation.SetValue(donnees[1])

    def Sauvegarde(self):
        varNom = self.text_nom.GetValue()
        varNation = self.text_nation.GetValue()

        DB = GestionDB.DB()
        if self.IDpays == 0:
            listeDonnees = [
                ("code_drapeau", "autre"),
                ("nom", varNom),
                ("nationalite", varNation),
            ]
            ID = DB.ReqInsert("pays", listeDonnees)
        else:
            listeDonnees = [
                ("nom", varNom),
                ("nationalite", varNation),
            ]
            DB.ReqMAJ("pays", listeDonnees, "IDpays", self.IDpays)
            ID = self.IDpays
        DB.Commit()
        DB.Close()
        return ID

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lespaysetnationalits")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        valeur = self.text_nom.GetValue()
        if valeur == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez saisir au moins un nom de pays !"),
                "Erreur",
                wx.OK,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.text_nom.SetFocus()
            return

        self.Sauvegarde()
        if FonctionsPerso.FrameOuverte("panel_config_pays") is not None:
            self.GetParent().MAJ_ListCtrl()
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, "", IDpays=0)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
