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
import GestionDB
import datetime
import FonctionsPerso
from Utils import UTILS_Dates
from Utils import UTILS_Customize
from Utils import UTILS_Interface
from Ctrl import CTRL_Bouton_image, CTRL_Gadget_pb_personnes
import sys

from Ol import OL_personnes
from Ctrl import CTRL_Photo

from ObjectListView import Filter

from application.services.person_summary import get_person_summary, select_contract_summary
from infrastructure.repositories.person_summary_repository import GestionDBPersonSummaryRepository


def _echelle_interface():
    try:
        valeur = UTILS_Customize.GetValeur(
            "interface", "echelle_interface", "", ajouter_si_manquant=False
        )
        if valeur in (None, ""):
            valeur = UTILS_Customize.GetValeur(
                "interface", "echelle_police", "100", type_valeur=int
            )
        return max(80, min(200, int(valeur)))
    except Exception:
        return 100


def _bouton_action(parent, nom_image):
    """Crée une action iconique via le contrat commun Teamworks-CCNS."""
    return CTRL_Bouton_image.CTRL(
        parent,
        cheminImage=Chemins.GetStaticPath("Images/32x32/%s" % nom_image),
    )


class PanelDossiers(wx.Panel):
    """Panneau compact des dossiers à contrôler, sans remplissage décoratif."""

    def __init__(self, parent, ID=-1, name="panel_dossiers"):
        wx.Panel.__init__(self, parent, ID, name=name)

        self.titre = wx.StaticText(self, -1, _(u"État des dossiers"))
        police = self.titre.GetFont()
        police.SetWeight(wx.FONTWEIGHT_BOLD)
        self.titre.SetFont(police)

        self.tree_ctrl_problemes = CTRL_Gadget_pb_personnes.TreeCtrl(self)

        surface = UTILS_Interface.GetToken("surface")
        controle = UTILS_Interface.GetToken("surface_container_lowest")
        self.SetBackgroundColour(surface)
        self.tree_ctrl_problemes.couleurFond = (
            controle.Red(), controle.Green(), controle.Blue()
        )
        self.tree_ctrl_problemes.SetBackgroundColour(controle)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer.Add(self.tree_ctrl_problemes, 1, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(sizer)


class PanelResume(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="panel_resume")
        self.parent = parent

        self.titre = wx.StaticText(self, -1, _(u"Détail de la sélection"))
        police_titre = self.titre.GetFont()
        police_titre.SetWeight(wx.FONTWEIGHT_BOLD)
        self.titre.SetFont(police_titre)

        self.bitmap_photo = CTRL_Photo.CTRL_Photo(self, style=wx.SUNKEN_BORDER)
        self.bitmap_photo.SetPhoto(
            IDindividu=None,
            nomFichier=Chemins.GetStaticPath("Images/128x128/Personne.png"),
            taillePhoto=(128, 128),
        )

        self.resume_L1 = wx.StaticText(self, -1, "")
        self.resume_L2 = wx.StaticText(self, -1, "")
        self.resume_L3 = wx.StaticText(self, -1, "")
        self.resume_L4 = wx.StaticText(self, -1, "")
        self.resume_L5 = wx.StaticText(self, -1, "")
        self.resume_L6 = wx.StaticText(self, -1, "")

        police_nom = self.resume_L1.GetFont()
        police_nom.SetWeight(wx.FONTWEIGHT_BOLD)
        police_nom.SetPointSize(max(police_nom.GetPointSize() + 3, 12))
        self.resume_L1.SetFont(police_nom)

        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_low"))

        sizer_texte = wx.BoxSizer(wx.VERTICAL)
        sizer_texte.Add(self.resume_L1, 0, wx.BOTTOM, 6)
        for controle in (self.resume_L2, self.resume_L3, self.resume_L4):
            sizer_texte.Add(controle, 0, wx.BOTTOM, 3)
        sizer_texte.AddSpacer(3)
        sizer_texte.Add(self.resume_L5, 0, wx.BOTTOM, 3)
        sizer_texte.Add(self.resume_L6, 0)

        sizer_contenu = wx.BoxSizer(wx.HORIZONTAL)
        sizer_contenu.Add(self.bitmap_photo, 0, wx.ALL, 10)
        sizer_contenu.Add(sizer_texte, 1, wx.EXPAND | wx.ALL, 10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer.Add(sizer_contenu, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        self.bitmap_photo.Refresh()
        event.Skip()

    def RecupIDfichier(self):
        DB = GestionDB.DB()
        req = "SELECT codeIDfichier FROM divers WHERE IDdivers=1;"
        DB.ExecuterReq(req)
        donnees = DB.ResultatReq()
        DB.Close()
        codeIDfichier = donnees[0][0]
        return codeIDfichier

    def OnSelectPersonne(self, IDpersonne=0):
        summary = get_person_summary(IDpersonne, GestionDBPersonSummaryRepository())
        if summary is None:
            return

        identity = summary.identity
        civilite = identity.civilite
        nom = "?" if identity.nom in ("", None) else identity.nom
        prenom = "?" if identity.prenom in ("", None) else identity.prenom
        date_naiss = "?" if identity.date_naiss in ("", None) else FonctionsPerso.DateEngFr(identity.date_naiss)
        ville_naiss = u"?" if identity.ville_naiss in ("", None) else identity.ville_naiss
        adresse_resid = u"?" if identity.adresse_resid in ("", None) else identity.adresse_resid
        cp_resid = u"?" if identity.cp_resid in ("", None) else str(identity.cp_resid)
        ville_resid = u"?" if identity.ville_resid in ("", None) else identity.ville_resid
        age = self.RetourneAge(identity.date_naiss)

        if summary.coordinates:
            texteCoords = _(u"Tél : ") + " | ".join(summary.coordinates)
        else:
            texteCoords = _(u"Aucune coordonnée")

        ligne1 = nom + " " + prenom
        ligne2 = _(u"Né le ") if civilite == "Mr" else _(u"Née le ")
        ligne2 += date_naiss + u" à " + ville_naiss + ", " + age
        ligne3 = _(u"Résidant ") + adresse_resid + " " + cp_resid + " " + ville_resid

        if civilite == "Mr":
            img = "Homme.png"
        elif civilite in ("Mme", "Melle"):
            img = "Femme.png"
        else:
            img = "Personne.png"
        self.bitmap_photo.SetPhoto(
            IDpersonne,
            "Images/128x128/" + img,
            taillePhoto=(128, 128),
        )

        contract_summary = select_contract_summary(summary.contracts)
        contract = contract_summary.contract
        kind = contract_summary.kind

        if kind == "none":
            etatContrat = _(u"Aucun contrat à ce jour.")
            detailContrat = u""
        elif kind == "current_fixed":
            etatContrat = _(u">> Contrat en cours :")
            detailContrat = contract.classification + " du " + FonctionsPerso.DateEngFr(contract.date_debut) + " au " + FonctionsPerso.DateEngFr(contract.date_fin) + "."
        elif kind == "last_fixed":
            etatContrat = _(u"Aucun contrat en cours. Dernier contrat :")
            detailContrat = contract.classification + " du " + FonctionsPerso.DateEngFr(contract.date_debut) + " au " + FonctionsPerso.DateEngFr(contract.date_fin) + "."
        elif kind == "next_fixed":
            etatContrat = _(u"Aucun contrat en cours. Prochain contrat :")
            detailContrat = contract.classification + " du " + FonctionsPerso.DateEngFr(contract.date_debut) + " au " + FonctionsPerso.DateEngFr(contract.date_fin) + "."
        elif kind == "current_ended":
            etatContrat = _(u">> Contrat en cours :")
            detailContrat = contract.classification + " du " + FonctionsPerso.DateEngFr(contract.date_debut) + " au " + FonctionsPerso.DateEngFr(contract.date_rupture) + " (rupture)."
        elif kind == "last_ended":
            etatContrat = _(u"Aucun contrat en cours. Dernier contrat :")
            detailContrat = contract.classification + " du " + FonctionsPerso.DateEngFr(contract.date_debut) + " au " + FonctionsPerso.DateEngFr(contract.date_rupture) + " (rupture)."
        elif kind == "next_ended":
            etatContrat = _(u"Aucun contrat en cours. Prochain contrat :")
            detailContrat = contract.classification + " du " + FonctionsPerso.DateEngFr(contract.date_debut) + " au " + FonctionsPerso.DateEngFr(contract.date_rupture) + " (rupture)."
        elif kind == "current_indefinite":
            etatContrat = _(u">> Contrat en cours :")
            detailContrat = contract.classification + _(u" depuis le ") + FonctionsPerso.DateEngFr(contract.date_debut) + _(u" (durée ind.).")
        else:
            etatContrat = _(u"Aucun contrat en cours. Prochain contrat :")
            detailContrat = contract.classification + _(u" à partir du ") + FonctionsPerso.DateEngFr(contract.date_debut) + _(u" (durée ind.).")

        self.resume_L1.SetLabel(ligne1)
        self.resume_L2.SetLabel(ligne2)
        self.resume_L3.SetLabel(ligne3)
        self.resume_L4.SetLabel(texteCoords)
        self.resume_L5.SetLabel(etatContrat)
        self.resume_L6.SetLabel(detailContrat)
        self.resume_L5.SetForegroundColour(
            UTILS_Interface.GetToken("danger" if contract_summary.active else "on_surface")
        )

        self.Layout()
        self.Refresh()

    def RetourneAge(self, dateStr):
        bday = UTILS_Dates.DateEnDateDD(dateStr)
        if bday is None:
            return ""
        datedujour = datetime.date.today()
        age = (datedujour.year - bday.year) - int((datedujour.month, datedujour.day) < (bday.month, bday.day))
        return str(age) + " ans"


class PanelPersonnes(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, name="Personnes")
        self.parent = parent
        self.init = False
        self._largeurs_colonnes = None
        self._separateur_initialise = False

    def InitPage(self):
        self.splitter = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE)
        self.splitter.SetMinimumPaneSize(180)
        self.splitter.SetSashGravity(0.0)

        self.window_G = wx.Panel(self.splitter, -1)
        self.window_D = wx.Panel(self.splitter, -1)

        self.panel_dossiers = PanelDossiers(self.window_G)
        sizer_gauche = wx.BoxSizer(wx.VERTICAL)
        sizer_gauche.Add(self.panel_dossiers, 1, wx.EXPAND)
        self.window_G.SetSizer(sizer_gauche)

        self.panel_resume = PanelResume(self.window_D)
        self.label_selection = wx.StaticText(self.window_D, -1, u"")
        self.label_selection.SetForegroundColour(UTILS_Interface.GetToken("primary"))
        self.label_selection.Show(False)

        self.listCtrl_personnes = OL_personnes.ListView(
            self.window_D,
            id=-1,
            name="OL_personnes",
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.listCtrl_personnes.SetMinSize((200, 160))
        self.barreRecherche = BarreRecherche(self.window_D)

        self.bouton_ajouter = _bouton_action(self.window_D, "Ajouter.png")
        self.bouton_modifier = _bouton_action(self.window_D, "Modifier.png")
        self.bouton_supprimer = _bouton_action(self.window_D, "Supprimer.png")
        self.bouton_rechercher = _bouton_action(self.window_D, "Calendrier3jours.png")
        self.bouton_affichertout = _bouton_action(self.window_D, "Actualiser.png")
        self.bouton_options = _bouton_action(self.window_D, "Mecanisme.png")
        self.bouton_courrier = _bouton_action(self.window_D, "Mail.png")
        self.bouton_imprimer = _bouton_action(self.window_D, "Imprimante.png")
        self.bouton_export_texte = _bouton_action(self.window_D, "Document.png")
        self.bouton_export_excel = _bouton_action(self.window_D, "Excel.png")
        self.bouton_aide = _bouton_action(self.window_D, "Aide.png")

        self.titre_liste = wx.StaticText(self.window_D, -1, _(u"Liste des individus"))
        police = self.titre_liste.GetFont()
        police.SetWeight(wx.FONTWEIGHT_BOLD)
        police.SetPointSize(max(police.GetPointSize() + 2, 11))
        self.titre_liste.SetFont(police)

        if "linux" in sys.platform:
            self.bouton_export_excel.Enable(False)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonRechercher, self.bouton_rechercher)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAfficherTout, self.bouton_affichertout)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOptions, self.bouton_options)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCourrier, self.bouton_courrier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonExportTexte, self.bouton_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonExportExcel, self.bouton_export_excel)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.listCtrl_personnes.Bind(wx.EVT_SIZE, self.OnTailleListe)

        self.bouton_modifier.Enable(False)
        self.bouton_supprimer.Enable(False)
        self.AffichePanelResume(False)

        self.init = True
        wx.CallAfter(self.InitialiserSeparateur)
        wx.CallAfter(self.AjusterColonnes)

    def __set_properties(self):
        self.barreRecherche.SetToolTip(wx.ToolTip(_(u"Saisissez ici un nom, un prénom, un nom de ville, etc... pour retrouver une personne donnée.")))
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour créer une nouvelle fiche individuelle")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier la fiche sélectionnée dans la liste\n(Vous pouvez également double-cliquer sur une ligne)")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer la fiche sélectionnée dans la liste")))
        self.bouton_rechercher.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour rechercher les personnes présentes sur une période donnée")))
        self.bouton_affichertout.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour réafficher toute la liste")))
        self.bouton_options.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour afficher les options de la liste")))
        self.bouton_imprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour imprimer la liste")))
        self.bouton_export_texte.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour exporter la liste au format texte")))
        self.bouton_export_excel.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour exporter la liste au format Excel")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_courrier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour créer un courrier ou un Email par publipostage")))

    def __do_layout(self):
        actions = wx.WrapSizer(wx.HORIZONTAL)
        groupes = [
            (self.bouton_ajouter, self.bouton_modifier, self.bouton_supprimer),
            (self.bouton_rechercher, self.bouton_affichertout, self.bouton_options),
            (self.bouton_courrier, self.bouton_imprimer, self.bouton_export_texte, self.bouton_export_excel),
            (self.bouton_aide,),
        ]
        for numero, groupe in enumerate(groupes):
            if numero:
                actions.AddSpacer(10)
            for bouton in groupe:
                actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, 4)

        sizer_droite = wx.BoxSizer(wx.VERTICAL)
        sizer_droite.Add(self.titre_liste, 0, wx.EXPAND | wx.ALL, 8)
        sizer_droite.Add(self.label_selection, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        sizer_droite.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        sizer_droite.Add(self.listCtrl_personnes, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        sizer_droite.Add(self.barreRecherche, 0, wx.EXPAND | wx.ALL, 8)
        sizer_droite.Add(self.panel_resume, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.window_D.SetSizer(sizer_droite)
        self.sizer_D = sizer_droite

        self.splitter.SplitVertically(self.window_G, self.window_D, 220)

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer_base)
        self.Layout()

    def InitialiserSeparateur(self):
        if self._separateur_initialise:
            return
        largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            wx.CallLater(50, self.InitialiserSeparateur)
            return
        cible = max(220, min(360, int(round(largeur * 0.18))))
        self.splitter.SetSashPosition(cible, True)
        self._separateur_initialise = True

    def OnTailleListe(self, event):
        wx.CallAfter(self.AjusterColonnes)
        event.Skip()

    def AjusterColonnes(self):
        liste = self.listCtrl_personnes
        try:
            nbre = liste.GetColumnCount()
            largeur_dispo = liste.GetClientSize().GetWidth() - 24
        except Exception:
            return
        if nbre <= 0 or largeur_dispo <= 100:
            return

        if self._largeurs_colonnes is None or len(self._largeurs_colonnes) != nbre:
            self._largeurs_colonnes = [max(22, liste.GetColumnWidth(i)) for i in range(nbre)]

        facteur = _echelle_interface() / 100.0
        minimums = [max(22, int(round(largeur * facteur))) for largeur in self._largeurs_colonnes]
        total = sum(minimums)
        cibles = list(minimums)

        if largeur_dispo > total:
            extensibles = [i for i, largeur in enumerate(minimums) if largeur >= 90]
            if not extensibles:
                extensibles = [nbre - 1]
            surplus = largeur_dispo - total
            poids = sum(minimums[i] for i in extensibles)
            distribue = 0
            for position, index in enumerate(extensibles):
                if position == len(extensibles) - 1:
                    ajout = surplus - distribue
                else:
                    ajout = int(surplus * minimums[index] / float(poids))
                    distribue += ajout
                cibles[index] += max(0, ajout)

        for index, largeur in enumerate(cibles):
            try:
                if liste.GetColumnWidth(index) != largeur:
                    liste.SetColumnWidth(index, largeur)
            except Exception:
                pass

    def OnBoutonAjouter(self, event):
        self.listCtrl_personnes.Ajouter()

    def OnBoutonModifier(self, event):
        self.listCtrl_personnes.Modifier()

    def OnBoutonSupprimer(self, event):
        self.listCtrl_personnes.Supprimer()

    def OnBoutonRechercher(self, event):
        resultat = self.listCtrl_personnes.Rechercher()
        if resultat != False:
            self.AfficheLabelSelection(True)
            date_debut = resultat[0].strftime("%d/%m/%Y")
            date_fin = resultat[1].strftime("%d/%m/%Y")
            texte = _(u"Sélection des personnes présentes du %s au %s :") % (date_debut, date_fin)
            self.label_selection.SetLabel(texte)

    def OnBoutonAfficherTout(self, event):
        self.listCtrl_personnes.AfficherTout()
        self.AfficheLabelSelection(etat=False)

    def OnBoutonOptions(self, event):
        self.listCtrl_personnes.Options()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Personnes")

    def AffichePanelResume(self, etat=True):
        if etat == True and self.panel_resume.IsShown() == True:
            return
        self.panel_resume.Show(etat)
        self.window_D.Layout()
        self.Refresh()

    def AfficheLabelSelection(self, etat=True):
        if etat == True and self.label_selection.IsShown() == True:
            return
        self.label_selection.Show(etat)
        self.window_D.Layout()
        self.Refresh()

    def MAJpanel(self, listeElements=[]):
        if self.init == False:
            self.InitPage()
        if "listCtrl_personnes" in listeElements or listeElements == []:
            self.listCtrl_personnes.MAJ()
            self.panel_dossiers.tree_ctrl_problemes.MAJ_treeCtrl()
            wx.CallAfter(self.AjusterColonnes)
            if self.listCtrl_personnes.GetNbrePersonnes() == 0:
                self.AffichePanelResume(False)

    def OnBoutonCourrier(self, event):
        self.listCtrl_personnes.CourrierPublipostage(mode='multiple')

    def OnBoutonImprimer(self, event):
        self.listCtrl_personnes.Imprimer()

    def OnBoutonExportTexte(self, event):
        self.listCtrl_personnes.ExportTexte()

    def OnBoutonExportExcel(self, event):
        self.listCtrl_personnes.ExportExcel()


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent

        self.SetDescriptiveText(_(u"Rechercher un individu"))
        self.ShowSearchButton(True)

        self.listView = self.GetParent().GetGrandParent().listCtrl_personnes
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))

        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_PNG))

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche(self.GetValue())

    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche(self.GetValue())

    def OnDoSearch(self, evt):
        self.Recherche(self.GetValue())

    def Recherche(self, txtSearch):
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.statusbar = self.CreateStatusBar(2, 0)
        self.statusbar.SetStatusWidths([360, -1])
        panel = PanelPersonnes(self)
        panel.InitPage()
        self.SetTitle(_(u"Panel Présences"))
        self.SetSize((1100, 800))
        self.Centre()


if __name__ == "__main__":
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
