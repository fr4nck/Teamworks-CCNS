#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import shelve
import os
import re
from Utils import UTILS_Fichiers

DICT_TRADUCTIONS = None

# Certains modules historiques ont été enregistrés avec un encodage ancien,
# puis relus ou convertis en UTF-8. Lorsque l'information d'origine est encore
# récupérable, on corrige ici les séquences de mojibake. Pour les chaînes où le
# caractère de remplacement Unicode a déjà détruit l'octet d'origine, seules
# des corrections explicites et non ambiguës sont appliquées.
_MOJIBAKE_REPLACEMENTS = (
    ("Ã©", "é"),
    ("Ã¨", "è"),
    ("Ãª", "ê"),
    ("Ã«", "ë"),
    ("Ã€", "À"),
    ("Ã ", "à"),
    ("Ã¢", "â"),
    ("Ã®", "î"),
    ("Ã¯", "ï"),
    ("Ã´", "ô"),
    ("Ã¶", "ö"),
    ("Ã¹", "ù"),
    ("Ã»", "û"),
    ("Ã¼", "ü"),
    ("Ã§", "ç"),
    ("Å“", "œ"),
    ("â€™", "’"),
    ("â€“", "–"),
    ("â€”", "—"),
    ("Â°", "°"),
    ("Â ", " "),
)

_REPLACEMENT_CHARACTER_FIXES = {
    # Mois complets et abrégés utilisés par les calendriers Teamworks.
    "F�vrier": "Février",
    "f�vrier": "février",
    "F�v.": "Fév.",
    "f�v.": "fév.",
    "Ao�t": "Août",
    "ao�t": "août",
    "D�cembre": "Décembre",
    "d�cembre": "décembre",
    "D�c.": "Déc.",
    "d�c.": "déc.",
}


def CorrigeMojibake(chaine):
    """Répare les séquences d'encodage cassées encore identifiables.

    La fonction est volontairement conservative : elle ne tente pas de deviner
    une lettre lorsque le caractère d'origine est perdu, sauf pour les libellés
    français explicitement recensés dans ``_REPLACEMENT_CHARACTER_FIXES``.
    """
    if not isinstance(chaine, str):
        return chaine

    resultat = chaine
    for valeur_incorrecte, valeur_correcte in _MOJIBAKE_REPLACEMENTS:
        resultat = resultat.replace(valeur_incorrecte, valeur_correcte)

    for valeur_incorrecte, valeur_correcte in _REPLACEMENT_CHARACTER_FIXES.items():
        resultat = resultat.replace(valeur_incorrecte, valeur_correcte)

    return resultat


def ChargeTraduction(nom=""):
    """ Charge un fichier de langage """
    global DICT_TRADUCTIONS
    dictTraductions = {}

    # Recherche le fichier de langage par défaut ".lang" puis un éventuel fichier perso ".xlang"
    for extension in ("lang", "xlang"):
        nomFichier = UTILS_Fichiers.GetRepLang(u"%s.%s" % (nom, extension))
        if os.path.isfile(nomFichier):
            fichier = shelve.open(nomFichier, "r")
            for key, valeur in fichier.items():
                if isinstance(key, bytes):
                    key = key.decode("iso-8859-15")
                dictTraductions[CorrigeMojibake(key)] = CorrigeMojibake(valeur)
            fichier.close()

    # Mémorise les traductions
    DICT_TRADUCTIONS = dictTraductions


def _(chaine):
    """ Traduit une chaîne et normalise les libellés historiques cassés. """
    chaine_corrigee = CorrigeMojibake(chaine)

    # Recherche si une traduction existe. On conserve aussi la recherche avec
    # la clé historique pour ne pas casser d'anciens fichiers de langue.
    if DICT_TRADUCTIONS is not None:
        if chaine_corrigee in DICT_TRADUCTIONS:
            return CorrigeMojibake(DICT_TRADUCTIONS[chaine_corrigee])
        if chaine in DICT_TRADUCTIONS:
            return CorrigeMojibake(DICT_TRADUCTIONS[chaine])

    # Sinon renvoie la chaîne par défaut corrigée.
    return chaine_corrigee


def GenerationFichierTextes():
    listeFichiers = os.listdir(os.getcwd())
    listeFichiersTrouves = []
    dictTextes = {}

    # Recherche des textes
    exp = re.compile(r"_\(u\".*?\"\)")

    for nomFichier in listeFichiers:

        if nomFichier.endswith("py") and nomFichier.startswith("DATA_") is False and nomFichier not in ("CreateurMAJ.py", "CreateurANNONCES.py"):
            # Ouverture du fichier
            fichier = open(nomFichier, "r")
            texte = "\n".join(fichier.readlines())
            fichier.close()

            # Analyse du fichier
            listeChaines = re.findall(exp, texte)
            for chaine in listeChaines:
                chaine = chaine[4:-2]

                valide = False
                for caract in "abceghijklmopqrtvwxyz":
                    if caract in chaine.lower():
                        valide = True
                if len(chaine) < 2:
                    valide = False
                if "Images/" in chaine:
                    valide = False

                if valide is True:
                    if chaine not in dictTextes:
                        dictTextes[chaine] = []
                    dictTextes[chaine].append(nomFichier)

    # Génération du fichier Shelve
    nomFichier = Chemins.GetStaticPath("Databases/Textes.dat")
    if os.path.isfile(nomFichier):
        flag = "w"
    else:
        flag = "n"
    fichier = shelve.open(nomFichier, flag)
    for texte, listeFichiers in dictTextes.items():
        fichier[texte] = listeFichiers
    fichier.close()
    print("Generation du fichier de textes terminee.")


def ConvertShelveEnTexte():
    """ Convertit le fichier Textes.dat en fichier Textes.txt """
    # Lecture du fichier dat
    fichier = shelve.open(Chemins.GetStaticPath("Databases/Textes.dat"), "r")
    listeTextes = []
    for texte, listeFichiers in fichier.items():
        listeTextes.append(texte)
    fichier.close()
    listeTextes.sort()

    # Enregistrement du fichier texte
    fichier = open(UTILS_Fichiers.GetRepTemp("Textes.txt"), "w")
    for texte in listeTextes:
        fichier.write(texte + "\n")
    fichier.close()
    print("Fini !")


def FusionneFichiers(code="en_GB"):
    # Lecture du fichier xlang
    fichier = shelve.open(UTILS_Fichiers.GetRepLang(u"%s.xlang" % code), "r")
    dictDonnees = {}
    for texte, traduction in fichier.items():
        if texte != "###INFOS###":
            dictDonnees[texte] = traduction
    fichier.close()

    # Lecture du fichier lang
    fichier = shelve.open(UTILS_Fichiers.GetRepLang(u"%s.lang" % code), "w")
    for texte, traduction in dictDonnees.items():
        fichier[texte] = traduction
    fichier.close()
    print("Fusion de %d traductions terminee !" % len(dictDonnees))


if __name__ == "__main__":
    GenerationFichierTextes()
#    ConvertShelveEnTexte()
#    FusionneFichiers("en_GB")
