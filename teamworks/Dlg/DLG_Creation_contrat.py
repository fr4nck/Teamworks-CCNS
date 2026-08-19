#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

from decimal import localcontext

import Chemins
from Utils.UTILS_Traduction import _
from Utils import UTILS_Contrats_schema
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB
import FonctionsPerso

from Ctrl.CTRL_Creation_contrat_p1 import Page as Page1
from Ctrl.CTRL_Creation_contrat_p2 import Page as Page2
from Ctrl.CTRL_Creation_contrat_p3 import Page as LegacyPage3
from Ctrl.CTRL_Creation_contrat_p4 import Page as LegacyPage4
from Ctrl.CTRL_Creation_contrat_p5 import Page as Page5
from Ctrl.CTRL_Creation_contrat_p6 import Page as Page6


class Page3(LegacyPage3):
    """Isole les calculs modernes et rafraîchit les champs dérivés du régime."""

    def _MonthlySalaryDecimal(self):
        with localcontext() as context:
            context.prec = max(28, context.prec)
            return super()._MonthlySalaryDecimal()

    def Validation(self):
        with localcontext() as context:
            context.prec = max(28, context.prec)
            validation = super().Validation()
        if validation and hasattr(self.GetGrandParent(), "page4"):
            # Le choix CCNS/CEE peut modifier la liste des champs legacy utiles.
            self.GetGrandParent().page4.MAJ_ListCtrl()
        return validation


