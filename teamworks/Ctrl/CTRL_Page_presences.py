#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Présences d'une personne : page, saisie multi-dates et application de modèle."""

import datetime
import wx
import six
import wx.lib.mixins.listctrl as listmix

import Chemins
import FonctionsPerso
import GestionDB
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Calendrier_tw
from Ctrl import CTRL_Presences_common
from Ctrl import CTRL_Section
from Ctrl import CTRL_Texte
from Dlg import DLG_Application_modele
from Dlg import DLG_Saisie_presence
from Utils import UTILS_Adaptations
from Utils import UTILS_Colonnes
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


class Panel(wx.Panel):
    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Panel.__init__(
            self,
            parent,
            id,
            name="panel_pagePresences",
            style=wx.TAB_TRAVERSAL,
        )
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.section = CTRL_Section.Section(
            self,
            titre=_(u"Présences"),
            niveau=2,
        )
        contenu = self.section.GetContentPanel()

        self.bouton_ajouter = CTRL_Bouton_image.CTRL(
            contenu,
            texte=_(u"Ajouter"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Ajouter.png"),
        )
        self.bouton_modifier = CTRL_Bouton_image.CTRL(
            contenu,
            texte=_(u"Modifier"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Modifier.png"),
        )
        self.bouton_supprimer = CTRL_Bouton_image.CTRL(
            contenu,
            texte=_(u"Supprimer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Supprimer.png"),
        )
        self.bouton_imprimer = CTRL_Bouton_image.CTRL(
            contenu,
            texte=_(u"Imprimer"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Imprimante.png"),
        )
        self.bouton_stats = CTRL_Bouton_image.CTRL(
            contenu,
            texte=_(u"Statistiques"),
        )
        self.bouton_modele = CTRL_Bouton_image.CTRL(
            contenu,
            texte=_(u"Appliquer un modèle"),
        )

        self.barreRecherche = BarreRecherche(contenu, owner=self)
        self.label_resume = CTRL_Texte.BodySecondary(contenu, u"")
        self.listCtrl = ListCtrl(contenu, IDpersonne=self.IDpersonne, owner=self)

        self.__set_properties()
        self.__do_layout(contenu)

    def __set_properties(self):
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Saisir une nouvelle présence")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Modifier la présence sélectionnée")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Supprimer la présence sélectionnée")))
        self.bouton_imprimer.SetToolTip(wx.ToolTip(_(u"Imprimer une feuille d'heures")))
        self.bouton_stats.SetToolTip(wx.ToolTip(_(u"Afficher les statistiques de présences")))
        self.bouton_modele.SetToolTip(wx.ToolTip(_(u"Appliquer un modèle de présences")))
        self.barreRecherche.SetToolTip(
            wx.ToolTip(
                _(u"Rechercher une date, une période de vacances, un mois, une année ou un intitulé")
            )
        )

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjout, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModif, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSuppr, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonStats, self.bouton_stats)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModele, self.bouton_modele)

    def __do_layout(self, contenu):
        gap = UTILS_Styles.GetLayoutSpacing("toolbar_gap")
        field_gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")

        actions = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (
            self.bouton_ajouter,
            self.bouton_modifier,
            self.bouton_supprimer,
            self.bouton_imprimer,
            self.bouton_stats,
            self.bouton_modele,
        ):
            actions.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, gap)

        contenu_sizer = wx.BoxSizer(wx.VERTICAL)
        contenu_sizer.Add(actions, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        contenu_sizer.Add(self.barreRecherche, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        contenu_sizer.Add(self.label_resume, 0, wx.EXPAND | wx.BOTTOM, field_gap)
        contenu_sizer.Add(self.listCtrl, 1, wx.EXPAND)
        contenu.SetSizer(contenu_sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.section, 1, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(sizer)

    def SetResume(self, texte):
        self.label_resume.SetLabel(texte)

    def OnBoutonAjout(self, event):
        self.Ajouter()
        event.Skip()

    def Ajouter(self):
        dlg = Dialog_saisie(self, IDpersonne=self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()
        self.MAJpanel()

    def OnBoutonModif(self, event):
        self.Modifier()
        event.Skip()

    def Modifier(self):
        index = self.listCtrl.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner une présence à modifier dans la liste."),
                _(u"Information"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        IDpresence = int(self.listCtrl.getColumnText(index, 0))
        dlg = DLG_Saisie_presence.Dialog(self, IDmodif=IDpresence)
        # Le formulaire historique sait masquer ces groupes en mode fiche individuelle.
        try:
            dlg.panel.sizer_1.Hide(False)
            dlg.panel.sizer_donnees_staticbox.Hide()
            dlg.panel.grid_sizer_base.Layout()
        except Exception:
            pass
        UTILS_Styles.ApplyWindowProfile(dlg, "compact")
        dlg.ShowModal()
        dlg.Destroy()
        self.listCtrl.indexEnCours = index
        self.MAJpanel()

    def OnBoutonSuppr(self, event):
        self.Supprimer()

    def Supprimer(self):
        index = self.listCtrl.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner une présence à supprimer dans la liste."),
                _(u"Information"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        date = self.listCtrl.DateAfficheePourIndex(index)
        horaires = self.listCtrl.GetItem(index, 5).GetText()
        texte_presence = date + " : " + horaires
        dlg_confirm = wx.MessageDialog(
            self,
            six.text_type(
                _(u"Voulez-vous vraiment supprimer cette présence ?\n\n")
                + texte_presence
            ),
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlg_confirm.ShowModal()
        dlg_confirm.Destroy()
        if reponse != wx.ID_YES:
            return

        IDpresence = int(self.listCtrl.getColumnText(index, 0))
        DB = GestionDB.DB()
        DB.ReqDEL("presences", "IDpresence", IDpresence)
        DB.Close()

        self.listCtrl.indexEnCours = max(0, index - 1)
        self.MAJpanel()

    def OnBoutonImprimer(self, event):
        from Dlg import DLG_Impression_calendrier_annuel
        dlg = DLG_Impression_calendrier_annuel.MyDialog(
            self,
            IDpersonne=self.IDpersonne,
            autoriser_choix_personne=False,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonStats(self, event):
        top_window = wx.GetApp().GetTopWindow()
        try:
            top_window.SetStatusText(
                _(u"Chargement du module des statistiques en cours. Veuillez patienter...")
            )
        except Exception:
            pass
        try:
            from Dlg import DLG_Statistiques
            dlg = DLG_Statistiques.Dialog(
                self,
                listeDates=[],
                listePersonnes=[self.IDpersonne],
            )
            dlg.ShowModal()
            dlg.Destroy()
        except Exception as err:
            print("Erreur d'ouverture de la fenêtre Statistiques :", err)
        try:
            top_window.SetStatusText(u"")
        except Exception:
            pass

    def OnBoutonModele(self, event):
        self.AppliquerModele()
        event.Skip()

    def AppliquerModele(self):
        dlg = Dialog_application_modele(self, IDpersonne=self.IDpersonne)
        dlg.ShowModal()
        dlg.Destroy()
        self.MAJpanel()

    def MAJpanel(self):
        self.listCtrl.MAJListeCtrl()


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, owner=None):
        wx.SearchCtrl.__init__(self, parent, style=wx.TE_PROCESS_ENTER)
        self.owner = owner or parent
        self.SetDescriptiveText(
            _(u"Rechercher une date, des vacances, un mois, une année ou un intitulé…")
        )
        self.ShowSearchButton(True)
        self.ShowCancelButton(True)
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
        self.owner.listCtrl.Rechercher(txtSearch)


class Dialog_saisie(wx.Dialog):
    """Saisie d'une présence pour plusieurs dates depuis la fiche individuelle."""

    def __init__(self, parent, title=_(u"Saisie de présences"), IDpersonne=0):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title=title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.section_calendrier = CTRL_Section.Section(
            self,
            titre=_(u"Dates"),
            niveau=2,
        )
        contenu_calendrier = self.section_calendrier.GetContentPanel()
        self.calendrier = CTRL_Calendrier_tw.Panel(
            contenu_calendrier,
            afficheBoutonAnnuel=True,
            callbacksenddates=self.SendDates,
        )
        self.label_dates = CTRL_Texte.BodySecondary(
            contenu_calendrier,
            _(u"Aucune date sélectionnée"),
        )
        calendrier_sizer = wx.BoxSizer(wx.VERTICAL)
        calendrier_sizer.Add(self.calendrier, 1, wx.EXPAND)
        calendrier_sizer.Add(
            self.label_dates,
            0,
            wx.EXPAND | wx.TOP,
            UTILS_Styles.GetLayoutSpacing("field_gap"),
        )
        contenu_calendrier.SetSizer(calendrier_sizer)
        self.calendrier.calendrier.SelectJours([])

        self.panel_saisiePresences = DLG_Saisie_presence.Panel(self)
        try:
            self.panel_saisiePresences.sizer_1.Hide(False)
            self.panel_saisiePresences.sizer_donnees_staticbox.Hide()
            self.panel_saisiePresences.grid_sizer_base.Layout()
        except Exception:
            pass

        self.bouton_fermer = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CLOSE,
            texte=_(u"Fermer"),
        )
        self.Bind(wx.EVT_BUTTON, self.OnFermer, self.bouton_fermer)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.__do_layout()
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def __do_layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        contenu = wx.BoxSizer(wx.HORIZONTAL)
        contenu.Add(self.section_calendrier, 3, wx.EXPAND | wx.RIGHT, gap)
        contenu.Add(self.panel_saisiePresences, 2, wx.EXPAND)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_fermer, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(contenu, 1, wx.EXPAND | wx.ALL, page_gap)
        sizer.Add(
            actions,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        self.SetSizer(sizer)

    def OnClose(self, event):
        self.Fermer()

    def OnFermer(self, event):
        self.Fermer()

    def Fermer(self):
        self.parent.MAJpanel()
        self.EndModal(wx.ID_OK)

    def SendDates(self, listeDates=None):
        listeDates = list(listeDates or [])
        liste_donnees = [(self.IDpersonne, date) for date in listeDates]
        self.panel_saisiePresences.CreationDictDonnees(liste_donnees)
        nombre = len(listeDates)
        if nombre == 0:
            texte = _(u"Aucune date sélectionnée")
        elif nombre == 1:
            texte = _(u"1 date sélectionnée")
        else:
            texte = str(nombre) + _(u" dates sélectionnées")
        self.label_dates.SetLabel(texte)


class Dialog_application_modele(wx.Dialog):
    def __init__(self, parent, IDpersonne=0):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title=_(u"Application d'un modèle"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.selectionLignes = []
        self.selectionPersonnes = [IDpersonne]
        self.selectionDates = (None, None)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))

        self.section_calendrier = CTRL_Section.Section(
            self,
            titre=_(u"Dates"),
            niveau=2,
            description=_(u"Sélectionnez une ou plusieurs dates auxquelles appliquer le modèle."),
        )
        contenu_calendrier = self.section_calendrier.GetContentPanel()
        self.calendrier = CTRL_Calendrier_tw.Panel(
            contenu_calendrier,
            afficheBoutonAnnuel=True,
            callbacksenddates=self.SendDates,
        )
        self.label_dates = CTRL_Texte.BodySecondary(
            contenu_calendrier,
            _(u"Aucune date sélectionnée"),
        )
        calendrier_sizer = wx.BoxSizer(wx.VERTICAL)
        calendrier_sizer.Add(self.calendrier, 1, wx.EXPAND)
        calendrier_sizer.Add(
            self.label_dates,
            0,
            wx.EXPAND | wx.TOP,
            UTILS_Styles.GetLayoutSpacing("field_gap"),
        )
        contenu_calendrier.SetSizer(calendrier_sizer)
        self.calendrier.calendrier.SelectJours([])

        self.panel_applicModele = DLG_Application_modele.Panel(
            self,
            selectionPersonnes=self.selectionPersonnes,
        )
        try:
            self.panel_applicModele.list_ctrl_personnes.Show(False)
            self.panel_applicModele.label_personnes.Show(False)
            self.panel_applicModele.grid_sizer_manuel.Layout()
            self.panel_applicModele.sizer_parametres_staticbox.SetLabel(
                _(u"Choix de la période")
            )
        except Exception:
            pass

        self.__do_layout()
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def __do_layout(self):
        gap = UTILS_Styles.GetLayoutSpacing("section_gap")
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.section_calendrier, 3, wx.EXPAND | wx.RIGHT, gap)
        sizer.Add(self.panel_applicModele, 2, wx.EXPAND)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(sizer, 1, wx.EXPAND | wx.ALL, page_gap)
        self.SetSizer(principal)

    def Fermer(self):
        self.EndModal(wx.ID_CANCEL)

    def SendDates(self, listeDates=None):
        listeDates = sorted(list(listeDates or []))
        self.selectionLignes = [
            (self.IDpersonne, date) for date in listeDates
        ]
        if not listeDates:
            self.selectionDates = (None, None)
        else:
            self.selectionDates = (listeDates[0], listeDates[-1])

        self.panel_applicModele.selectionLignes = self.selectionLignes
        self.panel_applicModele.selectionPersonnes = self.selectionPersonnes
        self.panel_applicModele.selectionDates = self.selectionDates
        self.panel_applicModele.SetLabelRadio1()

        nombre = len(listeDates)
        if nombre == 0:
            texte = _(u"Aucune date sélectionnée")
        elif nombre == 1:
            texte = _(u"1 date sélectionnée")
        else:
            texte = str(nombre) + _(u" dates sélectionnées")
        self.label_dates.SetLabel(texte)


class ListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin):
    """Tableau des présences : couleurs métier exprimées en texte, chrome neutre."""

    def __init__(self, parent, IDpersonne=0, owner=None):
        wx.ListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.LC_VRULES | wx.BORDER_NONE,
        )
        self.IDpersonne = IDpersonne
        self.owner = owner or parent
        self.selection = None
        self.txtSearch = ""
        self.indexEnCours = 0
        self.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self.attr_date_alternee = wx.ItemAttr()
        self.attr_date_alternee.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_low")
        )

        self.Importation_categories()
        self.Importation_vacances()
        self.Remplissage()
        self.gestion_colonnes = UTILS_Colonnes.ColonnesFlexibles(
            self,
            extensibles=(3, 4, 7),
        )

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.indexEnCours = max(0, self.nbreLignes - 1)
        self.SetSelection(index=self.indexEnCours, selection=False)

    def Remplissage(self):
        self.Importation()
        self.nbreColonnes = 8
        colonnes = (
            (u"", 0),
            (_(u"attribut"), 0),
            (_(u"categorie"), 0),
            (_(u"Date"), 190),
            (_(u"Vacances"), 130),
            (_(u"Horaires"), 110),
            (_(u"Durée"), 90),
            (_(u"Intitulé"), 260),
        )
        for index, (titre, largeur) in enumerate(colonnes):
            align = wx.LIST_FORMAT_RIGHT if index in (5, 6) else wx.LIST_FORMAT_LEFT
            self.InsertColumn(index, titre, align)
            self.SetColumnWidth(index, largeur)

        self.itemDataMap = self.donnees
        self.itemIndexMap = list(self.donnees.keys())
        self.SetItemCount(self.nbreLignes)
        listmix.ColumnSorterMixin.__init__(self, self.nbreColonnes)
        self.SortListItems(3, 1)

    def Importation_categories(self):
        DB = GestionDB.DB()
        DB.ExecuterReq(
            "SELECT IDcategorie, nom_categorie, couleur FROM cat_presences;"
        )
        liste_categories = DB.ResultatReq()
        DB.Close()
        self.dictCategories = {
            IDcategorie: (nom_categorie, couleur)
            for IDcategorie, nom_categorie, couleur in liste_categories
        }

    def Importation_vacances(self):
        DB = GestionDB.DB()
        DB.ExecuterReq(
            "SELECT IDperiode, nom, annee, date_debut, date_fin FROM periodes_vacances;"
        )
        self.listeVacances = DB.ResultatReq()
        DB.Close()

    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT IDpresence, date, heure_debut, heure_fin, IDcategorie, intitule
        FROM presences WHERE IDpersonne=%d ORDER BY date, heure_debut;""" % self.IDpersonne
        DB.ExecuterReq(req)
        liste_presences = DB.ResultatReq()
        DB.Close()

        self.donnees = {}
        attribut = 0
        date_precedente = None
        index = 1
        recherche = FonctionsPerso.EnleveAccents(self.txtSearch).upper()

        for IDpresence, date, heure_debut, heure_fin, IDcategorie, intitule in liste_presences:
            horaires = self.FormateHeure(heure_debut) + "–" + self.FormateHeure(heure_fin)
            duree = self.CalculeDuree(heure_debut, heure_fin)
            categorie = self.dictCategories.get(IDcategorie, (_(u"Catégorie inconnue"), ""))[0]
            texte = categorie
            if intitule:
                texte += " — " + intitule

            vacances = ""
            for IDperiode, nom, annee, date_debut, date_fin in self.listeVacances:
                if date_debut <= date <= date_fin:
                    vacances = nom + " " + six.text_type(annee)
                    break

            if date_precedente != date:
                attribut = 1 - attribut

            if recherche:
                champs = (
                    date[8:10] + "/" + date[5:7] + "/" + date[0:4],
                    self.FormateDate(date),
                    vacances,
                    texte,
                )
                valide = any(
                    recherche in FonctionsPerso.EnleveAccents(champ).upper()
                    for champ in champs
                )
            else:
                valide = True

            if valide:
                self.donnees[index] = (
                    IDpresence,
                    attribut,
                    IDcategorie,
                    date,
                    vacances,
                    horaires,
                    duree,
                    texte,
                )
                date_precedente = date
                index += 1

        self.nbreLignes = len(self.donnees)
        if not self.txtSearch:
            if self.nbreLignes == 0:
                resume = _(u"Aucune présence")
            elif self.nbreLignes == 1:
                resume = _(u"1 présence")
            else:
                resume = str(self.nbreLignes) + _(u" présences")
        else:
            if self.nbreLignes == 0:
                resume = _(u"Aucune présence trouvée pour « %s »") % self.txtSearch
            elif self.nbreLignes == 1:
                resume = _(u"1 présence trouvée pour « %s »") % self.txtSearch
            else:
                resume = _("%d présences trouvées pour « %s »") % (
                    self.nbreLignes,
                    self.txtSearch,
                )
        if hasattr(self.owner, "SetResume"):
            self.owner.SetResume(resume)

    def FormateHeure(self, heure):
        heures = int(heure[:2])
        minutes = int(heure[3:])
        return "%dh%02d" % (heures, minutes)

    def FormateDate(self, date_courte):
        annee = date_courte[:4]
        mois = date_courte[5:7]
        jour = date_courte[8:10]
        date = datetime.date(int(annee), int(mois), int(jour))
        liste_jours = (
            _(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"),
            _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"),
        )
        liste_mois = (
            _(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"),
            _(u"mai"), _(u"juin"), _(u"juillet"), _(u"août"),
            _(u"septembre"), _(u"octobre"), _(u"novembre"), _(u"décembre"),
        )
        return "%s %d %s %d" % (
            liste_jours[date.weekday()],
            date.day,
            liste_mois[date.month - 1],
            date.year,
        )

    def CalculeDuree(self, heureMin, heureMax):
        debut = datetime.timedelta(
            hours=int(heureMin[:2]),
            minutes=int(heureMin[3:]),
        )
        fin = datetime.timedelta(
            hours=int(heureMax[:2]),
            minutes=int(heureMax[3:]),
        )
        total_minutes = (fin - debut).seconds // 60
        heures, minutes = divmod(total_minutes, 60)
        return "%dh%02d" % (heures, minutes)

    def MAJListeCtrl(self):
        self.ClearAll()
        self.Remplissage()
        if hasattr(self, "gestion_colonnes"):
            self.gestion_colonnes.ReinitialiserReference()
        self.SetSelection(self.indexEnCours)

    def SetSelection(self, index=0, selection=True):
        try:
            self.EnsureVisible(index)
            if selection:
                self.Select(index)
        except Exception:
            pass

    def DateAfficheePourIndex(self, index):
        """Retrouve la date complète même si les lignes suivantes l'escamotent visuellement."""
        while index >= 0:
            valeur = self.GetItem(index, 3).GetText()
            if valeur:
                return valeur
            index -= 1
        return _(u"Date inconnue")

    def OnItemActivated(self, event):
        self.owner.Modifier()

    def getColumnText(self, index, col):
        return self.GetItem(index, col).GetText()

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        valeur = six.text_type(self.itemDataMap[index][col])
        if col == 3:
            date_str = self.FormateDate(valeur)
            if index > 1:
                date_precedente = six.text_type(self.itemDataMap[index - 1][col])
                if valeur == date_precedente:
                    return ""
            return date_str
        return valeur

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        index = self.itemIndexMap[item]
        return self.attr_date_alternee if str(self.itemDataMap[index][1]) == "1" else None

    def SortItems(self, sorter=FonctionsPerso.cmp):
        items = list(self.itemDataMap.keys())
        self.itemIndexMap = FonctionsPerso.SortItems(items, sorter)
        self.Refresh()

    def GetListCtrl(self):
        return self

    def GetSortImages(self):
        return (-1, -1)

    def OnContextMenu(self, event):
        if self.GetFirstSelected() == -1:
            return False
        menu = UTILS_Adaptations.Menu()
        menu.Append(10, _(u"Ajouter"))
        menu.Append(20, _(u"Modifier"))
        menu.Append(30, _(u"Supprimer"))
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)
        self.Bind(wx.EVT_MENU, self.Menu_Modifier, id=20)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)
        self.PopupMenu(menu)
        menu.Destroy()

    def Menu_Ajouter(self, event):
        self.owner.Ajouter()

    def Menu_Modifier(self, event):
        self.owner.Modifier()

    def Menu_Supprimer(self, event):
        self.owner.Supprimer()

    def Rechercher(self, txtSearch):
        self.txtSearch = txtSearch
        self.MAJListeCtrl()


