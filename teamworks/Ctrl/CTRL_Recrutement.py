#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Page Recrutement moderne de Teamworks.

La logique historique reste archivée dans ``CTRL_Recrutement_core``. Les
composants visibles sont séparés en modules de navigation et de résumé afin de
conserver une structure proche d'une application Web : page, composants et
feuille de styles centrale.
"""

import sys
import wx

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Recrutement_core as CORE
from Ctrl import CTRL_Recrutement_navigation as NAV
from Ctrl import CTRL_Recrutement_resume as RESUME
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Ol import OL_candidatures, OL_candidats, OL_emplois, OL_entretiens
from Utils import UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


MODE_AFFICHAGE = "candidats"

# Compatibilité des noms historiquement importables depuis ce module.
GadgetEntretiens = RESUME.GadgetEntretiens
GadgetInformations = RESUME.GadgetInformations
GadgetAvertissement = RESUME.GadgetAvertissement if hasattr(RESUME, "GadgetAvertissement") else wx.Panel
Panelidentite = RESUME.Panelidentite
PanelResume = RESUME.PanelResume
ToolBar = NAV.BarreModes
BarreRecherche = NAV.BarreRecherche
BarreAffichage = CORE.BarreAffichage


def _surface(window, token="surface"):
    window.SetBackgroundColour(UTILS_Interface.GetToken(token))
    return window


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="Recrutement", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.init = False
        _surface(self)

    def InitPage(self):
        if self.init:
            return

        # Le splitter natif est conservé : les ObjectListView historiques
        # s'appuient encore sur la chaîne window_D -> splitter -> Recrutement.
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

        self._creer_colonne_suivi()
        self._creer_contenu_principal()

        self.splitter.SplitVertically(
            self.window_G,
            self.window_D,
            UTILS_Styles.Scale(330),
        )

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.init = True
        self.AfficheListes()

    def _creer_colonne_suivi(self):
        self.section_entretiens = CTRL_Section.Section(
            self.window_G,
            titre=_(u"Prochains entretiens"),
            niveau=3,
            surface="surface_container_lowest",
        )
        self.gadget_entretiens = GadgetEntretiens(self.section_entretiens.GetContentPanel())
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
        self.gadget_informations = GadgetInformations(self.section_informations.GetContentPanel())
        sizer_infos = wx.BoxSizer(wx.VERTICAL)
        sizer_infos.Add(self.gadget_informations, 1, wx.EXPAND)
        self.section_informations.GetContentPanel().SetSizer(sizer_infos)

        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.section_entretiens, 1, wx.EXPAND | wx.ALL, padding)
        sizer.AddSpacer(gap)
        sizer.Add(
            self.section_informations,
            2,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            padding,
        )
        self.window_G.SetSizer(sizer)

    def _creer_contenu_principal(self):
        self.titre_liste = CTRL_Texte.H2(self.window_D, _(u"Candidats"))
        self.barreOutils = ToolBar(self.window_D, mode_initial=MODE_AFFICHAGE)
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

        self.barreRecherche = BarreRecherche(self.window_D, self.listCtrl_candidats)
        self.panel_resume = PanelResume(self.window_D)
        self._creer_boutons()
        self._installer_layout_principal()

        if "linux" in sys.platform:
            self.bouton_export_excel.Enable(False)

        self.bouton_modifier.Enable(False)
        self.bouton_supprimer.Enable(False)
        self.AffichePanelResume(False)

    def _creer_boutons(self):
        definitions = (
            ("bouton_ajouter", _(u"Ajouter"), self.OnBoutonAjouter),
            ("bouton_modifier", _(u"Modifier"), self.OnBoutonModifier),
            ("bouton_supprimer", _(u"Supprimer"), self.OnBoutonSupprimer),
            ("bouton_rechercher", _(u"Filtres"), self.OnBoutonRechercher),
            ("bouton_affichertout", _(u"Tout afficher"), self.OnBoutonAfficherTout),
            ("bouton_options", _(u"Colonnes"), self.OnBoutonOptions),
            ("bouton_courrier", _(u"Courrier"), self.OnBoutonCourrier),
            ("bouton_imprimer", _(u"Imprimer"), self.OnBoutonImprimer),
            ("bouton_export_texte", _(u"Export texte"), self.OnBoutonExportTexte),
            ("bouton_export_excel", _(u"Export Excel"), self.OnBoutonExportExcel),
            ("bouton_aide", _(u"Aide"), self.OnBoutonAide),
        )
        self._boutons_actions = []
        for nom, texte, handler in definitions:
            bouton = CTRL_Bouton_image.CTRL(self.window_D, texte=texte)
            bouton.Bind(wx.EVT_BUTTON, handler)
            setattr(self, nom, bouton)
            self._boutons_actions.append(bouton)

        self.barreRecherche.SetToolTip(
            wx.ToolTip(
                _(u"Saisissez un nom, un prénom, une ville ou un autre élément de la fiche candidat.")
            )
        )

    def _installer_layout_principal(self):
        padding = UTILS_Styles.GetLayoutSpacing("content_padding")
        gap = UTILS_Styles.GetLayoutSpacing("control_gap")

        actions = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in self._boutons_actions:
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

        # Nom conservé pour les appels historiques qui demandent simplement Layout().
        self.grid_sizer_D = sizer

    def ChangerMode(self, mode):
        global MODE_AFFICHAGE
        if mode not in ("candidats", "candidatures", "entretiens", "emplois"):
            return
        MODE_AFFICHAGE = mode
        CORE.MODE_AFFICHAGE = mode
        self.AfficheListes()
        self.AffichePanelResume(False)

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

    def OnBoutonCourrier(self, event):
        self._liste_active().CourrierPublipostage(mode="multiple")

    def OnBoutonImprimer(self, event):
        self._liste_active().Imprimer()

    def OnBoutonExportTexte(self, event):
        self._liste_active().ExportTexte()

    def OnBoutonExportExcel(self, event):
        self._liste_active().ExportExcel()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

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
        self.barreOutils.SetMode(MODE_AFFICHAGE, notifier=False)
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