class Page4(LegacyPage4):
    """Conserve les champs legacy sauf ceux désormais fournis par le moteur.

    BRUTJOUR est utilisé par le modèle CEE d'origine de Teamworks. Pour un CEE
    moderne, le montant provient du barème employeur : demander une seconde
    saisie serait contradictoire. Le champ reste disponible hors CEE.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._FilterEngineManagedFields()

    def MAJ_ListCtrl(self):
        super().MAJ_ListCtrl()
        self._FilterEngineManagedFields()

    def _FilterEngineManagedFields(self):
        dialog = self.GetGrandParent()
        if not hasattr(dialog, "page3") or not dialog.page3.IsCEESelected():
            return
        list_ctrl = self.listCtrl_champs
        for index in range(list_ctrl.GetItemCount() - 1, -1, -1):
            IDchamp = list_ctrl.GetItemData(index)
            valeurs = list_ctrl.dictChamps.get(IDchamp)
            mot_cle = (valeurs[3] if valeurs else "") or ""
            if mot_cle.strip().upper() != "BRUTJOUR":
                continue
            list_ctrl.DeleteItem(index)
            list_ctrl.dictChamps.pop(IDchamp, None)
            if IDchamp in list_ctrl.selections:
                list_ctrl.selections.remove(IDchamp)


class Dialog(wx.Dialog):
    def __init__(self, parent, title="", IDcontrat=0, IDpersonne=0):
        wx.Dialog.__init__(self, parent, -1, name="frm_creation_contrats",style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.listePages = ("Page1", "Page2", "Page3", "Page4", "Page5", "Page6")

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

        self.dictContrats = {
            "IDcontrat": IDcontrat,
            "IDpersonne": IDpersonne,
            "IDclassification": None,
            "IDtype": None,
            "valeur_point": None,
            "cee_qualification": None,
            "convention_code": "CCNS" if IDcontrat == 0 else None,
            "ccns_group": None,
            "weekly_hours": None,
            "gross_monthly_salary": None,
            "date_debut": "",
            "date_fin": "",
            "date_rupture": "",
            "essai": 0,
            "signature": None,
        }

        self.dictChamps = {}

        if IDcontrat != 0:
            self.SetTitle(_(u"Modification d'un contrat"))
            self.Importation(IDcontrat)

        self.Creation_Pages()
        self._ApplyInitialResponsiveSize()

    def Importation(self, IDcontrat=0):
        DB = GestionDB.DB()
        UTILS_Contrats_schema.EnsureContractEngineColumns(DB)
        req = (
            "SELECT IDclassification, IDtype, valeur_point, cee_qualification, "
            "convention_code, ccns_group, weekly_hours, gross_monthly_salary, "
            "date_debut, date_fin, date_rupture, essai "
            "FROM contrats WHERE IDcontrat=%d ;" % IDcontrat
        )
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()[0]

        self.dictContrats["IDclassification"] = listeDonnees[0]
        self.dictContrats["IDtype"] = listeDonnees[1]
        self.dictContrats["valeur_point"] = listeDonnees[2]
        self.dictContrats["cee_qualification"] = listeDonnees[3]
        self.dictContrats["convention_code"] = listeDonnees[4]
        self.dictContrats["ccns_group"] = listeDonnees[5]
        self.dictContrats["weekly_hours"] = listeDonnees[6]
        self.dictContrats["gross_monthly_salary"] = listeDonnees[7]
        self.dictContrats["date_debut"] = listeDonnees[8]
        self.dictContrats["date_fin"] = listeDonnees[9]
        self.dictContrats["date_rupture"] = listeDonnees[10]
        self.dictContrats["essai"] = listeDonnees[11]

        req = "SELECT IDchamp, valeur FROM contrats_valchamps WHERE (IDcontrat=%d AND type='contrat')  ;" % IDcontrat
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()

        for item in listeDonnees:
            self.dictChamps[item[0]] = item[1]

        DB.Close()

    def Creation_Pages(self):
        """ Creation des pages """
        for numPage in range(1, self.nbrePages+1):
            exec("self.page" + str(numPage) + " = " + self.listePages[numPage-1] + "(self.panel_base)")
            exec("self.sizer_pages.Add(self.page" + str(numPage) + ", 1, wx.EXPAND, 0)")
            self.sizer_pages.Layout()
            exec("self.page" + str(numPage) + ".Show(False)")
        self.page1.Show(True)
        self.sizer_pages.Layout()

    def _ApplyInitialResponsiveSize(self):
        """Dimensionne une fois le wizard sur sa page la plus exigeante.

        L'ancien dialogue faisait ``Fit()`` avant de créer les pages : il
        s'ouvrait donc autour de 500x460 puis tronquait la page contrat et la
        barre de navigation. On calcule maintenant le besoin réel des six pages
        et on le borne à la zone de travail Windows. La taille reste ensuite
        stable pendant toute la navigation.
        """
        content_width = 0
        content_height = 0
        for numPage in range(1, self.nbrePages + 1):
            page = getattr(self, "page%d" % numPage)
            best = page.GetBestSize()
            minimum = page.GetMinSize()
            content_width = max(content_width, best.GetWidth(), minimum.GetWidth())
            content_height = max(content_height, best.GetHeight(), minimum.GetHeight())

        button_height = max(
            self.bouton_aide.GetBestSize().GetHeight(),
            self.bouton_retour.GetBestSize().GetHeight(),
            self.bouton_suite.GetBestSize().GetHeight(),
            self.bouton_annuler.GetBestSize().GetHeight(),
        )
        desired_width = max(740, content_width + 40)
        desired_height = max(640, content_height + button_height + 70)

        try:
            display_rect = wx.GetClientDisplayRect()
            available_width = display_rect.GetWidth()
            available_height = display_rect.GetHeight()
        except Exception:
            display_size = wx.GetDisplaySize()
            available_width = display_size.GetWidth()
            available_height = display_size.GetHeight()

        max_width = max(640, available_width - 60)
        max_height = max(520, available_height - 60)
        width = min(desired_width, max_width)
        height = min(desired_height, max_height)

        min_width = min(720, max_width)
        min_height = min(600, max_height)
        self.SetMinSize((min_width, min_height))
        self.SetSize((width, height))
        self.panel_base.Layout()
        self.sizer_pages.Layout()
        self.Layout()
        self.CenterOnScreen()

    def __set_properties(self):
        self.SetTitle(_(u"Création d'un contrat"))
        _icon = wx.Icon()
        _icon.CopyFromBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.bouton_aide.SetToolTip(wx.ToolTip("Cliquez ici pour obtenir de l'aide"))
        self.bouton_aide.SetSize(self.bouton_aide.GetBestSize())
        self.bouton_retour.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour revenir à la page précédente")))
        self.bouton_retour.SetSize(self.bouton_retour.GetBestSize())
        self.bouton_suite.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour passer à l'étape suivante")))
        self.bouton_suite.SetSize(self.bouton_suite.GetBestSize())
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez pour annuler la création du contrat")))
        self.bouton_annuler.SetSize(self.bouton_annuler.GetBestSize())
        # Taille de secours avant création des pages. La taille réelle est
        # calculée ensuite par _ApplyInitialResponsiveSize().
        self.SetMinSize((500, 460))

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
        self.CenterOnScreen()
        self.sizer_pages = sizer_pages

    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Creruncontrat")

    def Onbouton_retour(self, event):
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(False)
        self.pageVisible -= 1
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(True)
        self.sizer_pages.Layout()
        if self.pageVisible == self.nbrePages-1:
            self.bouton_suite.Enable(True)
            self.bouton_suite.SetBitmapLabel(wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Suite_L72.png"), wx.BITMAP_TYPE_ANY))
        if self.pageVisible == 1:
            self.bouton_retour.Enable(False)

    def Onbouton_suite(self, event):
        validation = self.ValidationPages()
        if validation == False:
            return
        if self.pageVisible == self.nbrePages:
            self.Terminer()
            return
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(False)
        self.pageVisible += 1
        pageCible = eval("self.page"+str(self.pageVisible))
        pageCible.Show(True)
        self.sizer_pages.Layout()
        if self.pageVisible == self.nbrePages:
            self.bouton_suite.SetBitmapLabel(wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Valider_L72.png"), wx.BITMAP_TYPE_ANY))
        if self.pageVisible > 1:
            self.bouton_retour.Enable(True)

    def Onbouton_annuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def ValidationPages(self):
        """ Validation des données avant changement de pages """
        validation = getattr(self, "page%s" % self.pageVisible).Validation()
        return validation

    def Terminer(self):
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, "", IDcontrat=0, IDpersonne=0)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
