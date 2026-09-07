#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Lectures optimisées pour l'état des dossiers personnes.

Ce module conserve les règles historiques de ``FonctionsPerso`` mais regroupe
les lectures par personne afin d'éviter le N+1 sur une base MySQL distante.
"""

import datetime

import FonctionsPerso
import GestionDB
from Utils.UTILS_Traduction import _


def _ids_uniques(liste):
    resultat = []
    vus = set()
    for valeur in liste:
        if valeur in vus:
            continue
        vus.add(valeur)
        resultat.append(valeur)
    return resultat


def _clause_ids(liste_ids):
    if not liste_ids:
        return "(100000)"
    if len(liste_ids) == 1:
        return "(%d)" % liste_ids[0]
    return str(tuple(liste_ids))


def Creation_liste_pb_personnes():
    """Version batchée de ``FonctionsPerso.Creation_liste_pb_personnes``.

    Avant : 5 * N + 2 requêtes pour N personnes ayant un contrat actif/à venir.
    Après : 7 requêtes, indépendamment de N.
    """
    liste_ids = _ids_uniques(FonctionsPerso.Recherche_ContratsEnCoursOuAVenir())
    return Recherche_problemes_personnes(tuple(liste_ids))


def Recherche_problemes_personnes(listeIDpersonnes=(), infosPersonne=None):
    """Calcule les mêmes problèmes dossier avec des lectures SQL regroupées."""
    if infosPersonne is None:
        infosPersonne = []

    liste_ids = _ids_uniques(list(listeIDpersonnes))
    clause_ids = _clause_ids(liste_ids)
    dictProblemes = {}
    dictNoms = {}

    DB = GestionDB.DB()

    req = """SELECT IDpersonne, civilite, nom, nom_jfille, prenom, date_naiss,
    cp_naiss, ville_naiss, pays_naiss, nationalite, num_secu, adresse_resid,
    cp_resid, ville_resid, IDsituation
    FROM personnes WHERE IDpersonne IN %s ORDER BY nom;""" % clause_ids
    DB.ExecuterReq(req)
    listePersonnes = DB.ResultatReq()
    if infosPersonne:
        listePersonnes = infosPersonne

    req = """SELECT IDpersonne
    FROM coordonnees
    WHERE IDpersonne IN %s
    GROUP BY IDpersonne;""" % clause_ids
    DB.ExecuterReq(req)
    personnes_avec_coord = set(row[0] for row in DB.ResultatReq())

    for personne in listePersonnes:
        IDpersonne = personne[0]
        civilite = personne[1]
        nom = personne[2]
        nom_jfille = personne[3]
        prenom = personne[4]
        date_naiss = personne[5]
        cp_naiss = personne[6]
        ville_naiss = personne[7]
        pays_naiss = personne[8]
        nationalite = personne[9]
        num_secu = personne[10]
        adresse_resid = personne[11]
        cp_resid = personne[12]
        ville_resid = personne[13]
        IDsituation = personne[14]

        dictNoms[IDpersonne] = (nom or "") + " " + (prenom or "")
        problemesFiche = []

        if civilite in ("", None):
            problemesFiche.append(_(u"Civilité"))
        if nom in ("", None):
            problemesFiche.append(_(u"Nom de famille"))
        if civilite == "Mme" and nom_jfille in ("", None):
            problemesFiche.append(_(u"Nom de jeune fille"))
        if prenom in ("", None):
            problemesFiche.append(_(u"Prénom"))
        if date_naiss is None or str(date_naiss).strip(" ") == "":
            problemesFiche.append(_(u"Date de naissance"))
        if cp_naiss is None or str(cp_naiss).strip(" ") == "":
            problemesFiche.append(_(u"Code postal de la ville de naissance"))
        if ville_naiss in ("", None):
            problemesFiche.append(_(u"Ville de naissance"))
        if pays_naiss in ("", None, 0):
            problemesFiche.append(_(u"Pays de naissance"))
        if nationalite in ("", None, 0):
            problemesFiche.append(_(u"Nationalité"))
        if num_secu is None or str(num_secu).strip(" ") == "":
            problemesFiche.append(_(u"Numéro de sécurité sociale"))
        if adresse_resid in ("", None):
            problemesFiche.append(_(u"Adresse de résidence"))
        if cp_resid is None or str(cp_resid).strip(" ") == "":
            problemesFiche.append(_(u"Code postal de résidence"))
        if ville_resid in ("", None):
            problemesFiche.append(_(u"Ville de résidence"))
        if IDsituation in ("", None, 0):
            problemesFiche.append(_(u"Situation sociale"))
        if IDpersonne not in personnes_avec_coord:
            problemesFiche.append(_(u"Coordonnées téléphoniques"))

        if problemesFiche:
            dictProblemes.setdefault(IDpersonne, {})
            if len(problemesFiche) == 1:
                categorie = _(u"1 information manquante")
            else:
                categorie = str(len(problemesFiche)) + _(u" informations manquantes")
            dictProblemes[IDpersonne][categorie] = problemesFiche

    req = """SELECT diplomes.IDpersonne, types_pieces.IDtype_piece, types_pieces.nom_piece
    FROM diplomes
    INNER JOIN diplomes_pieces
        ON diplomes.IDtype_diplome = diplomes_pieces.IDtype_diplome
    INNER JOIN types_pieces
        ON diplomes_pieces.IDtype_piece = types_pieces.IDtype_piece
    WHERE diplomes.IDpersonne IN %s;""" % clause_ids
    DB.ExecuterReq(req)
    pieces_specifiques = {}
    for IDpersonne, IDtype_piece, nom_piece in DB.ResultatReq():
        pieces_specifiques.setdefault(IDpersonne, []).append((IDtype_piece, nom_piece))

    req = """SELECT diplomes_pieces.IDtype_piece, types_pieces.nom_piece
    FROM diplomes_pieces
    INNER JOIN types_pieces
        ON diplomes_pieces.IDtype_piece = types_pieces.IDtype_piece
    WHERE diplomes_pieces.IDtype_diplome=0;"""
    DB.ExecuterReq(req)
    pieces_basiques = list(DB.ResultatReq())

    date_jour = datetime.date.today()
    req = """SELECT pieces.IDpersonne, types_pieces.IDtype_piece,
    pieces.date_debut, pieces.date_fin
    FROM types_pieces
    LEFT JOIN pieces ON types_pieces.IDtype_piece = pieces.IDtype_piece
    WHERE pieces.IDpersonne IN %s
      AND pieces.date_debut<='%s'
      AND pieces.date_fin>='%s'
    ORDER BY pieces.IDpersonne, pieces.date_fin;""" % (clause_ids, date_jour, date_jour)
    DB.ExecuterReq(req)
    pieces_possedees = {}
    for IDpersonne, IDtype_piece, date_debut, date_fin in DB.ResultatReq():
        pieces_possedees.setdefault(IDpersonne, {})[IDtype_piece] = (date_debut, date_fin)

    req = """SELECT IDpersonne, signature, due
    FROM contrats
    WHERE IDpersonne IN %s
    ORDER BY IDpersonne, date_debut;""" % clause_ids
    DB.ExecuterReq(req)
    contrats = {}
    for IDpersonne, signature, due in DB.ResultatReq():
        contrats.setdefault(IDpersonne, []).append((signature, due))

    DB.Close()

    for IDpersonne in liste_ids:
        piecesManquantes = []
        piecesPerimees = []
        DictPieces = {}
        listePiecesAFournir = list(pieces_specifiques.get(IDpersonne, []))
        listePiecesAFournir.extend(pieces_basiques)
        dictTmpPieces = pieces_possedees.get(IDpersonne, {})

        for IDtype_piece, nom_piece in listePiecesAFournir:
            if IDtype_piece in dictTmpPieces:
                date_fin = dictTmpPieces[IDtype_piece][1]
                date_fin = datetime.date(int(date_fin[:4]), int(date_fin[5:7]), int(date_fin[8:10]))
                reste = str(date_fin - date_jour)
                if reste != "0:00:00":
                    jours = int(reste[:reste.index("day")])
                    if jours < 15 and jours > 0:
                        etat = "Attention"
                    elif jours <= 0:
                        etat = "PasOk"
                    else:
                        etat = "Ok"
                else:
                    etat = "Attention"
            else:
                etat = "PasOk"
            DictPieces[IDtype_piece] = (etat, nom_piece)

        for IDtype_piece, donnees in DictPieces.items():
            etat, nom_piece = donnees
            if etat == "PasOk":
                piecesManquantes.append(nom_piece)
            elif etat == "Attention":
                piecesPerimees.append(nom_piece)

        if piecesManquantes:
            dictProblemes.setdefault(IDpersonne, {})
            if len(piecesManquantes) == 1:
                categorie = _(u"1 pièce manquante")
            else:
                categorie = str(len(piecesManquantes)) + _(u" pièces manquantes")
            dictProblemes[IDpersonne][categorie] = piecesManquantes

        if piecesPerimees:
            dictProblemes.setdefault(IDpersonne, {})
            if len(piecesPerimees) == 1:
                categorie = _(u"1 pièce bientôt périmée")
            else:
                categorie = str(len(piecesPerimees)) + _(u" pièces bientôt périmées")
            dictProblemes[IDpersonne][categorie] = piecesPerimees

        problemesContrats = []
        for signature, due in contrats.get(IDpersonne, []):
            if signature in ("", "Non"):
                problemesContrats.append(_(u"Contrat non signé"))
            if due in ("", "Non"):
                problemesContrats.append(_(u"DUE à faire"))

        if problemesContrats:
            dictProblemes.setdefault(IDpersonne, {})
            if len(problemesContrats) == 1:
                categorie = _(u"1 contrat à voir")
            else:
                categorie = str(len(problemesContrats)) + _(u" contrats à voir")
            dictProblemes[IDpersonne][categorie] = problemesContrats

    return dictNoms, dictProblemes
