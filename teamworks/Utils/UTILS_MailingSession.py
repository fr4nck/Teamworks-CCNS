# -*- coding: utf-8 -*-
"""Session d'envoi du Mailer wx : aucun accès wx depuis le worker.

Le transport est entièrement séquentiel. Une erreur pendant Envoyer() est
considérée comme INCERTAINE : aucun renvoi automatique n'est autorisé.
Les dialogues restent sur le thread GUI, via wx.CallAfter.
"""

from dataclasses import dataclass, field
from threading import Event, Thread
import time


@dataclass
class BilanEnvoi:
    succes: list = field(default_factory=list)
    refuses: list = field(default_factory=list)
    incertains: list = field(default_factory=list)
    non_tentes: list = field(default_factory=list)
    erreur_connexion: object = None
    erreur_fermeture: object = None


def envoyer_lot_sans_wx(fabrique, messages, progression=None, decision=None,
                       delai=1.0, pause=time.sleep):
    """Envoie un lot séquentiel, sans dépendance graphique ni relance cachée.

    Un résultat faux signifie refus/non-confirmation explicite. Une exception
    pendant l'envoi est toujours classée « incertain », même si la transmission
    a peut-être réussi. decision(categorie, message, erreur, index, total)
    décide seulement de continuer vers le *message suivant*, jamais de renvoyer.
    """
    messages = list(messages)
    bilan = BilanEnvoi()
    connexion = None
    try:
        try:
            connexion = fabrique()
            connexion.Connecter()
        except Exception as erreur:
            bilan.erreur_connexion = erreur
            bilan.non_tentes.extend(messages)
            return bilan

        total = len(messages)
        for indice, message in enumerate(messages):
            if progression is not None:
                progression(indice + 1, total)

            categorie = None
            erreur = None
            try:
                accepte = connexion.Envoyer(message)
            except Exception as exc:
                categorie = "incertain"
                erreur = exc
                bilan.incertains.append((message, exc))
            else:
                if accepte:
                    bilan.succes.append(message)
                else:
                    categorie = "refuse"
                    erreur = RuntimeError("Le serveur n'a pas confirmé l'acceptation")
                    bilan.refuses.append((message, erreur))

            if categorie is not None:
                continuer = False
                if decision is not None:
                    try:
                        continuer = bool(decision(
                            categorie, message, erreur, indice + 1, total
                        ))
                    except Exception:
                        continuer = False
                if not continuer:
                    bilan.non_tentes.extend(messages[indice + 1:])
                    break

            if indice + 1 < total and delai:
                pause(delai)
    finally:
        if connexion is not None:
            try:
                connexion.Fermer()
            except Exception as exc:
                bilan.erreur_fermeture = exc
    return bilan


def proprietaire_visible(fenetre, wx):
    """Remonte les parents avant de consulter la fenêtre principale wx."""
    courant = fenetre
    while courant is not None:
        if courant.IsShownOnScreen():
            return courant
        courant = courant.GetParent()
    app = wx.GetApp()
    principale = app.GetTopWindow() if app is not None else None
    if principale is not None and principale.IsShownOnScreen():
        return principale
    return None


