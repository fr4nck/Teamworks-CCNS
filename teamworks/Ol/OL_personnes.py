#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Vue personnes modernisée : lecture tolérante et suppression atomique."""

import wx

from Ol import OL_personnes_core as CORE
from Utils.UTILS_Traduction import _


LISTE_COLONNES = CORE.LISTE_COLONNES


class Track(CORE.Track):
    """Ligne personne tolérante aux références historiques orphelines."""

    def __init__(self, donnees):
        self.IDpersonne = donnees[0]
        self.civilite = donnees[1]
        self.nom = donnees[2]
        self.nom_jfille = donnees[3]
        self.prenom = donnees[4]
        self.date_naiss = donnees[5]
        self.age = CORE.Track.RetourneAge(self, self.date_naiss)
        self.cp_naiss = donnees[6]
        self.ville_naiss = donnees[7]
        self.pays_naiss = donnees[8]
        self.nationalite = donnees[9]
        self.num_secu = donnees[10]
        self.adresse_resid = donnees[11]
        self.cp_resid = donnees[12]
        self.ville_resid = donnees[13]
        self.IDsituation = donnees[14]

        pays = CORE.DICT_PAYS.get(self.pays_naiss)
        self.nom_pays_naiss = (
            pays[0]
            if pays
            else (_(u"Pays introuvable (réf. %s)") % self.pays_naiss if self.pays_naiss not in (None, 0) else "")
        )
        nationalite = CORE.DICT_PAYS.get(self.nationalite)
        self.nom_nationalite = (
            nationalite[1]
            if nationalite
            else (_(u"Nationalité introuvable (réf. %s)") % self.nationalite if self.nationalite not in (None, 0) else "")
        )
        self.nom_situation = self.GetNomSituation(self.IDsituation)
        self.telephones = CORE.Track.GetCoordonnees(self, self.IDpersonne, type="telephone")
        self.email = CORE.Track.GetCoordonnees(self, self.IDpersonne, type="email")
        self.fax = CORE.Track.GetCoordonnees(self, self.IDpersonne, type="fax")
        self.qualifications = self.GetQualifications(self.IDpersonne)

        nom = self.nom or ""
        prenom = self.prenom or ""
        self.champ_recherche = u"%s %s %s" % (nom, prenom, nom)

    def GetNomSituation(self, IDsituation):
        if IDsituation in (None, 0):
            return ""
        return CORE.DICT_SITUATIONS.get(
            IDsituation,
            _(u"Situation introuvable (réf. %s)") % IDsituation,
        )

    def GetQualifications(self, IDpersonne):
        qualifications = []
        for IDtype_diplome in CORE.DICT_QUALIFICATIONS.get(IDpersonne, []):
            qualifications.append(
                CORE.DICT_TYPES_DIPLOMES.get(
                    IDtype_diplome,
                    _(u"Diplôme introuvable (réf. %s)") % IDtype_diplome,
                )
            )
        return "; ".join(qualifications)


