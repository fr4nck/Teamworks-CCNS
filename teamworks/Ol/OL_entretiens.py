#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ObjectListView Entretiens modernisé : avis textuels et verrouillage explicite."""

import datetime
import wx

from Ctrl import CTRL_Bouton_image, CTRL_Section, CTRL_Texte
from Ol import OL_entretiens_core as CORE
from ObjectListView import ColumnDefn
from Utils import UTILS_Dates, UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


NOMS_CANDIDATS = CORE.NOMS_CANDIDATS
NOMS_PERSONNES = CORE.NOMS_PERSONNES
LISTE_COLONNES_1 = CORE.LISTE_COLONNES_1
LISTE_COLONNES_2 = CORE.LISTE_COLONNES_2
LISTE_COLONNES_3 = CORE.LISTE_COLONNES_3

AVIS_LABELS = {
    0: _(u"Avis inconnu"),
    1: _(u"Pas convaincant"),
    2: _(u"Mitigé"),
    3: _(u"Bien"),
    4: _(u"Très bien"),
    999: _(u"Avis verrouillé"),
}


class Track(CORE.Track):
    def __init__(self, donnees):
        CORE.Track.__init__(self, donnees)
        if self.IDpersonne not in (None, 0) and self.nom_candidat:
            self.nom_candidat = u"%s · %s" % (self.nom_candidat, _(u"salarié"))
            self.date_heure_nom = self.date_heure + ";" + self.nom_candidat


class ListView(CORE.ListView):
    def __init__(self, *args, **kwds):
        self.IDcandidat = kwds.pop("IDcandidat", None)
        self.IDpersonne = kwds.pop("IDpersonne", None)
        self.modeAffichage = kwds.pop("modeAffichage", None)
        self.colorerSalaries = kwds.pop("colorerSalaries", True)
        self.prochainsEntretiens = kwds.pop("prochainsEntretiens", False)
        self.afficheHyperlink = kwds.pop("afficheHyperlink", True)
        self.selectionID = None
        self.selectionTrack = None
        self.presents = False
        self.donnees = []
        self.criteres = ""
        self.listeFiltres = []
        self.itemSelected = False

        CORE.ObjectListView.__init__(self, *args, **kwds)
        if self.modeAffichage in (None, "sans_nom"):
            self.listeColonnes = LISTE_COLONNES_1
        elif self.modeAffichage == "avec_nom":
            self.listeColonnes = LISTE_COLONNES_2
        else:
            self.listeColonnes = LISTE_COLONNES_3
        self.listeColonnesOriginale = list(self.listeColonnes)

        if CORE.VERROUILLAGE is None:
            password = CORE.FonctionsPerso.Parametres(
                mode="get", categorie="recrutement", nom="password_entretien", valeur=""
            )
            CORE.VERROUILLAGE = bool(password)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def GetTracks(self):
        listeID = None
        self.criteres = ""
        if self.IDcandidat not in (None, 0):
            self.criteres = "WHERE IDcandidat=%d" % self.IDcandidat
        if self.IDpersonne not in (None, 0):
            self.criteres = "WHERE IDpersonne=%d" % self.IDpersonne
        if self.prochainsEntretiens:
            self.criteres = "WHERE date>='%s'" % datetime.date.today()
        if self.listeFiltres:
            listeID, criteres = self.GetListeFiltres(self.listeFiltres)
            if criteres:
                self.criteres = "WHERE " + criteres if not self.criteres else self.criteres + " AND " + criteres

        DB = CORE.GestionDB.DB()
        req = """SELECT IDentretien, IDcandidat, date, heure, avis, remarques, IDpersonne
        FROM entretiens %s ORDER BY date, heure;""" % self.criteres
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()
        objets = []
        for row in rows:
            if listeID is not None and row[0] not in listeID:
                continue
            track = Track(row)
            if track.nom_candidat:
                objets.append(track)
                if self.selectionID == row[0]:
                    self.selectionTrack = track
        return objets

    def InitObjectListView(self):
        self.oddRowsBackColor = UTILS_Interface.GetToken("surface_container_lowest")
        self.evenRowsBackColor = UTILS_Interface.GetToken("surface_container_low")
        self.useExpansionColumn = True
        self.rowFormatter = None

        def format_avis(value):
            return AVIS_LABELS.get(value, "")

        def format_heure(value):
            return (value or "").replace(":", "h")

        def format_date_heure_nom(value):
            try:
                date, heure, nom = value.split(";", 2)
                return u"%s %s · %s" % (UTILS_Dates.DateEngFr(date), format_heure(heure), nom)
            except Exception:
                return value or ""

        colonnes = []
        for labelCol, alignement, largeur, nomChamp, args, description, affiche, ordre in sorted(
            self.listeColonnes, key=lambda item: item[7]
        ):
            if not affiche:
                continue
            kwargs = {}
            if args == "date":
                kwargs["stringConverter"] = UTILS_Dates.DateEngFr
            elif args == "heure":
                kwargs["stringConverter"] = format_heure
            elif args == "date_heure_nom":
                kwargs["stringConverter"] = format_date_heure_nom
            elif args == "image_avis":
                kwargs["stringConverter"] = format_avis
            colonnes.append(ColumnDefn(labelCol, alignement, largeur, nomChamp, **kwargs))
        self.SetColumns(colonnes)
        if len(self.columns) > 1:
            self.SetSortColumn(self.columns[1])
        self.SetEmptyListMsg(_(u"Aucun entretien"))
        self.SetEmptyListMsgFont(UTILS_Styles.GetFont("body-secondary"))
        self.SetObjects(self.donnees)

    def MAJ(self, IDcandidat=None, presents=None):
        if IDcandidat is not None:
            self.selectionID = IDcandidat
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        if presents is not None:
            self.presents = presents
        self.InitModel()
        self.InitObjectListView()
        if self.selectionTrack is not None:
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        self.SetLabelSelection()

    def SetLabelHyperlink(self):
        # Compatibilité : l'état de verrouillage n'est plus peint dans la liste.
        return

    def OnContextMenu(self, event):
        selection = bool(self.Selection())
        menu = wx.Menu()

        def ajouter(label, handler, enabled=True):
            identifiant = wx.NewIdRef()
            item = menu.Append(identifiant, label)
            item.Enable(enabled)
            self.Bind(wx.EVT_MENU, handler, id=identifiant)

        ajouter(_(u"Ajouter"), self.Menu_Ajouter)
        menu.AppendSeparator()
        ajouter(_(u"Modifier"), self.Menu_Modifier, selection)
        ajouter(_(u"Supprimer"), self.Menu_Supprimer, selection)
        menu.AppendSeparator()
        ajouter(
            _(u"Déverrouiller les avis") if CORE.VERROUILLAGE else _(u"Verrouiller les avis"),
            self.Menu_Verrouillage,
        )
        menu.AppendSeparator()
        ajouter(_(u"Rechercher / filtrer"), self.Menu_Rechercher)
        ajouter(_(u"Afficher tout"), self.Menu_AfficherTout)
        ajouter(_(u"Colonnes et options"), self.Menu_Options)
        menu.AppendSeparator()
        ajouter(_(u"Imprimer"), self.MenuImprimer)
        ajouter(_(u"Exporter en texte"), self.MenuExportTexte)
        ajouter(_(u"Exporter vers Excel"), self.MenuExportExcel)
        menu.AppendSeparator()
        ajouter(_(u"Aide"), self.Menu_Aide)
        self.PopupMenu(menu)
        menu.Destroy()

    def GestionVerrouillage(self, MAJ=False):
        password = CORE.FonctionsPerso.Parametres(
            mode="get", categorie="recrutement", nom="password_entretien", valeur=""
        )
        if CORE.VERROUILLAGE:
            dlg = SaisiePassword(self)
            if dlg.ShowModal() == wx.ID_OK:
                if dlg.GetPassword() == password:
                    CORE.VERROUILLAGE = False
                else:
                    wx.MessageBox(
                        _(u"Votre mot de passe est erroné."),
                        _(u"Mot de passe erroné"),
                        wx.OK | wx.ICON_ERROR,
                    )
            dlg.Destroy()
        else:
            if not password:
                from Dlg import DLG_Saisie_password_dialog
                texte = _(
                    u"Vous pouvez protéger l'accès aux avis et commentaires des entretiens. "
                    u"Saisissez le mot de passe souhaité à deux reprises."
                )
                dlg = DLG_Saisie_password_dialog.MyDialog(self, texteIntro=texte)
                if dlg.ShowModal() == wx.ID_OK:
                    pwd = dlg.GetPassword()
                    CORE.FonctionsPerso.Parametres(
                        mode="set", categorie="recrutement", nom="password_entretien", valeur=pwd
                    )
                    CORE.VERROUILLAGE = True
                dlg.Destroy()
            else:
                CORE.VERROUILLAGE = True
        if MAJ:
            self.MAJ()
            try:
                recrutement = self
                while recrutement is not None and recrutement.GetName() != "Recrutement":
                    recrutement = recrutement.GetParent()
                if recrutement is not None:
                    recrutement.MAJapresVerrouillage(OL_gadget=True, OL_principal=True, OL_resume=True)
            except Exception:
                pass


