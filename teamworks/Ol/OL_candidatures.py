#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ObjectListView Candidatures modernisé sans pictogrammes décoratifs."""

import datetime
import wx

from Ol import OL_candidatures_core as CORE
from ObjectListView import ColumnDefn
from Utils import UTILS_Dates, UTILS_Interface, UTILS_Styles
from Utils.UTILS_Traduction import _


DEPOT_LABELS = {
    0: _(u"De vive voix"),
    1: _(u"Courrier"),
    2: _(u"Téléphone"),
    3: _(u"Main à main"),
    4: _(u"Email"),
    5: _(u"France Travail"),
    6: _(u"Organisateur"),
    7: _(u"Fédération"),
    8: _(u"Autre"),
}
DECISION_LABELS = {0: _(u"À décider"), 1: _(u"Oui"), 2: _(u"Non")}
REPONSE_LABELS = {
    0: _(u"De vive voix"), 1: _(u"Courrier"), 2: _(u"Téléphone"),
    3: _(u"Main à main"), 4: _(u"Email"), 5: _(u"Autre"),
}


# Réexport des dictionnaires historiques pour compatibilité d'import.
DICT_FONCTIONS = CORE.DICT_FONCTIONS
DICT_AFFECTATIONS = CORE.DICT_AFFECTATIONS
DICT_EMPLOIS = CORE.DICT_EMPLOIS
DICT_DISPONIBILITES = CORE.DICT_DISPONIBILITES
DICT_CAND_FONCTIONS = CORE.DICT_CAND_FONCTIONS
DICT_CAND_AFFECTATIONS = CORE.DICT_CAND_AFFECTATIONS
NOMS_CANDIDATS = CORE.NOMS_CANDIDATS
NOMS_PERSONNES = CORE.NOMS_PERSONNES
LISTE_COLONNES_1 = CORE.LISTE_COLONNES_1
LISTE_COLONNES_2 = CORE.LISTE_COLONNES_2
LISTE_COLONNES_3 = CORE.LISTE_COLONNES_3


class Track(CORE.Track):
    """Même modèle métier, informations anciennement pictographiques rendues textuelles."""

    def __init__(self, donnees):
        CORE.Track.__init__(self, donnees)
        date = UTILS_Dates.DateEngFr(self.date_depot) or ""
        canal = DEPOT_LABELS.get(self.IDtype, _(u"Autre"))
        self.depot = u"%s · %s" % (date, canal) if date else canal

        if self.IDpersonne not in (None, 0):
            self.nom_candidat = u"%s · %s" % (self.nom_candidat, _(u"salarié"))

        decision = DECISION_LABELS.get(self.IDdecision, _(u"À décider"))
        if self.decision_remarques:
            self.decision = u"%s · %s" % (decision, self.decision_remarques)
        else:
            self.decision = decision

        if self.reponse == 1:
            canal_reponse = REPONSE_LABELS.get(self.IDtype_reponse, _(u"Autre"))
            date_reponse = ""
            if self.date_reponse:
                date_reponse = UTILS_Dates.DateEngFr(self.date_reponse) or ""
            self.texte_reponse = (
                u"%s · %s" % (date_reponse, canal_reponse)
                if date_reponse else canal_reponse
            )
        elif self.reponse_obligatoire == 1:
            self.texte_reponse = _(u"À envoyer")
        else:
            self.texte_reponse = _(u"Non requise")


