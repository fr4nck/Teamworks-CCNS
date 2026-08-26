#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Envoi explicite et minimal d'un rapport de crash Teamworks CCNS."""

import os


DESTINATAIRE_RAPPORTS_BUGS = "multimedia@pelemele.org"
TAILLE_MAX_RAPPORT = 2 * 1024 * 1024


class ErreurEnvoiRapport(Exception):
    """Erreur présentable à l'utilisateur sans exposer la configuration mail."""


def _valider_rapport(chemin_rapport):
    chemin = os.path.abspath(chemin_rapport or "")
    if not chemin_rapport or not os.path.isfile(chemin):
        raise ErreurEnvoiRapport("Le fichier de rapport est introuvable.")
    if os.path.splitext(chemin)[1].lower() != ".txt":
        raise ErreurEnvoiRapport("Seuls les rapports techniques .txt peuvent être envoyés.")
    if os.path.getsize(chemin) > TAILLE_MAX_RAPPORT:
        raise ErreurEnvoiRapport("Le rapport technique est anormalement volumineux.")
    return chemin


def ConstruireSujet(version=""):
    version = (version or "inconnue").strip()
    return "Teamworks CCNS - rapport de crash - %s" % version


def EnvoyerRapport(chemin_rapport, version="", module_email=None):
    """Envoie un rapport sûr avec l'expéditeur par défaut de Teamworks.

    Aucun envoi n'est tenté sans adresse expéditeur configurée. ``module_email``
    est injectable afin de tester ce chemin sans accès réseau ni base réelle.
    """
    chemin = _valider_rapport(chemin_rapport)
    if module_email is None:
        from Utils import UTILS_Envoi_email as module_email

    adresse = module_email.GetAdresseExpDefaut()
    if not adresse:
        raise ErreurEnvoiRapport(
            "Aucune adresse expéditeur par défaut n'est configurée dans Teamworks."
        )

    message = module_email.Message(
        destinataires=[DESTINATAIRE_RAPPORTS_BUGS],
        sujet=ConstruireSujet(version),
        texte_html=(
            "<p>Rapport technique automatique de Teamworks CCNS.</p>"
            "<p>Le fichier joint ne contient ni donnée métier ni contenu de base de données.</p>"
        ),
        fichiers=[chemin],
    )
    messagerie = None
    connectee = False
    try:
        messagerie = module_email.Messagerie(
            backend=adresse.get("moteur"),
            hote=adresse.get("smtp"),
            port=adresse.get("port"),
            utilisateur=adresse.get("utilisateur"),
            motdepasse=adresse.get("motdepasse"),
            email_exp=adresse.get("adresse"),
            nom_exp=adresse.get("nom_adresse"),
            use_tls=adresse.get("startTLS", False),
            timeout=60,
            parametres=adresse.get("parametres"),
        )
        messagerie.Connecter()
        connectee = True
        resultat = messagerie.Envoyer(message)
        if resultat in (False, 0, None):
            raise ErreurEnvoiRapport("Le serveur de messagerie a refusé le rapport.")
    except ErreurEnvoiRapport:
        raise
    except Exception as err:
        raise ErreurEnvoiRapport(
            "L'envoi a échoué. Vérifiez la configuration de l'adresse expéditeur."
        ) from err
    finally:
        if messagerie is not None and connectee:
            try:
                messagerie.Fermer()
            except Exception:
                pass

    return DESTINATAIRE_RAPPORTS_BUGS