class ListView(CORE.ListView):
    """Liste historique conservée, avec lecture robuste et suppression transactionnelle."""

    def GetTracks(self):
        DB = CORE.GestionDB.DB()
        req = """SELECT IDpersonne, civilite, nom, nom_jfille, prenom, date_naiss,
        cp_naiss, ville_naiss, pays_naiss, nationalite, num_secu,
        adresse_resid, cp_resid, ville_resid, IDsituation
        FROM personnes %s ORDER BY nom, prenom;""" % self.criteres
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()

        objets = []
        for row in rows:
            track = Track(row)
            objets.append(track)
            if self.selectionID == row[0]:
                self.selectionTrack = track
        return objets

    def _selected_person_id(self):
        selection = self.Selection()
        if not selection:
            return None
        return getattr(selection[0], "IDpersonne", None)

    def _top_person_id(self):
        if not self.GetItemCount():
            return None
        try:
            top_index = self.GetTopItem()
            top_object = self.GetObjectAt(top_index)
        except Exception:
            return None
        return getattr(top_object, "IDpersonne", None)

    def _find_track(self, person_id, objects=None):
        if person_id is None:
            return None
        if objects is None:
            objects = self.GetObjects()
        for track in objects:
            if getattr(track, "IDpersonne", None) == person_id:
                return track
        return None

    def _visible_person_ids(self):
        return {
            getattr(track, "IDpersonne", None)
            for track in self.GetFilteredObjects()
        }

    def SyncSummary(self, person_id=None):
        """Synchronise explicitement le résumé avec la sélection visible."""
        if person_id is None:
            person_id = self._selected_person_id()

        visible = person_id is not None and person_id in self._visible_person_ids()
        try:
            frame = self.GetGrandParent().GetParent()
            if visible:
                frame.panel_resume.OnSelectPersonne(IDpersonne=person_id)
                frame.AffichePanelResume(True)
            else:
                frame.AffichePanelResume(False)
        except Exception:
            pass

    def MAJ(self, IDpersonne=None, presents=None):
        """Recharge les données sans reconstruire la configuration ObjectListView."""
        selected_id = IDpersonne if IDpersonne is not None else self._selected_person_id()
        top_id = self._top_person_id()

        if presents is not None:
            self.presents = presents

        # InitModel utilise selectionID uniquement pour retrouver le Track demandé.
        self.selectionID = selected_id
        self.selectionTrack = None
        self.InitModel()

        # SetObjects conserve colonnes, largeurs, filtre et configuration de tri.
        self.SetObjects(self.donnees)

        visible_ids = self._visible_person_ids()
        selected_track = self._find_track(selected_id)
        if selected_track is not None and selected_id in visible_ids:
            self.SelectObject(selected_track, deselectOthers=True, ensureVisible=True)
        else:
            self.DeselectAll()

        # En l'absence d'une sélection visible à restaurer, conserver autant que
        # possible la zone de lecture précédente.
        if selected_track is None or selected_id not in visible_ids:
            top_track = self._find_track(top_id, self.GetFilteredObjects())
            if top_track is not None:
                top_index = self.GetIndexOf(top_track)
                if top_index >= 0:
                    self.EnsureVisible(top_index)

        self.SyncSummary(selected_id if selected_id in visible_ids else None)
        self.selectionID = None
        self.selectionTrack = None

    def Supprimer(self):
        selection = self.Selection()
        if not selection:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez d'abord sélectionner une fiche personne à supprimer dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        from application.services.person_delete import (
            BLOCK_CONTRACTS,
            BLOCK_PRESENCES,
            BLOCK_REIMBURSEMENTS,
            BLOCK_TRAVEL,
            check_person_deletion,
            delete_person,
        )
        from infrastructure.repositories.person_delete_repository import (
            GestionDBPersonDeleteRepository,
        )

        person_id = selection[0].IDpersonne
        repository = GestionDBPersonDeleteRepository()
        blocking_messages = {
            BLOCK_CONTRACTS: _(u"Vous ne pouvez pas supprimer une personne qui possède un ou plusieurs contrat(s).\n\nSi vous voulez vraiment supprimer cette fiche, vous devez d'abord supprimer le ou les contrat(s) de la personne."),
            BLOCK_PRESENCES: _(u"Vous ne pouvez pas supprimer une personne pour laquelle des présences ont déjà été enregistrées.\n\nSi vous voulez vraiment supprimer cette fiche, vous devez d'abord supprimer le ou les présence(s) de la personne."),
            BLOCK_TRAVEL: _(u"Vous ne pouvez pas supprimer une personne pour laquelle des déplacements ont déjà été enregistrés.\n\nSi vous voulez vraiment supprimer cette fiche, vous devez d'abord supprimer le ou les déplacement(s) de la personne."),
            BLOCK_REIMBURSEMENTS: _(u"Vous ne pouvez pas supprimer une personne pour laquelle des remboursements ont déjà été enregistrés.\n\nSi vous voulez vraiment supprimer cette fiche, vous devez d'abord supprimer le ou les remboursement(s) de la personne."),
        }

        try:
            check = check_person_deletion(person_id, repository)
        except Exception as err:
            wx.MessageBox(
                _(u"La vérification des données liées à cette personne a échoué. La suppression n'a pas été lancée.\n\nDétail technique : %s") % err,
                _(u"Suppression annulée"),
                wx.OK | wx.ICON_ERROR,
            )
            return False

        if not check.allowed:
            dlg = wx.MessageDialog(
                self,
                blocking_messages[check.blocking_reason],
                "Information",
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        nom = u"%s %s" % (selection[0].prenom or "", selection[0].nom or "")
        message = _(
            u"Voulez-vous vraiment supprimer cette identité ?\n\n> %s\n\n\n"
            u"Attention : Les coordonnées, diplômes ou pièces de cette personne seront également supprimés."
        ) % nom.strip()
        dlg = wx.MessageDialog(
            self,
            message,
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES:
            return False

        try:
            result = delete_person(person_id, repository)
        except Exception as err:
            wx.MessageBox(
                _(u"La personne n'a pas pu être supprimée. Aucune suppression n'a été validée.\n\nDétail technique : %s") % err,
                _(u"Suppression annulée"),
                wx.OK | wx.ICON_ERROR,
            )
            return False

        if not result.allowed:
            dlg = wx.MessageDialog(
                self,
                blocking_messages[result.blocking_reason],
                "Information",
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        self.MAJ()
        try:
            self.GetGrandParent().GetParent().AffichePanelResume(False)
        except Exception:
            pass
        return True


DateEngFr = CORE.DateEngFr
Impression = CORE.Impression


if __name__ == "__main__":
    app = wx.App(0)
    frame = wx.Frame(None, title=_(u"Personnes"))
    panel = wx.Panel(frame)
    ctrl = ListView(panel, id=-1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(ctrl, 1, wx.EXPAND)
    panel.SetSizer(sizer)
    frame.SetSize((1100, 700))
    frame.Show()
    app.MainLoop()
