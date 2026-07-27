#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Chargement différé des onglets lourds de la fiche individuelle."""

import wx

import Chemins
from Utils.UTILS_Traduction import _
from Ctrl import CTRL_Page_generalites
from Ctrl import CTRL_Page_questionnaire
from Ctrl import CTRL_Page_qualifications
from Ctrl import CTRL_Page_contrats
from Ctrl import CTRL_Page_presences
from Ctrl import CTRL_Page_frais
from Ctrl import CTRL_Page_scenarios
from Ctrl import CTRL_Page_candidatures


class LazyNotebook(wx.Notebook):
    """Ne construit les onglets secondaires qu'à leur premier affichage."""

    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Notebook.__init__(self, parent, id, style=wx.BK_DEFAULT)
        self.IDpersonne = IDpersonne
        self._lazy_pages = {}

        images = wx.ImageList(16, 16)
        self.img1 = images.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Identite.png"), wx.BITMAP_TYPE_PNG))
        self.img2 = images.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/BlocNotes.png"), wx.BITMAP_TYPE_PNG))
        self.img3 = images.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Document.png"), wx.BITMAP_TYPE_PNG))
        self.img4 = images.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Presences.png"), wx.BITMAP_TYPE_PNG))
        self.img5 = images.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Scenario.png"), wx.BITMAP_TYPE_PNG))
        self.img6 = images.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calculatrice.png"), wx.BITMAP_TYPE_PNG))
        self.img7 = images.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Candidature.png"), wx.BITMAP_TYPE_PNG))
        self.img8 = images.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Document2.png"), wx.BITMAP_TYPE_PNG))
        self.AssignImageList(images)

        self.pageGeneralites = CTRL_Page_generalites.Panel_general(self, -1, IDpersonne=self.IDpersonne)
        self.AddPage(self.pageGeneralites, _(u"Généralités"))
        self.SetPageImage(0, self.img1)

        if self.IDpersonne == 0:
            self.GetGrandParent().nouvelleFiche = True
            self.pageGeneralites.Sauvegarde()
            self.IDpersonne = self.pageGeneralites.IDpersonne
        else:
            self.GetGrandParent().nouvelleFiche = False

        self.pageQuestionnaire = None
        self.pageStatut = None
        self.pageContrats = None
        self.pagePresences = None
        self.pageScenarios = None
        self.pageFrais = None
        self.pageCandidatures = None

        self._page_specs = [
            ("pageQuestionnaire", _(u"Questionnaire"), self.img8,
             lambda: CTRL_Page_questionnaire.Panel(self, -1, IDpersonne=self.IDpersonne)),
            ("pageStatut", _(u"Qualifications"), self.img2,
             lambda: CTRL_Page_qualifications.Panel_Statut(self, -1, IDpersonne=self.IDpersonne)),
            ("pageContrats", _(u"Contrats"), self.img3,
             lambda: CTRL_Page_contrats.Panel_Contrats(self, -1, IDpersonne=self.IDpersonne)),
            ("pagePresences", _(u"Présences"), self.img4,
             lambda: CTRL_Page_presences.Panel(self, IDpersonne=self.IDpersonne)),
            ("pageScenarios", _(u"Scénarios"), self.img5,
             lambda: CTRL_Page_scenarios.Panel(self, IDpersonne=self.IDpersonne)),
            ("pageFrais", _(u"Frais"), self.img6,
             lambda: CTRL_Page_frais.Panel(self, IDpersonne=self.IDpersonne)),
            ("pageCandidatures", _(u"Recrutement"), self.img7,
             lambda: CTRL_Page_candidatures.Panel(self, IDpersonne=self.IDpersonne)),
        ]
        self._add_secondary_pages()
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def _create_placeholder(self):
        panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer()
        sizer.Add(wx.StaticText(panel, -1, _(u"Chargement de l'onglet…")), 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.AddStretchSpacer()
        panel.SetSizer(sizer)
        return panel

    def _add_secondary_pages(self):
        if self.GetPageCount() > 1:
            return
        self._lazy_pages = {}
        for index, (attribute, title, image, factory) in enumerate(self._page_specs, 1):
            loaded_page = getattr(self, attribute)
            page = loaded_page if loaded_page is not None else self._create_placeholder()
            self.AddPage(page, title)
            self.SetPageImage(index, image)
            self._lazy_pages[index] = {
                "attribute": attribute,
                "title": title,
                "image": image,
                "factory": factory,
                "loaded": loaded_page is not None,
            }

    def EnsurePageLoaded(self, index):
        spec = self._lazy_pages.get(index)
        if spec is None or spec["loaded"]:
            return self.GetPage(index)

        placeholder = self.GetPage(index)
        self.Freeze()
        try:
            page = spec["factory"]()
            spec["loaded"] = True
            setattr(self, spec["attribute"], page)
            self.RemovePage(index)
            self.InsertPage(index, page, spec["title"], True, spec["image"])
            placeholder.Destroy()
            return page
        finally:
            self.Thaw()

    def AfficheAutresPages(self, etat=True):
        if etat and self.GetPageCount() <= 1:
            self._add_secondary_pages()
        elif not etat and self.GetPageCount() > 1:
            for index in range(self.GetPageCount() - 1, 0, -1):
                self.RemovePage(index)

    def OnPageChanged(self, event):
        old_page = event.GetOldSelection()
        new_page = event.GetSelection()

        if old_page == 0:
            self.GetGrandParent().AnnulationImpossible = True
            self.GetGrandParent().bitmap_button_annuler.Enable(False)
            self.pageGeneralites.Sauvegarde()

        self.GetPage(new_page).Refresh()
        spec = self._lazy_pages.get(new_page)
        if spec is not None and not spec["loaded"]:
            wx.CallAfter(self.EnsurePageLoaded, new_page)
        event.Skip()


def install(module):
    """Installe la variante différée dans le module historique, une seule fois."""
    if getattr(module, "_LAZY_INDIVIDUAL_FORM_INSTALLED", False):
        return module

    module.Notebook = LazyNotebook
    base_dialog = module.Dialog

    class LazyDialog(base_dialog):
        def Fermer(self, save=True):
            if save is False:
                if self.nouvelleFiche is True:
                    db = module.GestionDB.DB()
                    db.ReqDEL("coordonnees", "IDpersonne", self.IDpersonne)
                    db.ReqDEL("personnes", "IDpersonne", self.IDpersonne)
                    db.Close()
            else:
                if self.Verifie_validite_donnees() is True:
                    self.notebook.pageGeneralites.Sauvegarde()
                    if self.notebook.pageQuestionnaire is not None:
                        self.notebook.pageQuestionnaire.Sauvegarde()
                else:
                    return

            frame = module.FonctionsPerso.FrameOuverte("Personnes")
            if frame is not None:
                frame.listCtrl_personnes.MAJ(IDpersonne=self.IDpersonne)
                frame.panel_dossiers.tree_ctrl_problemes.MAJ_treeCtrl()
            self.EndModal(module.wx.ID_OK)

    LazyDialog.__name__ = "Dialog"
    LazyDialog.__module__ = module.__name__
    module.Dialog = LazyDialog
    module._LAZY_INDIVIDUAL_FORM_INSTALLED = True
    return module
