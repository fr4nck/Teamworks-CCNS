#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import GestionDB
import FonctionsPerso


class Page(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.label_titre = wx.StaticText(self, -1, _(u"Création d'un modèle de contrat"))
        self.label_intro = wx.StaticText(self, -1, _(u"Saisissez un nom et une description pour ce modèle :"))
        self.label_nom = wx.StaticText(self, -1, "Nom :")
        self.text_nom = wx.TextCtrl(self, -1, "")
        self.label_description = wx.StaticText(self, -1, "Description :")
        self.text_description = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE)
        self.__set_properties()
        self.__do_layout()
        self.Importation()

    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT, 20)
        grid = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid.Add(self.text_nom, 1, wx.EXPAND, 0)
        grid.Add(self.label_description, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid.Add(self.text_description, 1, wx.EXPAND, 0)
        grid.AddGrowableCol(1)
        grid_sizer_base.Add(grid, 1, wx.LEFT|wx.EXPAND, 20)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)

    def Importation(self):
        d = self.GetGrandParent().dictModeles
        self.text_nom.SetValue(d["nom"])
        self.text_description.SetValue(d["description"])

    def Validation(self):
        if self.text_nom.GetValue() == "":
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir un nom pour ce modèle !"), "Erreur", wx.OK)
            dlg.ShowModal(); dlg.Destroy()
            self.text_nom.SetFocus()
            return False

        dictModeles = self.GetGrandParent().dictModeles
        dictChamps = self.GetGrandParent().dictChamps
        DB = GestionDB.DB()
        champs = DB.GetListeChamps2("contrats_modeles")
        listeDonnees = [
            ("IDclassification", dictModeles.get("IDclassification")),
            ("IDtype", dictModeles.get("IDtype")),
            ("nom", self.text_nom.GetValue()),
            ("description", self.text_description.GetValue()),
        ]
        for nom in ("convention_code", "ccns_group", "cee_qualification"):
            if nom in champs:
                listeDonnees.append((nom, dictModeles.get(nom)))

        if dictModeles["IDmodele"] == 0:
            IDmodele = DB.ReqInsert("contrats_modeles", listeDonnees)
            DB.Commit()
        else:
            DB.ReqMAJ("contrats_modeles", listeDonnees, "IDmodele", dictModeles["IDmodele"])
            DB.Commit()
            IDmodele = dictModeles["IDmodele"]

        req = "SELECT IDval_champ, IDchamp FROM contrats_valchamps WHERE (IDmodele=%d AND type='modele');" % IDmodele
        DB.ExecuterReq(req)
        existants = DB.ResultatReq()
        for IDchamp, valeur in dictChamps.items():
            ligne = [("IDchamp", IDchamp), ("type", "modele"), ("valeur", valeur), ("IDmodele", IDmodele), ("IDcontrat", 0)]
            trouve = False
            for IDval, IDchampDB in existants:
                if IDchampDB == IDchamp:
                    DB.ReqMAJ("contrats_valchamps", ligne, "IDval_champ", IDval)
                    DB.Commit(); trouve = True
            if not trouve:
                DB.ReqInsert("contrats_valchamps", ligne); DB.Commit()
        for IDval, IDchampDB in existants:
            if IDchampDB not in dictChamps:
                DB.ReqDEL("contrats_valchamps", "IDval_champ", IDval)
        DB.Close()
        if FonctionsPerso.FrameOuverte("panel_config_Modeles_Contrats") is not None:
            self.GetGrandParent().GetParent().MAJ_ListCtrl()
        return True
