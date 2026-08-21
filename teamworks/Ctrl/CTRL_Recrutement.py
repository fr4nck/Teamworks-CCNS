#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Coque moderne du module Recrutement Teamworks.

La logique historique reste disponible dans ``CTRL_Recrutement_core``.
Ce module reconstruit l'interface visible avec les composants du design
system tout en conservant la hiérarchie ``window_D -> splitter -> Recrutement``
attendue par les ObjectListView existantes.
"""

import sys
import wx

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Gadget_candidatures
from Ctrl import CTRL_Recrutement_core as CORE
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Ol import OL_candidatures
from Ol import OL_candidats
from Ol import OL_entretiens
from Ol import OL_emplois
from ObjectListView import Filter
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


MODE_AFFICHAGE = "candidats"


def _racine_recrutement(window):
    current = window
    while current is not None:
        try:
            if current.GetName() == "Recrutement":
                return current
        except Exception:
            pass
        try:
            current = current.GetParent()
        except Exception:
            current = None
    return None


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


class GadgetAvertissement(wx.Panel):
    def __init__(self, parent, ID=-1, name="gadget_avertissement"):
        wx.Panel.__init__(self, parent, ID, name=name, style=wx.TAB_TRAVERSAL)
        _surface(self, "surface_container_low")
        self.label_introduction = CTRL_Texte.BodySecondary(
            self,
            _(u"Attention, ce module Recrutement est encore en phase de test. "
              u"Merci de bien vouloir signaler les bugs rencontrés."),
        )
        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_introduction, 1, wx.EXPAND | wx.ALL, padding)
        self.SetSizer(sizer)


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
    """Détail de la sélection sans hauteur fixe ni icônes de notebook."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_resume", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _surface(self, "surface_container_low")

        self.section = CTRL_Section.Section(
            self,
            titre=_(u"Détail de la sélection"),
            niveau=3,
            surface="surface_container_low",
        )
        contenu = self.section.GetContentPanel()

        self.noteBook = wx.Notebook(contenu, -1)
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

        sizer_contenu = wx.BoxSizer(wx.VERTICAL)
        sizer_contenu.Add(self.noteBook, 1, wx.EXPAND)
        contenu.SetSizer(sizer_contenu)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.section, 1, wx.EXPAND)
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


class BoutonMode(wx.ToggleButton):
    def __init__(self, parent, label, mode):
        wx.ToggleButton.__init__(self, parent, -1, label=label)
        self.mode = mode
        self.SetFont(UTILS_Styles.GetFont("label"))
        self.SetMinSize((-1, UTILS_Styles.GetControlMetric("button_min_height")))
        self.AppliquerTheme(False)

    def AppliquerTheme(self, actif=False):
        if actif:
            fond = UTILS_Interface.GetToken("primary_container")
            texte = UTILS_Interface.GetToken("on_primary_container")
        else:
            fond = UTILS_Interface.GetToken("surface_container_low")
            texte = UTILS_Interface.GetToken("on_surface")
        self.SetBackgroundColour(fond)
        self.SetForegroundColour(texte)
        self.SetValue(bool(actif))


