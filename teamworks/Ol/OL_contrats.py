#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liste des contrats modernisée : compatibilité historique et lecture tolérante."""

from Ol import OL_contrats_core as CORE
from Utils.UTILS_Traduction import _


LISTE_COLONNES_1 = CORE.LISTE_COLONNES_1
LISTE_COLONNES_2 = CORE.LISTE_COLONNES_2
LISTE_COLONNES_3 = CORE.LISTE_COLONNES_3
CTRL_Outils = CORE.CTRL_Outils
Popup = CORE.Popup
DateEngFr = CORE.DateEngFr
Impression = CORE.Impression


class Track(CORE.Track):
    """Contrat tolérant aux types de diplômes historiques supprimés."""

    def GetQualifications(self, IDpersonne):
        qualifications = []
        for IDtype_diplome in self.parent.dict_qualifications.get(IDpersonne, []):
            qualifications.append(
                self.parent.dict_types_diplomes.get(
                    IDtype_diplome,
                    _(u"Diplôme introuvable (réf. %s)") % IDtype_diplome,
                )
            )
        return ", ".join(qualifications)


class ListView(CORE.ListView):
    """Conserve la liste historique sans le branchement Recrutement obsolète."""

    def OnItemSelected(self, event):
        self.DestroyPopup()
        self.itemSelected = True

    def DeselectionneItem(self):
        self.itemSelected = False

    def GetTracks(self):
        listeID = None
        self.criteres = ""
        if self.IDpersonne not in (None, 0):
            self.criteres = "WHERE IDpersonne=%d" % self.IDpersonne
        if self.listeFiltres:
            listeID, criteres = self.GetListeFiltres(self.listeFiltres)
            if criteres:
                if self.criteres:
                    self.criteres += " AND " + criteres
                else:
                    self.criteres = "WHERE " + criteres

        DB = CORE.GestionDB.DB()

        DB.ExecuterReq("""SELECT IDdiplome, IDpersonne, IDtype_diplome
        FROM diplomes;""")
        self.dict_qualifications = {}
        for _IDdiplome, IDpersonne, IDtype_diplome in DB.ResultatReq():
            self.dict_qualifications.setdefault(IDpersonne, []).append(IDtype_diplome)

        DB.ExecuterReq("""SELECT IDtype_diplome, nom_diplome
        FROM types_diplomes;""")
        self.dict_types_diplomes = {
            IDtype_diplome: nom_diplome
            for IDtype_diplome, nom_diplome in DB.ResultatReq()
        }

        req = """
        SELECT contrats.IDcontrat, contrats.IDpersonne, contrats.date_debut, contrats.date_fin,
        contrats_class.nom, contrats_types.nom,
        personnes.civilite, personnes.nom, personnes.nom_jfille, personnes.prenom,
        personnes.date_naiss, pays.nom, personnes.num_secu
        FROM contrats
        LEFT JOIN personnes ON contrats.IDpersonne = personnes.IDpersonne
        LEFT JOIN contrats_class ON contrats_class.IDclassification = contrats.IDclassification
        LEFT JOIN contrats_types ON contrats_types.IDtype = contrats.IDtype
        LEFT JOIN pays ON pays.IDpays = personnes.nationalite
        %s
        """ % self.criteres
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        DB.Close()

        objets = []
        for row in rows:
            if listeID is not None and row[0] not in listeID:
                continue
            track = Track(self, row)
            objets.append(track)
            if self.selectionID == row[0]:
                self.selectionTrack = track
        return objets


if __name__ == "__main__":
    CORE.MyFrame