class SaisiePassword(wx.Dialog):
    def __init__(self, parent, id=-1, title=_(u"Déverrouiller les avis")):
        wx.Dialog.__init__(self, parent, id, title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        self.section = CTRL_Section.Section(
            self,
            titre=_(u"Avis protégés"),
            niveau=2,
            description=_(u"Saisissez le mot de passe pour afficher les avis et commentaires jusqu'à la fermeture du logiciel."),
        )
        contenu = self.section.GetContentPanel()
        self.label_password = CTRL_Texte.Label(contenu, _(u"Mot de passe"))
        self.text_password = wx.TextCtrl(contenu, -1, "", style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        gap = UTILS_Styles.GetLayoutSpacing("field_gap")
        cs = wx.BoxSizer(wx.VERTICAL)
        cs.Add(self.label_password, 0, wx.EXPAND)
        cs.AddSpacer(gap)
        cs.Add(self.text_password, 0, wx.EXPAND)
        contenu.SetSizer(cs)
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, id=wx.ID_OK, texte=_(u"Déverrouiller"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"))
        padding = UTILS_Styles.GetLayoutSpacing("dialog_padding")
        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.RIGHT, gap)
        actions.Add(self.bouton_annuler, 0)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.section, 1, wx.EXPAND | wx.ALL, padding)
        sizer.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, padding)
        self.SetSizer(sizer)
        self.text_password.Bind(wx.EVT_TEXT_ENTER, lambda evt: self.EndModal(wx.ID_OK))
        UTILS_Styles.ApplyWindowProfile(self, "compact")
        self.text_password.SetFocus()

    def GetPassword(self):
        return self.text_password.GetValue()


# Réexports utiles aux impressions et aux appels historiques.
DateEngFr = CORE.DateEngFr
Impression = CORE.Impression


if __name__ == "__main__":
    app = wx.App(0)
    frame = wx.Frame(None, title=_(u"Entretiens"))
    panel = wx.Panel(frame)
    ctrl = ListView(panel, id=-1, modeAffichage="avec_nom", style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
    ctrl.MAJ()
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(ctrl, 1, wx.EXPAND)
    panel.SetSizer(sizer)
    frame.SetSize((1000, 650))
    frame.Show()
    app.MainLoop()