def envoyer_avec_progression(parent, fabrique, messages,
                             afficher_confirmation_envoi=True):
    """Pont synchrone pour les appelants historiques, GUI wx toujours réactive.

    ShowModal utilise la boucle d'événements wx pendant que le worker exécute
    exclusivement le réseau et l'attente anti-spam. Aucune fenêtre n'est créée
    ou modifiée par le worker, hors wx.CallAfter.
    """
    import wx
    from Utils.UTILS_Traduction import _
    from Dlg import DLG_Messagebox

    if parent is None or not parent.IsShownOnScreen():
        raise RuntimeError("Propriétaire visible du Mailer introuvable")

    messages = list(messages)
    dialogue = wx.Dialog(parent, title=_(u"Envoi des mails"),
                         style=wx.DEFAULT_DIALOG_STYLE)
    conteneur = wx.BoxSizer(wx.VERTICAL)
    etat = wx.StaticText(dialogue, label=_(u"Connexion au serveur de messagerie..."))
    jauge = wx.Gauge(dialogue, range=max(1, len(messages)))
    conteneur.Add(etat, 0, wx.ALL | wx.EXPAND, 12)
    conteneur.Add(jauge, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
    dialogue.SetSizerAndFit(conteneur)
    dialogue.SetMinSize((450, 140))
    dialogue.SetSize((450, 140))
    dialogue.CenterOnParent()

    resultat = {}
    def _progression(numero, total):
        def afficher():
            etat.SetLabel(_(u"Envoi %d/%d...") % (numero, total))
            jauge.SetValue(numero - 1)
        wx.CallAfter(afficher)

    def _decision(categorie, message, erreur, numero, total):
        if numero >= total:
            return False
        evenement = Event()
        choix = {"continuer": False}
        def demander():
            try:
                if categorie == "incertain":
                    explication = _(u"Statut incertain : le serveur peut avoir reçu ce message. Aucun renvoi automatique.")
                else:
                    explication = _(u"Le serveur n'a pas confirmé l'acceptation de ce message.")
                texte = _(u"%s\n\nContinuer avec les autres destinataires ?") % explication
                dlg = wx.MessageDialog(dialogue, texte, _(u"Erreur d'envoi"),
                                       wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
                try:
                    choix["continuer"] = dlg.ShowModal() == wx.ID_YES
                finally:
                    dlg.Destroy()
            finally:
                evenement.set()
        wx.CallAfter(demander)
        evenement.wait()
        return choix["continuer"]

    def _terminer():
        if dialogue.IsModal():
            dialogue.EndModal(wx.ID_OK)

    def _travail():
        try:
            resultat["bilan"] = envoyer_lot_sans_wx(
                fabrique, messages, progression=_progression, decision=_decision
            )
        except Exception as exc:
            resultat["erreur_inattendue"] = exc
        finally:
            wx.CallAfter(_terminer)

    worker = Thread(target=_travail, name="teamworks-mailer", daemon=False)
    def _fermeture(event):
        if worker.is_alive():
            event.Veto()
        else:
            event.Skip()
    dialogue.Bind(wx.EVT_CLOSE, _fermeture)

    try:
        worker.start()
        dialogue.ShowModal()
        worker.join()
    finally:
        dialogue.Destroy()

    if "erreur_inattendue" in resultat:
        raise resultat["erreur_inattendue"]
    bilan = resultat["bilan"]

    if bilan.erreur_connexion is not None:
        dlg = DLG_Messagebox.Dialog(
            parent, titre=_(u"Erreur"),
            introduction=_(u"La connexion au serveur de messagerie est impossible :"),
            detail=str(bilan.erreur_connexion),
            conclusion=_(u"Vérifiez votre connexion internet ou les paramètres de votre adresse d'expédition."),
            icone=wx.ICON_ERROR, boutons=[_(u"Ok")]
        )
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
        return bilan

    incidents = [(msg, err, "refuse") for msg, err in bilan.refuses]
    incidents.extend((msg, err, "incertain") for msg, err in bilan.incertains)
    if incidents:
        lignes = []
        for message, erreur, categorie in incidents:
            description = _(u"statut incertain, ne pas renvoyer automatiquement") if categorie == "incertain" else _(u"refus / absence de confirmation")
            lignes.append(u"- %s : %s (%s)" % (
                message.GetLabelDestinataires(), description, type(erreur).__name__
            ))
        dlg = DLG_Messagebox.Dialog(
            parent, titre=_(u"Compte-rendu de l'envoi"),
            introduction=_(u"%d accepté(s), %d incertain(s), %d refusé(s), %d non tenté(s).") % (
                len(bilan.succes), len(bilan.incertains),
                len(bilan.refuses), len(bilan.non_tentes)),
            detail="\n".join(lignes),
            conclusion=_(u"Vérifiez le statut des messages incertains avant tout nouvel envoi."),
            icone=wx.ICON_WARNING, boutons=[_(u"Ok")]
        )
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
    elif afficher_confirmation_envoi:
        message = (_(u"L'Email a été envoyé avec succès !")
                   if len(bilan.succes) == 1
                   else _(u"Les %d Emails ont été envoyés avec succès !") % len(bilan.succes))
        dlg = wx.MessageDialog(parent, message, _(u"Fin de l'envoi"),
                               wx.OK | wx.ICON_INFORMATION)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    if bilan.erreur_fermeture is not None:
        dlg = wx.MessageDialog(
            parent,
            _(u"L'envoi est terminé mais la fermeture de la connexion a échoué."),
            _(u"Avertissement"), wx.OK | wx.ICON_WARNING
        )
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
    return bilan
