#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import wx
import GestionDB

if 'phoenix' in wx.PlatformInfo:
    TYPE_COULEUR = wx._core.Colour
else:
    TYPE_COULEUR = wx._gdi.Colour


def ParametresCategorie(mode="get", categorie="", dictParametres={}, nomFichier=""):
    """Pour mémoriser ou récupérer des paramètres dans la base de données."""
    DB = GestionDB.DB(nomFichier=nomFichier)

    if DB.echec == 1:
        return dictParametres

    req = u'''SELECT IDparametre, nom, parametre FROM parametres WHERE categorie="%s";''' % categorie
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    dictDonnees = {}
    for IDparametre, nom, parametre in listeDonnees:
        dictDonnees[nom] = parametre

    listeAjouts = []
    listeModifications = []
    dictFinal = {}

    for nom, valeur in list(dictParametres.items()):
        type_parametre = type(valeur)
        if type_parametre in (int, float, tuple, list, dict, bool, TYPE_COULEUR):
            valeurTmp = str(valeur)
        elif type_parametre == str:
            valeurTmp = valeur
        else:
            valeurTmp = ""

        if nom in dictDonnees:
            if mode == "get":
                valeur = dictDonnees[nom]
                try:
                    if type_parametre == int:
                        valeur = int(valeur)
                    if type_parametre == float:
                        valeur = float(valeur)
                    if type_parametre in (tuple, list, dict, bool):
                        valeur = eval(valeur)
                    if type_parametre == TYPE_COULEUR and valeur != "":
                        valeur = eval(valeur)
                except Exception:
                    valeur = None
                dictFinal[nom] = valeur

            if mode == "set":
                dictFinal[nom] = valeur
                if dictDonnees[nom] != valeurTmp:
                    listeModifications.append((valeurTmp, categorie, nom))
        else:
            listeAjouts.append((categorie, nom, valeurTmp))
            dictFinal[nom] = valeur

    if len(listeModifications) > 0:
        DB.Executermany(
            "UPDATE parametres SET parametre=? WHERE categorie=? and nom=?",
            listeModifications,
            commit=False,
        )

    if len(listeAjouts) > 0:
        DB.Executermany(
            "INSERT INTO parametres (categorie, nom, parametre) VALUES (?, ?, ?)",
            listeAjouts,
            commit=False,
        )

    if len(listeModifications) > 0 or len(listeAjouts) > 0:
        DB.Commit()
    DB.Close()
    return dictFinal


def Parametres(mode="get", categorie="", nom="", valeur=None, nomFichier=""):
    """Mémorise ou récupère un paramètre quelconque dans la base de données."""
    type_parametre = type(valeur)
    if type_parametre in (int, float, tuple, list, dict, bool):
        valeurTmp = str(valeur)
    elif type_parametre == str:
        valeurTmp = valeur
    else:
        valeurTmp = ""

    DB = GestionDB.DB(nomFichier=nomFichier)

    if DB.echec == 1:
        return valeur

    req = u'''SELECT IDparametre, parametre FROM parametres WHERE categorie="%s" AND nom="%s" ;''' % (categorie, nom)
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    if len(listeDonnees) != 0:
        if mode == "get":
            valeurTmp = listeDonnees[0][1]
            if type_parametre == int:
                valeurTmp = int(valeurTmp)
            if type_parametre == float:
                valeurTmp = float(valeurTmp)
            if type_parametre in (tuple, list, dict, bool):
                valeurTmp = eval(valeurTmp)
        else:
            IDparametre = listeDonnees[0][0]
            listeDonnees = [
                ("categorie", categorie),
                ("nom", nom),
                ("parametre", valeurTmp),
            ]
            DB.ReqMAJ("parametres", listeDonnees, "IDparametre", IDparametre)
            valeurTmp = valeur
    else:
        listeDonnees = [
            ("categorie", categorie),
            ("nom", nom),
            ("parametre", valeurTmp),
        ]
        DB.ReqInsert("parametres", listeDonnees)
        valeurTmp = valeur
    DB.Close()
    return valeurTmp


def TestParametre(categorie="", nom="", valeur=None, nomFichier=""):
    """Vérifie si un paramètre existe dans le fichier."""
    DB = GestionDB.DB(nomFichier=nomFichier)
    req = u'''SELECT IDparametre, parametre FROM parametres WHERE categorie="%s" AND nom="%s" ;''' % (categorie, nom)
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    return len(listeDonnees) != 0


if __name__ == u"__main__":
    reponse = Parametres(
        mode="get",
        categorie="dlg_ouvertures",
        nom="afficher_tous_groupes",
        valeur=False,
    )
    print((reponse, type(reponse)))
