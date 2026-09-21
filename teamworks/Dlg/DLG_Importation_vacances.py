#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Importation des vacances scolaires depuis la source officielle."""

import datetime
import threading

import wx
import wx.lib.agw.hyperlink as Hyperlink

import Chemins
import GestionDB
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Bouton_image
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn
from Utils import UTILS_Calendrier_scolaire_officiel
from Utils import UTILS_Interface
from Utils import UTILS_Parametres
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


class Track(object):
    def __init__(self, vacance):
        self.nom = vacance.nom
        self.annee = vacance.annee
        self.annee_scolaire = vacance.annee_scolaire
        self.date_debut = vacance.date_debut
        self.date_fin = vacance.date_fin
        self.zone = vacance.zone
        self.academie = vacance.academie
        self.population = vacance.population


class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.owner = kwds.pop("owner")
        self.zone = None
        self.donnees = []
        self._charger_vacances_existantes()
        FastObjectListView.__init__(self, *args, **kwds)

    @staticmethod
    def _date_texte(value):
        if isinstance(value, datetime.datetime):
            value = value.date()
        if isinstance(value, datetime.date):
            return value.isoformat()
        return str(value or "")[:10]

    @classmethod
    def _cle(cls, nom, date_debut, date_fin):
        return (
            str(nom or "").strip().casefold(),
            cls._date_texte(date_debut),
            cls._date_texte(date_fin),
        )

    def _charger_vacances_existantes(self):
        DB = GestionDB.DB()
        try:
            DB.ExecuterReq(
                """SELECT IDperiode, nom, annee, date_debut, date_fin
                FROM periodes_vacances ORDER BY date_debut;"""
            )
            lignes = DB.ResultatReq()
        finally:
            DB.Close()

        self.vacances_existantes = {
            self._cle(nom, date_debut, date_fin)
            for _IDperiode, nom, _annee, date_debut, date_fin in lignes
        }

    def SetPeriodes(self, zone, periodes):
        self.zone = zone
        self.donnees = [
            Track(vacance)
            for vacance in periodes
            if self._cle(vacance.nom, vacance.date_debut, vacance.date_fin)
            not in self.vacances_existantes
        ]
        self.InitObjectListView()
        self.CocheSuggestions()
        self.DefileDernier()

    def Vider(self):
        self.donnees = []
        self.InitObjectListView()

    def InitObjectListView(self):
        self.oddRowsBackColor = UTILS_Interface.GetValeur(
            "couleur_tres_claire", wx.Colour(240, 251, 237)
        )
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateDate(date):
            listeMois = (
                _(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"),
                _(u"mai"), _(u"juin"), _(u"juillet"), _(u"août"),
                _(u"septembre"), _(u"octobre"), _(u"novembre"), _(u"décembre"),
            )
            listeJours = (
                _(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"),
                _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"),
            )
            return "%s %d %s %d" % (
                listeJours[date.weekday()],
                date.day,
                listeMois[date.month - 1],
                date.year,
            )

        self.SetColumns(
            [
                ColumnDefn(_(u"Année"), "left", 65, "annee"),
                ColumnDefn(_(u"Nom"), "left", 150, "nom"),
                ColumnDefn(_(u"Date de début"), "left", 190, "date_debut", stringConverter=FormateDate),
                ColumnDefn(_(u"Date de fin"), "left", 190, "date_fin", stringConverter=FormateDate),
            ]
        )
        self.CreateCheckStateColumn(0)
        self.SetEmptyListMsg(_(u"Aucune nouvelle période de vacances"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[2])
        self.SetObjects(self.donnees)

    def CocheTout(self, event=None):
        for track in self.donnees:
            self.Check(track)
            self.RefreshObject(track)

    def CocheRien(self, event=None):
        for track in self.donnees:
            self.Uncheck(track)
            self.RefreshObject(track)

    def CocheSuggestions(self):
        aujourdhui = datetime.date.today()
        nbre = 0
        for track in self.donnees:
            if track.date_fin >= aujourdhui:
                self.Check(track)
                self.RefreshObject(track)
                nbre += 1
            else:
                self.Uncheck(track)

        if nbre == 0:
            texte = _(u"Aucune nouvelle période actuelle ou future n'est proposée.")
        elif nbre == 1:
            texte = _(u"Teamworks vous suggère d'importer 1 période de vacances.")
        else:
            texte = _(u"Teamworks vous suggère d'importer %d périodes de vacances.") % nbre
        self.SetLabelPeriodes(texte)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

    def SetLabelPeriodes(self, texte=""):
        self.owner.SetLabelPeriodes(texte)


class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)

    def OnLeftLink(self, event):
        if self.URL == "tout":
            self.parent.ctrl_periodes.CocheTout()
        elif self.URL == "rien":
            self.parent.ctrl_periodes.CocheRien()
        elif self.URL == "suggestions":
            self.parent.ctrl_periodes.CocheSuggestions()
        self.UpdateLink()


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self._generation_chargement = 0
        self._ferme = False
        self._chargement_en_cours = False

        intro = _(
            u"Importez les périodes publiées par le ministère de l'Éducation nationale. "
            u"Sélectionnez votre zone puis cochez les périodes à importer."
        )
        titre = _(u"Importation de périodes de vacances")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(
            self,
            titre=titre,
            texte=intro,
            hauteurHtml=30,
            nomImage=Chemins.GetStaticPath("Images/32x32/Telecharger.png"),
        )

        self.box_zone_staticbox = wx.StaticBox(self, -1, _(u"1. Sélectionnez votre zone"))
        self.label_zone = wx.StaticText(self.box_zone_staticbox, -1, _(u"Zone géographique :"))
        self.ctrl_zone = wx.Choice(
            self.box_zone_staticbox, -1, choices=[u"Zone A", u"Zone B", u"Zone C"]
        )

        self.box_periodes_staticbox = wx.StaticBox(self, -1, _(u"2. Cochez les périodes à importer"))
        self.label_periodes = wx.StaticText(
            self.box_periodes_staticbox, -1, _(u"Sélectionnez une zone...")
        )

        self.ctrl_periodes = ListView(
            self.box_periodes_staticbox,
            owner=self,
            id=-1,
            style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.ctrl_periodes.Vider()

        self.hyper_tout = Hyperlien(
            self.box_periodes_staticbox,
            label=_(u"Tout sélectionner"),
            infobulle=_(u"Cliquez ici pour tout sélectionner"),
            URL="tout",
        )
        self.label_separation_1 = wx.StaticText(self.box_periodes_staticbox, -1, u" | ")
        self.hyper_rien = Hyperlien(
            self.box_periodes_staticbox,
            label=_(u"Tout désélectionner"),
            infobulle=_(u"Cliquez ici pour tout désélectionner"),
            URL="rien",
        )
        self.label_separation_2 = wx.StaticText(self.box_periodes_staticbox, -1, u" | ")
        self.hyper_suggestions = Hyperlien(
            self.box_periodes_staticbox,
            label=_(u"Sélectionner les suggestions"),
            infobulle=_(u"Cliquez ici pour sélectionner uniquement les suggestions"),
            URL="suggestions",
        )

        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png")
        )
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Importer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fleche_bas.png")
        )
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png")
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHOICE, self.OnChoixZone, self.ctrl_zone)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        zone = UTILS_Parametres.Parametres(
            mode="get", categorie="vacances", nom="zone", valeur="A"
        )
        self.SetZone(zone, charger=False)
        self.ChargerZone()

    def __set_properties(self):
        self.ctrl_zone.SetToolTip(wx.ToolTip(_(u"Sélectionnez une zone")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour importer les périodes sélectionnées")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour annuler")))
        UTILS_Styles.ApplyWindowProfile(self, "standard")

    def __do_layout(self):
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")

        base = wx.BoxSizer(wx.VERTICAL)
        base.Add(self.ctrl_bandeau, 0, wx.EXPAND)

        box_zone = wx.StaticBoxSizer(self.box_zone_staticbox, wx.VERTICAL)
        ligne_zone = wx.BoxSizer(wx.HORIZONTAL)
        ligne_zone.Add(self.label_zone, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, gap)
        ligne_zone.Add(self.ctrl_zone, 1)
        box_zone.Add(ligne_zone, 0, wx.ALL | wx.EXPAND, padding)
        base.Add(box_zone, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, padding)

        box_periodes = wx.StaticBoxSizer(self.box_periodes_staticbox, wx.VERTICAL)
        box_periodes.Add(self.label_periodes, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, padding)
        box_periodes.Add(self.ctrl_periodes, 1, wx.ALL | wx.EXPAND, padding)

        commandes = wx.BoxSizer(wx.HORIZONTAL)
        commandes.Add(self.hyper_tout, 0)
        commandes.Add(self.label_separation_1, 0)
        commandes.Add(self.hyper_rien, 0)
        commandes.Add(self.label_separation_2, 0)
        commandes.Add(self.hyper_suggestions, 0)
        box_periodes.Add(commandes, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        base.Add(box_periodes, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, padding)

        boutons = wx.BoxSizer(wx.HORIZONTAL)
        boutons.Add(self.bouton_aide, 0)
        boutons.AddStretchSpacer(1)
        boutons.Add(self.bouton_ok, 0, wx.RIGHT, gap)
        boutons.Add(self.bouton_annuler, 0)
        base.Add(boutons, 0, wx.ALL | wx.EXPAND, padding)

        self.SetSizer(base)
        self.Layout()
        self.CentreOnParent()

    def GetZone(self):
        selection = self.ctrl_zone.GetSelection()
        if selection not in (0, 1, 2):
            return "A"
        return ("A", "B", "C")[selection]

    def SetZone(self, zone="A", charger=True):
        zone = str(zone or "A").upper()
        try:
            index = ("A", "B", "C").index(zone)
        except ValueError:
            index = 0
        self.ctrl_zone.SetSelection(index)
        if charger:
            self.ChargerZone()

    def OnChoixZone(self, event=None):
        self.ChargerZone()
        if event is not None:
            event.Skip()

    def ChargerZone(self):
        if self._ferme:
            return
        zone = self.GetZone()
        self._generation_chargement += 1
        generation = self._generation_chargement
        self._chargement_en_cours = True
        self.bouton_ok.Enable(False)
        self.SetLabelPeriodes(_(u"Chargement du calendrier officiel pour la zone %s...") % zone)
        self.ctrl_periodes.Vider()

        thread = threading.Thread(
            target=self._charger_zone_worker,
            args=(generation, zone),
            name="teamworks-calendrier-scolaire-%s" % zone,
            daemon=True,
        )
        thread.start()

    def _charger_zone_worker(self, generation, zone):
        try:
            resultat = UTILS_Calendrier_scolaire_officiel.charger_vacances(zone)
            erreur = None
        except Exception as err:
            resultat = None
            erreur = err
        wx.CallAfter(self._terminer_chargement, generation, zone, resultat, erreur)

    def _terminer_chargement(self, generation, zone, resultat, erreur):
        if self._ferme or generation != self._generation_chargement:
            return
        self._chargement_en_cours = False
        if erreur is not None:
            self.SetLabelPeriodes(_(u"Le calendrier officiel n'est pas disponible actuellement."))
            wx.MessageBox(
                _(u"Impossible de charger les vacances scolaires officielles pour la zone %s.\n\n%s")
                % (zone, erreur),
                _(u"Calendrier scolaire indisponible"),
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
            return

        self.ctrl_periodes.SetPeriodes(zone, resultat.vacances)
        self.bouton_ok.Enable(bool(self.ctrl_periodes.donnees))
        if resultat.avertissement:
            self.bouton_ok.SetToolTip(
                wx.ToolTip(
                    _(u"Les données proviennent du calendrier iCal officiel car l'API principale était indisponible.")
                )
            )

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Vacances")

    def OnBoutonOk(self, event):
        if self._chargement_en_cours:
            return
        tracks = self.ctrl_periodes.GetTracksCoches()
        if not tracks:
            wx.MessageBox(
                _(u"Vous n'avez coché aucune période à importer !"),
                _(u"Erreur"),
                wx.OK | wx.ICON_EXCLAMATION,
                parent=self,
            )
            return

        donnees = [
            (track.nom, track.annee, str(track.date_debut), str(track.date_fin))
            for track in tracks
        ]
        DB = GestionDB.DB()
        try:
            DB.Executermany(
                "INSERT INTO periodes_vacances (nom, annee, date_debut, date_fin) VALUES (?, ?, ?, ?)",
                donnees,
                commit=True,
            )
        finally:
            DB.Close()

        self.MemoriseZone()
        self._ferme = True
        self._generation_chargement += 1
        self.EndModal(wx.ID_OK)

    def OnBoutonAnnuler(self, event):
        self._fermer(wx.ID_CANCEL)

    def OnClose(self, event):
        self._fermer(wx.ID_CANCEL)

    def _fermer(self, code):
        if self._ferme:
            return
        self._ferme = True
        self._generation_chargement += 1
        self.MemoriseZone()
        if self.IsModal():
            self.EndModal(code)
        else:
            self.Destroy()

    def MemoriseZone(self):
        UTILS_Parametres.Parametres(
            mode="set", categorie="vacances", nom="zone", valeur=self.GetZone()
        )

    def SetLabelPeriodes(self, texte=u""):
        self.label_periodes.SetLabel(texte)
        self.label_periodes.Wrap(max(240, self.GetClientSize().GetWidth() - 80))


if __name__ == "__main__":
    app = wx.App(0)
    dialog = Dialog(None)
    app.SetTopWindow(dialog)
    dialog.ShowModal()
    dialog.Destroy()
    app.MainLoop()