class ListView(CORE.ListView):
    """Liste métier historique avec rendu neutre et états textuels."""

    def GetTracks(self):
        listeID = None
        self.criteres = ""
        if self.IDcandidat not in (None, 0):
            self.criteres = "WHERE IDcandidat=%d" % self.IDcandidat
        if self.IDpersonne not in (None, 0):
            self.criteres = "WHERE IDpersonne=%d" % self.IDpersonne
        if self.IDemploi is not None:
            self.criteres = "WHERE IDemploi=%d" % self.IDemploi
        if self.listeFiltres:
            listeID, criteres = self.GetListeFiltres(self.listeFiltres)
            if criteres:
                self.criteres = (
                    "WHERE " + criteres if not self.criteres
                    else self.criteres + " AND " + criteres
                )

        DB = CORE.GestionDB.DB()
        req = """SELECT IDcandidature, IDcandidat, date_depot, IDtype, acte_remarques,
        IDemploi, periodes_remarques, IDdecision, decision_remarques,
        reponse_obligatoire, reponse, date_reponse, IDtype_reponse, IDpersonne
        FROM candidatures %s ORDER BY date_depot;""" % self.criteres
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()
        objets = []
        for row in rows:
            if listeID is not None and row[0] not in listeID:
                continue
            track = Track(row)
            objets.append(track)
            if self.selectionID == row[0]:
                self.selectionTrack = track
        return objets

    def InitObjectListView(self):
        self.oddRowsBackColor = UTILS_Interface.GetToken("surface_container_lowest")
        self.evenRowsBackColor = UTILS_Interface.GetToken("surface_container_low")
        self.useExpansionColumn = True
        self.rowFormatter = None

        colonnes = []
        for labelCol, alignement, largeur, nomChamp, args, description, affiche, ordre in sorted(
            self.listeColonnes, key=lambda item: item[7]
        ):
            if not affiche:
                continue
            if args == "date":
                colonne = ColumnDefn(
                    labelCol, alignement, largeur, nomChamp,
                    stringConverter=UTILS_Dates.DateEngFr,
                )
            else:
                # Les anciens imageGetter sont volontairement ignorés :
                # l'information correspondante est maintenant dans le texte.
                colonne = ColumnDefn(labelCol, alignement, largeur, nomChamp)
            colonnes.append(colonne)
        self.SetColumns(colonnes)
        self.SetEmptyListMsg(_(u"Aucune candidature"))
        self.SetEmptyListMsgFont(UTILS_Styles.GetFont("body-secondary"))
        if self.activeCheckBoxes:
            self.CreateCheckStateColumn(1)
            if len(self.columns) > 2:
                self.SetSortColumn(self.columns[2])
        elif len(self.columns) > 1:
            self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)

    def Supprimer(self):
        if len(self.Selection()) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner une candidature à supprimer dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        try:
            if self.GetGrandParent().GetParent().GetName() == "Recrutement":
                self.GetGrandParent().GetParent().AffichePanelResume(False)
        except Exception:
            pass

        IDcandidature = self.Selection()[0].IDcandidature
        date_depot = self.Selection()[0].depot
        dlgConfirm = wx.MessageDialog(
            self,
            _(u"Voulez-vous vraiment supprimer la candidature du %s ?") % date_depot,
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse != wx.ID_YES:
            return False

        DB = CORE.GestionDB.DB()
        placeholder = "%s" if DB.isNetwork else "?"
        try:
            for table in (
                "disponibilites",
                "cand_fonctions",
                "cand_affectations",
                "candidatures",
            ):
                DB.cursor.execute(
                    "DELETE FROM %s WHERE IDcandidature=%s" % (table, placeholder),
                    (IDcandidature,),
                )
            DB.Commit()
        except Exception as err:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            DB.Close()
            wx.MessageBox(
                _(u"La candidature n'a pas pu être supprimée. Aucune suppression n'a été validée.\n\nDétail technique : %s") % err,
                _(u"Suppression annulée"),
                wx.OK | wx.ICON_ERROR,
            )
            return False
        DB.Close()

        self.MAJ()
        return True

    def OnContextMenu(self, event):
        selection = bool(self.Selection())
        menu = wx.Menu()

        def ajouter(label, handler, enabled=True):
            identifiant = wx.NewIdRef()
            item = menu.Append(identifiant, label)
            item.Enable(enabled)
            self.Bind(wx.EVT_MENU, handler, id=identifiant)
            return item

        ajouter(_(u"Ajouter"), self.Menu_Ajouter)
        menu.AppendSeparator()
        ajouter(_(u"Modifier"), self.Menu_Modifier, selection)
        ajouter(_(u"Supprimer"), self.Menu_Supprimer, selection)
        menu.AppendSeparator()
        ajouter(_(u"Créer un courrier ou un email"), self.Menu_Courrier, selection)
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


if __name__ == "__main__":
    app = wx.App(0)
    frame = wx.Frame(None, title=_(u"Candidatures"))
    panel = wx.Panel(frame)
    ctrl = ListView(panel, id=-1, modeAffichage="avec_nom", style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
    ctrl.MAJ()
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(ctrl, 1, wx.EXPAND)
    panel.SetSizer(sizer)
    frame.SetSize((1000, 650))
    frame.Show()
    app.MainLoop()
