#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Correctifs de compatibilité pour la page Qualifications.

Des bases historiques peuvent contenir dans ``pieces.date_fin`` des valeurs
vides ou non normalisées. Le contrôle historique supposait toujours une chaîne
ISO AAAA-MM-JJ et pouvait donc empêcher l'ouverture complète d'une fiche
individuelle. Ce module conserve les données telles quelles et rend uniquement
leur lecture non bloquante.
"""

from Utils import UTILS_Dates

_INSTALLED = False


def _date_fr(value):
    date_dd = UTILS_Dates.DateEnDateDD(value)
    if date_dd is None:
        return ""
    return UTILS_Dates.DateEngFr(date_dd)


def _date_tri(value):
    date_dd = UTILS_Dates.DateEnDateDD(value)
    if date_dd is None:
        return ""
    return "%04d-%02d-%02d" % (date_dd.year, date_dd.month, date_dd.day)


def _etat_expiration(self, date_debut, date_fin):
    import datetime

    date_fin_dd = UTILS_Dates.DateEnDateDD(date_fin)
    if date_fin_dd is None:
        return "Date invalide"
    if date_fin_dd == datetime.date(2999, 1, 1):
        return ""

    jours = (date_fin_dd - datetime.date.today()).days
    if jours < 0:
        return "Pièce expirée"
    if jours == 0:
        return "Expire aujourd'hui !"
    if jours == 1:
        return "Expire demain !"
    return "Expire dans %d jours" % jours


def _importation_dossier(self):
    import datetime
    import GestionDB

    date_jour = datetime.date.today()
    self.dict_docs = self.GetDocumentsScan()

    DB = GestionDB.DB()
    try:
        self.DictDossier = {}
        req = """
        SELECT pieces.IDpiece, types_pieces.nom_piece, pieces.date_debut, pieces.date_fin, pieces.IDpersonne
        FROM pieces INNER JOIN types_pieces ON pieces.IDtype_piece = types_pieces.IDtype_piece
        WHERE (((pieces.IDpersonne)=%d));
        """ % self.IDpersonne
        DB.ExecuterReq(req)
        liste_pieces = DB.ResultatReq()

        for piece in liste_pieces:
            IDpiece = piece[0]
            nom_piece = piece[1]
            date_debut = piece[2]
            date_fin = piece[3]
            date_fin_dd = UTILS_Dates.DateEnDateDD(date_fin)

            if date_fin_dd is None:
                etat = "Invalide"
            elif date_fin_dd < date_jour:
                etat = "Perim"
            else:
                etat = "Ok"

            self.DictDossier[IDpiece] = (
                etat,
                nom_piece,
                date_debut,
                date_fin,
            )
    finally:
        DB.Close()


def install():
    """Installe le correctif une seule fois sur le module historique."""
    global _INSTALLED
    if _INSTALLED:
        return

    from Ctrl import CTRL_Page_qualifications as legacy

    legacy.DateEngFr = _date_fr
    legacy.DateFrEng = _date_tri
    legacy.ListCtrl_Dossier.etatExpiration = _etat_expiration
    legacy.ListCtrl_Dossier.Importation = _importation_dossier
    _INSTALLED = True
