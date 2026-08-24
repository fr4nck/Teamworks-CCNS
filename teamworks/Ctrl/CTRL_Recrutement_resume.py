#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Composants de suivi et de détail du module Recrutement."""

import wx

from Ctrl import CTRL_Gadget_candidatures
from Ctrl import CTRL_Recrutement_core as CORE
from Ctrl import CTRL_Texte
from Ol import OL_candidatures
from Ol import OL_entretiens
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


def _surface(window, token="surface_container_lowest"):
    window.SetBackgroundColour(UTILS_Interface.GetToken(token))
    return window


class GadgetEntretiens(wx.Panel):
    def __init__(self, parent, ID=-1, name="gadget_entretiens"):
        wx.Panel.__init__(self, parent, ID, name=name, style=wx.TAB_TRAVERSAL)
        _surface(self)
        self.ctrl = OL_entretiens.ListView(
            self,
            id=-1,
            name="OL_gadget_entretiens",
            afficheHyperlink=False,
            prochainsEntretiens=True,
            modeAffichage="gadget",
            colorerSalaries=False,
            style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.NO_BORDER | wx.LC_SINGLE_SEL,
        )
        fond = UTILS_Interface.GetToken("surface_container_lowest")
        self.ctrl.couleurFond = fond
        self.ctrl.SetBackgroundColour(fond)
        try:
            self.ctrl.stEmptyListMsg.SetBackgroundColour(fond)
        except Exception:
            pass
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.MAJ()

    def MAJ(self):
        self.ctrl.MAJ()


class GadgetInformations(wx.Panel):
    def __init__(self, parent, ID=-1, name="gadget_informations"):
        wx.Panel.__init__(self, parent, ID, name=name, style=wx.TAB_TRAVERSAL)
        _surface(self)
        self.treeCtrl = CTRL_Gadget_candidatures.TreeCtrl(self)
        fond = UTILS_Interface.GetToken("surface_container_lowest")
        self.treeCtrl.couleurFond = fond
        self.treeCtrl.SetBackgroundColour(fond)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.treeCtrl, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def MAJ(self):
        self.treeCtrl.MAJ()


class Panelidentite(CORE.Panelidentite):
    """Rendu moderne du résumé d'identité, logique métier historique conservée."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_identite", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _surface(self)

        self.resume_L1 = CTRL_Texte.H2(self, u"")
        self.resume_L2 = CTRL_Texte.Body(self, u"")
        self.resume_L3 = CTRL_Texte.BodySecondary(self, u"")
        self.resume_L4 = CTRL_Texte.BodySecondary(self, u"")
        self.resume_L5 = CTRL_Texte.BodySecondary(self, u"")
        self.resume_L6 = CTRL_Texte.BodySecondary(self, u"")

        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        for index, controle in enumerate(
            (self.resume_L1, self.resume_L2, self.resume_L3, self.resume_L4, self.resume_L5, self.resume_L6)
        ):
            if index:
                sizer.AddSpacer(gap)
            sizer.Add(controle, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetMinSize((-1, UTILS_Styles.Scale(140)))


class PanelResume(wx.Panel):
    """Détail de sélection moderne avec parentage historique des ObjectListView."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_resume", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _surface(self, "surface_container_low")

        # Le Notebook reste enfant direct du panneau : les OLV historiques
        # conservent ainsi la chaîne list -> notebook -> PanelResume -> window_D.
        self.titre = CTRL_Texte.H3(self, _(u"Détail de la sélection"))
        self.noteBook = wx.Notebook(self, -1)
        self.panel_identite = Panelidentite(self.noteBook)
        self.listCtrl_candidatures = OL_candidatures.ListView(
            self.noteBook,
            id=-1,
            name="OL_candidatures",
            modeAffichage="avec_nom",
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES,
        )
        self.listCtrl_entretiens = OL_entretiens.ListView(
            self.noteBook,
            id=-1,
            name="OL_entretiens",
            modeAffichage="avec_nom",
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES,
        )
        self._mode = "candidat"
        self._installer_pages_candidat()

        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.AddSpacer(gap)
        sizer.Add(self.noteBook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)
        self.SetMinSize((-1, UTILS_Styles.Scale(220)))

    def _vider_pages(self):
        while self.noteBook.GetPageCount():
            self.noteBook.RemovePage(0)

    def _installer_pages_candidat(self):
        self._vider_pages()
        self.noteBook.AddPage(self.panel_identite, _(u"Identité"))
        self.noteBook.AddPage(self.listCtrl_candidatures, _(u"Candidatures"))
        self.noteBook.AddPage(self.listCtrl_entretiens, _(u"Entretiens"))
        self._mode = "candidat"

    def _installer_page_emploi(self):
        self._vider_pages()
        self.noteBook.AddPage(self.listCtrl_candidatures, _(u"Candidatures"))
        self._mode = "emploi"

    def _index_page(self, page):
        for index in range(self.noteBook.GetPageCount()):
            if self.noteBook.GetPage(index) is page:
                return index
        return -1

    def MAJ(self, IDcandidat=None, IDpersonne=None, IDemploi=None):
        if IDemploi is None:
            if self._mode != "candidat" or self.noteBook.GetPageCount() != 3:
                self._installer_pages_candidat()

            self.panel_identite.MAJidentite(IDcandidat=IDcandidat, IDpersonne=IDpersonne)
            self.listCtrl_candidatures.IDcandidat = IDcandidat
            self.listCtrl_candidatures.IDpersonne = IDpersonne
            self.listCtrl_candidatures.IDemploi = None
            self.listCtrl_candidatures.MAJ()

            self.listCtrl_entretiens.IDcandidat = IDcandidat
            self.listCtrl_entretiens.IDpersonne = IDpersonne
            self.listCtrl_entretiens.MAJ()

            self.noteBook.SetPageText(0, _(u"Identité"))
            self.MAJlabelsPages("candidatures")
            self.MAJlabelsPages("entretiens")
            self.panel_identite.Enable(True)
            self.listCtrl_entretiens.Enable(True)
        else:
            if self._mode != "emploi" or self.noteBook.GetPageCount() != 1:
                self._installer_page_emploi()
            self.listCtrl_candidatures.IDcandidat = None
            self.listCtrl_candidatures.IDpersonne = None
            self.listCtrl_candidatures.IDemploi = IDemploi
            self.listCtrl_candidatures.MAJ()
            self.MAJlabelsPages("candidatures")

    def MAJlabelsPages(self, nomPage="candidatures"):
        if nomPage == "candidatures":
            page = self.listCtrl_candidatures
            nombre = page.GetNbreItems()
            label = _(u"1 candidature") if nombre == 1 else _(u"%d candidatures") % nombre
        elif nomPage == "entretiens":
            page = self.listCtrl_entretiens
            nombre = page.GetNbreItems()
            label = _(u"1 entretien") if nombre == 1 else _(u"%d entretiens") % nombre
        else:
            return
        index = self._index_page(page)
        if index != -1:
            self.noteBook.SetPageText(index, label)
