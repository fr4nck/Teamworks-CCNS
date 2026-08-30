#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Vue personnes modernisée : lecture tolérante et suppression atomique."""

import wx

from Ol import OL_personnes_core as CORE
from Utils.UTILS_Traduction import _


LISTE_COLONNES = CORE.LISTE_COLONNES


class Track(object):
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

        IDpersonne = selection[0].IDpersonne
        DB = CORE.GestionDB.DB()
        placeholder = "%s" if DB.isNetwork else "?"
        controles = (
            ("contrats", "IDcontrat", _(u"Vous ne pouvez pas supprimer une personne qui possède un ou plusieurs contrat(s).\n\nSi vous voulez vraiment supprimer cette fiche, vous devez d'abord supprimer le ou les contrat(s) de la personne.")),
            ("presences", "IDpresence", _(u"Vous ne pouvez pas supprimer une personne pour laquelle des présences ont déjà été enregistrées.\n\nSi vous voulez vraiment supprimer cette fiche, vous devez d'abord supprimer le ou les présence(s) de la personne.")),
            ("deplacements", "IDdeplacement", _(u"Vous ne pouvez pas supprimer une personne pour laquelle des déplacements ont déjà été enregistrés.\n\nSi vous voulez vraiment supprimer cette fiche, vous devez d'abord supprimer le ou les déplacement(s) de la personne.")),
            ("remboursements", "IDremboursement", _(u"Vous ne pouvez pas supprimer une personne pour laquelle des remboursements ont déjà été enregistrés.\n\nSi vous voulez vraiment supprimer cette fiche, vous devez d'abord supprimer le ou les remboursement(s) de la personne.")),
        )
        try:
            for table, colonne, message in controles:
                DB.cursor.execute(
                    "SELECT %s FROM %s WHERE IDpersonne=%s" % (colonne, table, placeholder),
                    (IDpersonne,),
                )
                if DB.cursor.fetchone() is not None:
                    DB.Close()
                    dlg = wx.MessageDialog(self, message, "Information", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
        except Exception as err:
            DB.Close()
            wx.MessageBox(
                _(u"La vérification des données liées à cette personne a échoué. La suppression n'a pas été lancée.\n\nDétail technique : %s") % err,
                _(u"Suppression annulée"),
                wx.OK | wx.ICON_ERROR,
            )
            return False
        DB.Close()

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

        DB = CORE.GestionDB.DB()
        placeholder = "%s" if DB.isNetwork else "?"
        try:
            for table in ("coordonnees", "diplomes", "pieces", "personnes"):
                DB.cursor.execute(
                    "DELETE FROM %s WHERE IDpersonne=%s" % (table, placeholder),
                    (IDpersonne,),
                )
            DB.Commit()
        except Exception as err:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            DB.Close()
            wx.MessageBox(
                _(u"La personne n'a pas pu être supprimée. Aucune suppression n'a été validée.\n\nDétail technique : %s") % err,
                _(u"Suppression annulée"),
                wx.OK | wx.ICON_ERROR,
            )
            return False
        DB.Close()

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
