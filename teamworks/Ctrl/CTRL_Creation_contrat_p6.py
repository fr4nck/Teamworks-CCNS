#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
from Utils import UTILS_Contrats_schema
import wx
from Ctrl import CTRL_Bouton_image
import FonctionsPerso
import GestionDB


def getRGB(winColor):
    b = winColor >> 16
    g = winColor >> 8 & 255
    r = winColor & 255
    return (r,g,b)


class Page(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.parent = self.GetGrandParent()

        self.label_titre = wx.StaticText(self, -1, _(u"Fin de l'assistant de création de contrat"))

        txtIntro = u"""
        <FONT face="Arial" color="#000000" size=2>
        <P>Vous avez saisi toutes les données du contrat. Cliquez sur le bouton 'Valider' pour terminer l'assistant.</P>
        <p>Vous pouvez ensuite par exemple imprimer ce contrat ou la déclaration unique d'embauche correspondante.</p>
        </FONT>
        """
        self.label_intro = FonctionsPerso.TexteHtml(self, texte=txtIntro, Enabled=False)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 20)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)

    def Validation(self):
        dictContrats = self.GetGrandParent().dictContrats
        dictChamps = self.GetGrandParent().dictChamps
        DB = GestionDB.DB()
        UTILS_Contrats_schema.EnsureContractEngineColumns(DB)

        listeDonnees = [
            ("IDpersonne", dictContrats["IDpersonne"]),
            ("IDclassification", dictContrats["IDclassification"]),
            ("IDtype", dictContrats["IDtype"]),
            ("valeur_point", dictContrats["valeur_point"]),
            ("cee_qualification", dictContrats.get("cee_qualification")),
            ("convention_code", dictContrats.get("convention_code")),
            ("ccns_group", dictContrats.get("ccns_group")),
            ("weekly_hours", dictContrats.get("weekly_hours")),
            ("gross_monthly_salary", dictContrats.get("gross_monthly_salary")),
            ("date_debut", dictContrats["date_debut"]),
            ("date_fin", dictContrats["date_fin"]),
            ("date_rupture", dictContrats["date_rupture"]),
            ("essai", dictContrats["essai"]),
        ]

        if dictContrats["IDcontrat"] == 0:
            listeDonnees.append(("signature", ""))
            listeDonnees.append(("due", ""))
            IDcontrat = DB.ReqInsert("contrats", listeDonnees)
            DB.Commit()
        else:
            DB.ReqMAJ("contrats", listeDonnees, "IDcontrat", dictContrats["IDcontrat"])
            DB.Commit()
            IDcontrat = dictContrats["IDcontrat"]

        req = "SELECT IDval_champ, IDchamp FROM contrats_valchamps WHERE (IDcontrat=%d AND type='contrat')  ;" % IDcontrat
        DB.ExecuterReq(req)
        listeChampsDB = DB.ResultatReq()

        for IDchamp, valeur in dictChamps.items():
            donneesChamp = [
                ("IDchamp", IDchamp),
                ("type", "contrat"),
                ("valeur", valeur),
                ("IDcontrat", IDcontrat),
                ("IDmodele", 0),
            ]
            modif = False
            for IDval_champDB, IDchampDB in listeChampsDB:
                if IDchampDB == IDchamp:
                    DB.ReqMAJ("contrats_valchamps", donneesChamp, "IDval_champ", IDval_champDB)
                    DB.Commit()
                    modif = True
            if modif == False:
                DB.ReqInsert("contrats_valchamps", donneesChamp)
                DB.Commit()

        for IDval_champDB, IDchampDB in listeChampsDB:
            trouve = False
            for IDchamp, valeur in dictChamps.items():
                if IDchampDB == IDchamp:
                    trouve = True
            if trouve == False:
                DB.ReqDEL("contrats_valchamps", "IDval_champ", IDval_champDB)

        DB.Close()

        if FonctionsPerso.FrameOuverte("FicheIndividuelle") != None:
            self.GetGrandParent().GetParent().list_ctrl_contrats.Remplissage()
            self.GetGrandParent().GetParent().MAJ_barre_problemes()

        return True
