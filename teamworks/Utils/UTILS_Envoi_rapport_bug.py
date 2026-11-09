#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Envoi explicite et minimal d'un rapport de crash Teamworks CCNS."""

import os

from Utils import UTILS_MailingSession


DESTINATAIRE_RAPPORTS_BUGS_HISTORIQUE = "noethys@gmail.com"
CATEGORIE_PARAMETRE_RAPPORTS_BUGS = "maintenance"
NOM_PARAMETRE_RAPPORTS_BUGS = "adresse_rapport_bugs"
TAILLE_MAX_RAPPORT = 2 * 1024 * 1024


class ErreurEnvoiRapport(Exception):
    """Erreur présentable à l'utilisateur sans exposer la configuration mail."""


def _module_parametres(module_parametres=None):
    if module_parametres is not None:
        return module_parametres
    from Utils import UTILS_Parametres
    return UTILS_Parametres


def GetAdresseRapportBugsConfiguree(module_parametres=None):
    """Retourne uniquement la valeur explicitement configurée en base.

    Une absence de paramètre, une valeur vide ou une base indisponible renvoie
    une chaîne vide. La lecture ne crée pas le paramètre pendant un crash.
    """
    try:
        parametres = _module_parametres(module_parametres)
        if not parametres.TestParametre(
            categorie=CATEGORIE_PARAMETRE_RAPPORTS_BUGS,
            nom=NOM_PARAMETRE_RAPPORTS_BUGS,
        ):
            return ""
        valeur = parametres.Parametres(
            mode="get",
            categorie=CATEGORIE_PARAMETRE_RAPPORTS_BUGS,
            nom=NOM_PARAMETRE_RAPPORTS_BUGS,
            valeur="",
        )
    except Exception:
        return ""
    return valeur.strip() if isinstance(valeur, str) else ""


def SetAdresseRapportBugsConfiguree(adresse, module_parametres=None):
    """Enregistre le destinataire partagé ; vide signifie fallback historique."""
    valeur = adresse.strip() if isinstance(adresse, str) else ""
    parametres = _module_parametres(module_parametres)
    parametres.Parametres(
        mode="set",
        categorie=CATEGORIE_PARAMETRE_RAPPORTS_BUGS,
        nom=NOM_PARAMETRE_RAPPORTS_BUGS,
        valeur=valeur,
    )
    return valeur


def GetDestinataireRapportsBugs(module_parametres=None):
    """Résout le destinataire effectif avec le comportement historique."""
    return (
        GetAdresseRapportBugsConfiguree(module_parametres=module_parametres)
        or DESTINATAIRE_RAPPORTS_BUGS_HISTORIQUE
    )


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


def EnvoyerRapport(
    chemin_rapport,
    version="",
    module_email=None,
    destinataire=None,
    module_parametres=None,
):
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

    destinataire = destinataire.strip() if isinstance(destinataire, str) else ""
    if not destinataire:
        destinataire = GetDestinataireRapportsBugs(
            module_parametres=module_parametres
        )

    message = module_email.Message(
        destinataires=[destinataire],
        sujet=ConstruireSujet(version),
        texte_html=(
            "<p>Rapport technique automatique de Teamworks CCNS.</p>"
            "<p>Le fichier joint ne contient ni donnée métier ni contenu de base de données.</p>"
        ),
        fichiers=[chemin],
    )
    def _fabrique_messagerie():
        return module_email.Messagerie(
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

    try:
        # La methode reste synchrone pour ses appelants historiques ; si une
        # boucle wx existe, le reseau passe sur le worker de la progression.
        # En contexte sans GUI, on utilise le meme moteur sans aucun widget.
        try:
            import wx
        except ImportError:
            wx = None
        app = wx.GetApp() if wx is not None else None
        if wx is not None and wx.IsMainThread() and app is not None:
            proprietaire = UTILS_MailingSession.proprietaire_visible(None, wx)
            if proprietaire is None:
                raise ErreurEnvoiRapport(
                    "Aucune fenetre principale visible pour envoyer le rapport."
                )
            bilan = UTILS_MailingSession.envoyer_avec_progression(
                parent=proprietaire, fabrique=_fabrique_messagerie,
                messages=[message], afficher_confirmation_envoi=False,
            )
        else:
            bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
                _fabrique_messagerie, [message], delai=0,
            )

        if len(bilan.succes) != 1:
            raise ErreurEnvoiRapport(
                "L'envoi n'est pas confirme. Ne le relancez pas "
                "avant d'en verifier le statut."
            )
    except ErreurEnvoiRapport:
        raise
    except Exception as err:
        raise ErreurEnvoiRapport(
            "L'envoi a echoue ou son statut est incertain. "
            "Verifiez la configuration et le statut avant tout nouvel essai."
        ) from err

    return destinataire