class ToolBar(wx.Panel):
    """Navigation de modes flexible remplaçant la wx.ToolBar 22 px."""

    MODES = (
        ("candidats", _(u"Candidats")),
        ("candidatures", _(u"Candidatures")),
        ("entretiens", _(u"Entretiens")),
        ("emplois", _(u"Offres d'emploi")),
    )

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="barre_modes_recrutement")
        _surface(self, "surface_container_low")
        self.boutons = {}

        gap = UTILS_Styles.GetLayoutSpacing("control_gap")
        sizer = wx.WrapSizer(wx.HORIZONTAL)
        for mode, label in self.MODES:
            bouton = BoutonMode(self, label, mode)
            bouton.Bind(wx.EVT_TOGGLEBUTTON, self.ModeAffichage)
            self.boutons[mode] = bouton
            sizer.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)
        self.SetSizer(sizer)
        self.SetMode(MODE_AFFICHAGE, notifier=False)

    def SetMode(self, mode, notifier=True):
        global MODE_AFFICHAGE
        if mode not in self.boutons:
            return
        MODE_AFFICHAGE = mode
        CORE.MODE_AFFICHAGE = mode
        for code, bouton in self.boutons.items():
            bouton.AppliquerTheme(code == mode)
        if notifier:
            racine = _racine_recrutement(self)
            if racine is not None:
                racine.AfficheListes()
                racine.AffichePanelResume(False)

    def ModeAffichage(self, event):
        self.SetMode(event.GetEventObject().mode)

    def Rechercher(self, event):
        racine = _racine_recrutement(self)
        if racine is not None:
            racine.OnBoutonRechercher(None)

    def Aide(self, event):
        racine = _racine_recrutement(self)
        if racine is not None:
            racine.OnBoutonAide(None)


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, owner):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.owner = owner
        self.SetDescriptiveText(_(u"Rechercher un candidat"))
        self.ShowSearchButton(True)
        self.ShowCancelButton(False)
        self.SetMinSize((-1, UTILS_Styles.GetControlMetric("input_min_height")))

        self.listView = owner.listCtrl_candidats
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(
            Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes])
        )

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, event):
        self.Recherche(self.GetValue())

    def OnCancel(self, event):
        self.SetValue("")
        self.Recherche("")

    def OnDoSearch(self, event):
        self.Recherche(self.GetValue())

    def Recherche(self, txtSearch):
        self.ShowCancelButton(bool(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()


BarreAffichage = CORE.BarreAffichage


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="Recrutement", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.init = False
        _surface(self, "surface")

    def InitPage(self):
        if self.init:
            return

        self.splitter = wx.SplitterWindow(
            self,
            -1,
            style=wx.SP_LIVE_UPDATE | wx.SP_3D,
            name="splitter_recrutement",
        )
        self.splitter.SetSashGravity(0.22)
        self.splitter.SetMinimumPaneSize(UTILS_Styles.Scale(230))

        self.window_G = wx.Panel(self.splitter, -1, name="recrutement_colonne_suivi")
        self.window_D = wx.Panel(self.splitter, -1, name="recrutement_contenu")
        _surface(self.window_G, "surface_container_low")
        _surface(self.window_D, "surface")

        self.section_entretiens = CTRL_Section.Section(
            self.window_G,
            titre=_(u"Prochains entretiens"),
            niveau=3,
            surface="surface_container_lowest",
        )
        self.gadget_entretiens = GadgetEntretiens(
            self.section_entretiens.GetContentPanel()
        )
        sizer_entretiens = wx.BoxSizer(wx.VERTICAL)
        sizer_entretiens.Add(self.gadget_entretiens, 1, wx.EXPAND)
        self.section_entretiens.GetContentPanel().SetSizer(sizer_entretiens)

        self.section_informations = CTRL_Section.Section(
            self.window_G,
            titre=_(u"À traiter"),
            niveau=3,
            description=_(u"Entretiens sans avis et candidatures en attente de réponse."),
            surface="surface_container_lowest",
        )
        self.gadget_informations = GadgetInformations(
            self.section_informations.GetContentPanel()
        )
        sizer_infos = wx.BoxSizer(wx.VERTICAL)
        sizer_infos.Add(self.gadget_informations, 1, wx.EXPAND)
        self.section_informations.GetContentPanel().SetSizer(sizer_infos)

        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        sizer_gauche = wx.BoxSizer(wx.VERTICAL)
        sizer_gauche.Add(self.section_entretiens, 1, wx.EXPAND | wx.ALL, padding)
        sizer_gauche.AddSpacer(gap)
        sizer_gauche.Add(
            self.section_informations,
            2,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            padding,
        )
        self.window_G.SetSizer(sizer_gauche)

        self.titre_liste = CTRL_Texte.H2(self.window_D, _(u"Candidats"))
        self.barreOutils = ToolBar(self.window_D)

        self.label_selection = CTRL_Texte.BodySecondary(self.window_D, u"")
        self.label_selection.Show(False)

        style_liste = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES
        self.listCtrl_candidats = OL_candidats.ListView(
            self.window_D, id=-1, name="OL_candidats", style=style_liste
        )
        self.listCtrl_candidatures = OL_candidatures.ListView(
            self.window_D,
            id=-1,
            name="OL_candidatures",
            modeAffichage="avec_nom",
            style=style_liste,
        )
        self.listCtrl_entretiens = OL_entretiens.ListView(
            self.window_D,
            id=-1,
            name="OL_entretiens",
            modeAffichage="avec_nom",
            style=style_liste,
        )
        self.listCtrl_emplois = OL_emplois.ListView(
            self.window_D, id=-1, name="OL_emplois", style=style_liste
        )
        self.barreRecherche = BarreRecherche(self.window_D, self)

        self.panel_resume = PanelResume(self.window_D)

        self.bouton_ajouter = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Ajouter"))
        self.bouton_modifier = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Modifier"))
        self.bouton_supprimer = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Supprimer"))
        self.bouton_rechercher = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Filtres"))
        self.bouton_affichertout = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Tout afficher"))
        self.bouton_options = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Colonnes"))
        self.bouton_courrier = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Courrier"))
        self.bouton_imprimer = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Imprimer"))
        self.bouton_export_texte = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Export texte"))
        self.bouton_export_excel = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Export Excel"))
        self.bouton_aide = CTRL_Bouton_image.CTRL(self.window_D, texte=_(u"Aide"))

        self._installer_actions()
        self._installer_layout()

        if "linux" in sys.platform:
            self.bouton_export_excel.Enable(False)

        self.bouton_modifier.Enable(False)
        self.bouton_supprimer.Enable(False)
        self.AffichePanelResume(False)

        self.splitter.SplitVertically(
            self.window_G,
            self.window_D,
            UTILS_Styles.Scale(330),
        )

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer_base)

        self.init = True
        self.AfficheListes()

    def _installer_actions(self):
        bindings = (
            (self.bouton_ajouter, self.OnBoutonAjouter),
            (self.bouton_modifier, self.OnBoutonModifier),
            (self.bouton_supprimer, self.OnBoutonSupprimer),
            (self.bouton_rechercher, self.OnBoutonRechercher),
            (self.bouton_affichertout, self.OnBoutonAfficherTout),
            (self.bouton_options, self.OnBoutonOptions),
            (self.bouton_courrier, self.OnBoutonCourrier),
            (self.bouton_imprimer, self.OnBoutonImprimer),
            (self.bouton_export_texte, self.OnBoutonExportTexte),
            (self.bouton_export_excel, self.OnBoutonExportExcel),
            (self.bouton_aide, self.OnBoutonAide),
        )
        for bouton, handler in bindings:
            bouton.Bind(wx.EVT_BUTTON, handler)

        self.barreRecherche.SetToolTip(
            wx.ToolTip(
                _(u"Saisissez un nom, un prénom, une ville ou un autre élément "
                  u"de la fiche candidat.")
            )
        )

    def _installer_layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("control_gap")
        padding = UTILS_Styles.GetLayoutSpacing("content_padding")

        actions = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (
            self.bouton_ajouter,
            self.bouton_modifier,
            self.bouton_supprimer,
            self.bouton_rechercher,
            self.bouton_affichertout,
            self.bouton_options,
            self.bouton_courrier,
            self.bouton_imprimer,
            self.bouton_export_texte,
            self.bouton_export_excel,
            self.bouton_aide,
        ):
            actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre_liste, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(self.barreOutils, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)
        sizer.Add(self.label_selection, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)

        for liste in (
            self.listCtrl_candidats,
            self.listCtrl_candidatures,
            self.listCtrl_entretiens,
            self.listCtrl_emplois,
        ):
            sizer.Add(liste, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, padding)

        sizer.Add(self.barreRecherche, 0, wx.EXPAND | wx.ALL, padding)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        sizer.Add(self.panel_resume, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)

        self.window_D.SetSizer(sizer)
        self.grid_sizer_D = sizer

    def _liste_active(self):
        return getattr(self, "listCtrl_%s" % MODE_AFFICHAGE)

    def OnBoutonAjouter(self, event):
        self._liste_active().Ajouter()

    def OnBoutonModifier(self, event):
        self._liste_active().Modifier()

    def OnBoutonSupprimer(self, event):
        self._liste_active().Supprimer()

    def OnBoutonRechercher(self, event):
        self._liste_active().Rechercher()

    def OnBoutonAfficherTout(self, event):
        self._liste_active().AfficherTout()
        self.AfficheLabelSelection(False)

    def OnBoutonOptions(self, event):
        self._liste_active().Options()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

    def OnBoutonCourrier(self, event):
        self._liste_active().CourrierPublipostage(mode="multiple")

    def OnBoutonImprimer(self, event):
        self._liste_active().Imprimer()

    def OnBoutonExportTexte(self, event):
        self._liste_active().ExportTexte()

    def OnBoutonExportExcel(self, event):
        self._liste_active().ExportExcel()

    def AffichePanelResume(self, etat=True):
        self.panel_resume.Show(bool(etat))
        self.window_D.Layout()
        self.Refresh()

    def AfficheLabelSelection(self, etat=True):
        self.label_selection.Show(bool(etat))
        self.window_D.Layout()
        self.Refresh()

    def AfficheListes(self):
        titres = {
            "candidats": _(u"Candidats"),
            "candidatures": _(u"Candidatures"),
            "entretiens": _(u"Entretiens"),
            "emplois": _(u"Offres d'emploi"),
        }
        for mode in ("candidats", "candidatures", "entretiens", "emplois"):
            getattr(self, "listCtrl_%s" % mode).Show(mode == MODE_AFFICHAGE)

        self.titre_liste.SetLabel(titres[MODE_AFFICHAGE])
        self.barreRecherche.Show(MODE_AFFICHAGE == "candidats")
        self.bouton_courrier.Show(MODE_AFFICHAGE in ("candidats", "candidatures"))
        self.bouton_modifier.Enable(False)
        self.bouton_supprimer.Enable(False)

        self.window_D.Layout()
        self.Refresh()
        self._liste_active().MAJ()

    def MAJpanel(self, listeElements=None, MAJpanelResume=True):
        if listeElements is None:
            listeElements = []
        if not self.init:
            self.InitPage()

        for mode in ("candidats", "candidatures", "entretiens", "emplois"):
            liste = getattr(self, "listCtrl_%s" % mode)
            if liste.IsShown():
                liste.MAJ()
        self.gadget_entretiens.MAJ()
        self.gadget_informations.MAJ()

        if MAJpanelResume:
            self.AffichePanelResume(False)

    def MAJapresVerrouillage(self, OL_gadget=False, OL_principal=False, OL_resume=False):
        if OL_gadget:
            self.gadget_entretiens.MAJ()
        if OL_principal and self.listCtrl_entretiens.IsShown():
            self.listCtrl_entretiens.MAJ()
        if OL_resume and self.panel_resume.noteBook.GetPageCount() > 1:
            if self.panel_resume.listCtrl_entretiens.IsShown():
                self.panel_resume.listCtrl_entretiens.MAJ()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.statusbar = self.CreateStatusBar(2, 0)
        self.statusbar.SetStatusWidths([360, -1])
        self.panel = Panel(self)
        self.panel.InitPage()
        self.panel.MAJpanel()
        self.SetTitle(_(u"Recrutement"))
        UTILS_Styles.ApplyWindowProfile(self, "wide")
        self.Centre()


if __name__ == "__main__":
    app = wx.App(0)
    frame = MyFrame(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
