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
import GestionDB
import FonctionsPerso

from Ctrl.CTRL_Creation_modele_contrat_p1 import Page as Page1
from Ctrl.CTRL_Creation_modele_contrat_p2 import Page as Page2
from Ctrl.CTRL_Creation_modele_contrat_p3 import Page as Page3


class Dialog(wx.Dialog):
    def __init__(self, parent, title="", IDmodele=0):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.listePages = ("Page1", "Page2", "Page3")
        self.panel_base = wx.Panel(self, -1)
        self.static_line = wx.StaticLine(self.panel_base, -1)
        self.bouton_aide = CTRL_Bouton_image.CTRL(self.panel_base, texte=_(u"Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_retour = wx.BitmapButton(self.panel_base, -1, wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Retour_L72.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_suite = wx.BitmapButton(self.panel_base, -1, wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Suite_L72.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self.panel_base, texte=_(u"Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))
        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_retour, self.bouton_retour)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_suite, self.bouton_suite)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)
        self.bouton_retour.Enable(False)
        self.nbrePages = len(self.listePages)
        self.pageVisible = 1
        self.dictModeles = {
            "IDmodele": IDmodele,
            "IDclassification": None,
            "IDtype": None,
            "convention_code": None,
            "ccns_group": None,
            "cee_qualification": None,
            "nom": "",
            "description": "",
        }
        self.dictChamps = {}
        if IDmodele != 0:
            self.Importation(IDmodele)
        self.Creation_Pages()

    def Importation(self, IDmodele=0):
        DB = GestionDB.DB()
        champs = DB.GetListeChamps2("contrats_modeles")
        modernes = all(x in champs for x in ("convention_code", "ccns_group", "cee_qualification"))
        if modernes:
            req = "SELECT nom, description, IDclassification, IDtype, convention_code, ccns_group, cee_qualification FROM contrats_modeles WHERE IDmodele=%d ;" % IDmodele
        else:
            req = "SELECT nom, description, IDclassification, IDtype FROM contrats_modeles WHERE IDmodele=%d ;" % IDmodele
        DB.ExecuterReq(req)
        resultats = DB.ResultatReq()
        if not resultats:
            DB.Close()
            self.dictModeles["IDmodele"] = 0
            return False
        donnees = resultats[0]
        self.dictModeles["nom"] = donnees[0]
        self.dictModeles["description"] = donnees[1]
        self.dictModeles["IDclassification"] = donnees[2]
        self.dictModeles["IDtype"] = donnees[3]
        if modernes:
            self.dictModeles["convention_code"] = donnees[4]
            self.dictModeles["ccns_group"] = donnees[5]
            self.dictModeles["cee_qualification"] = donnees[6]
        req = "SELECT IDchamp, valeur FROM contrats_valchamps WHERE (IDmodele=%d AND type='modele') ;" % IDmodele
        DB.ExecuterReq(req)
        for IDchamp, valeur in DB.ResultatReq():
            self.dictChamps[IDchamp] = valeur
        DB.Close()
        return True

    def Creation_Pages(self):
        for numPage in range(1, self.nbrePages+1):
            page = (Page1, Page2, Page3)[numPage-1](self.panel_base)
            setattr(self, "page%d" % numPage, page)
            self.sizer_pages.Add(page, 1, wx.EXPAND, 0)
            page.Show(False)
        self.page1.Show(True)
        self.sizer_pages.Layout()

    def __set_properties(self):
        self.SetTitle(_(u"Création d'un modèle de contrat"))
        _icon = wx.Icon()
        _icon.CopyFromBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.bouton_aide.SetToolTip(wx.ToolTip("Cliquez ici pour obtenir de l'aide"))
        self.bouton_retour.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour revenir à la page précédente")))
        self.bouton_suite.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour passer à l'étape suivante")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez pour annuler la création du contrat")))
        self.SetMinSize((520, 520))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        sizer_pages = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_base.Add(sizer_pages, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(self.static_line, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_retour, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_suite, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, wx.LEFT, 10)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        self.panel_base.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        sizer_base.Add(self.panel_base, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_base)
        sizer_base.Fit(self)
        self.Layout()
        self.Centre()
        self.sizer_pages = sizer_pages

    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lesmodlesdecontrats")

    def Onbouton_retour(self, event):
        getattr(self, "page%d" % self.pageVisible).Show(False)
        self.pageVisible -= 1
        getattr(self, "page%d" % self.pageVisible).Show(True)
        self.sizer_pages.Layout()
        if self.pageVisible == self.nbrePages-1:
            self.bouton_suite.Enable(True)
            self.bouton_suite.SetBitmapLabel(wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Suite_L72.png"), wx.BITMAP_TYPE_ANY))
        if self.pageVisible == 1:
            self.bouton_retour.Enable(False)

    def Onbouton_suite(self, event):
        if self.ValidationPages() is False:
            return
        if self.pageVisible == self.nbrePages:
            self.Terminer()
            return
        getattr(self, "page%d" % self.pageVisible).Show(False)
        self.pageVisible += 1
        getattr(self, "page%d" % self.pageVisible).Show(True)
        self.sizer_pages.Layout()
        if self.pageVisible == self.nbrePages:
            self.bouton_suite.SetBitmapLabel(wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Valider_L72.png"), wx.BITMAP_TYPE_ANY))
        if self.pageVisible > 1:
            self.bouton_retour.Enable(True)

    def Onbouton_annuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def ValidationPages(self):
        return getattr(self, "page%s" % self.pageVisible).Validation()

    def Terminer(self):
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, "", IDmodele=4)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
