#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-19 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
import wx
import os
import shutil
from Utils import UTILS_Fichiers
from Utils import UTILS_Json




def GetNomFichierConfig(nomFichier="Config.json"):
    return UTILS_Fichiers.GetRepUtilisateur(nomFichier)

def IsFichierExists() :
    nomFichier = GetNomFichierConfig()
    return os.path.isfile(nomFichier)

def GenerationFichierConfig():
    dictDonnees = {}
    nouveau_fichier = True

    # L'ancien fichier Config.dat n'est importable que par l'ancienne version Python 2.
    # En Python 3, la configuration est créée directement au format JSON.

    # Crée les nouvelles données
    if nouveau_fichier == True :
        dictDonnees = {
            "nomFichier": "",
            "derniersFichiers": [],
            "taille_fenetre": [0, 0],
            "interface_mysql": "mysql.connector",
        }

    # Création d'un nouveau fichier json
    cfg = FichierConfig()
    cfg.SetDictConfig(dictConfig=dictDonnees)

    print(("nouveau_fichier = %s" % nouveau_fichier))
    return nouveau_fichier

def SupprimerFichier():
    nomFichier = GetNomFichierConfig()
    os.remove(nomFichier)



class FichierConfig():
    def __init__(self):
        self.nomFichier = GetNomFichierConfig()
        
    def GetDictConfig(self):
        """ Recupere une copie du dictionnaire du fichier de config """
        data = {}
        try :
            data = UTILS_Json.Lire(self.nomFichier)
        except:
            nom_fichier_bak = self.nomFichier + ".bak"
            if os.path.isfile(nom_fichier_bak):
                print("Recuperation de config.json.bak")
                data = UTILS_Json.Lire(nom_fichier_bak)
        return data

    def SetDictConfig(self, dictConfig={}):
        """ Remplace le fichier de config présent sur le disque dur par le dict donné """
        UTILS_Json.Ecrire(nom_fichier=self.nomFichier, data=dictConfig)
        # Création d'une copie de sauvegarde du config
        shutil.copyfile(self.nomFichier, self.nomFichier + ".bak")

    def GetItemConfig(self, key, defaut=None):
        """ Récupère une valeur du dictionnaire du fichier de config """
        data = self.GetDictConfig()
        if key in data :
            valeur = data[key]
        else:
            valeur = defaut
        return valeur
    
    def SetItemConfig(self, key, valeur ):
        """ Remplace une valeur dans le fichier de config """
        data = self.GetDictConfig()
        data[key] = valeur
        self.SetDictConfig(data)