class Dialog(wx.Dialog):
    def __init__(self, parent, title=_(u"Liste de présences"), IDpersonne=1):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.parent = parent
        self.IDpersonne = IDpersonne
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.panel_contenu = Panel(self, IDpersonne=IDpersonne)
        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Aide"),
            cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"),
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_OK,
            texte=_(u"Fermer"),
        )
        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)

    def __set_properties(self):
        try:
            DB = GestionDB.DB()
            DB.ExecuterReq(
                "SELECT nom, prenom FROM personnes WHERE IDpersonne=%d;"
                % self.IDpersonne
            )
            identite = DB.ResultatReq()[0]
            DB.Close()
            self.SetTitle(
                _(u"Liste des présences de ") + identite[1] + " " + identite[0]
            )
        except Exception:
            self.SetTitle(_(u"Liste des présences"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Fermer cette fenêtre")))
        UTILS_Styles.ApplyWindowProfile(self, "wide")

    def __do_layout(self):
        page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel_contenu, 1, wx.EXPAND)
        sizer.Add(
            actions,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            page_gap,
        )
        self.SetSizer(sizer)

    def Onbouton_aide(self, event):
        from Utils import UTILS_Aide
        try:
            UTILS_Aide.Aide("Lespresences")
        except Exception:
            pass

    def Onbouton_ok(self, event):
        panel_presences = CTRL_Presences_common.find_presences_panel(self)
        if panel_presences is not None:
            panel_presences.MAJpanel(reinitSelectionPersonnes=True)
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, "")
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
