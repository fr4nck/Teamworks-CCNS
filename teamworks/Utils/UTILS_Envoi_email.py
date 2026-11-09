#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
import socket
import os
import sys
import time
import GestionDB
import FonctionsPerso
import re
import traceback
import base64
from Utils import UTILS_Html2text
from Utils import UTILS_Parametres
from Utils import UTILS_Mailing
from Dlg import DLG_Messagebox

import smtplib
from Utils import UTILS_Encodage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from email.utils import formatdate
from email import encoders
import mimetypes

from Outils import mail

# Import pour permettre compilation windows
from Outils.mail import base, smtp



def EnvoiEmailFamille(parent=None, IDfamille=None, nomDoc="", categorie="", listeAdresses=None, visible=True, log=None, CreationPDF=None, IDmodele=None):
    # Création du PDF
    if listeAdresses is None:
        listeAdresses = []
    if CreationPDF != None :
        temp = CreationPDF
    else :
        temp = parent.CreationPDF
    dictChamps = temp(nomDoc=nomDoc, afficherDoc=False)
    if dictChamps == False :
        return False

    if nomDoc != False :
        liste_pieces = [nomDoc,]
    else :
        liste_pieces = []

    # Recherche adresse famille
    if len(listeAdresses) == 0 :
        listeAdresses = GetAdresseFamille(IDfamille)
        if len(listeAdresses) == 0 :
            return False
    
    # DLG Mailer
    listeDonnees = []
    for adresse in listeAdresses :
        listeDonnees.append({
            "adresse" : adresse, 
            "pieces" : liste_pieces,
            "champs" : dictChamps,
            })
    from Dlg import DLG_Mailer
    dlg = DLG_Mailer.Dialog(parent, categorie=categorie, afficher_confirmation_envoi=visible)
    dlg.SetDonnees(listeDonnees, modificationAutorisee=False)
    if IDmodele == None :
        dlg.ChargerModeleDefaut()
    else :
        dlg.ChargerModele(IDmodele)

    if visible == True :
        # Fenêtre visible
        dlg.ShowModal()

    else :
        # Fenêtre cachée
        dlg.OnBoutonEnvoyer(None)

    if len(dlg.listeSucces) > 0 :
        resultat = True
        if log : log.EcritLog(_(u"L'Email a été envoyé avec succès."))
    else :
        resultat = False
        if log : log.EcritLog(_(u"L'email n'a pas été envoyé."))

    dlg.Destroy()

    # Suppression du PDF temporaire
    if nomDoc != False :
        try :
            os.remove(nomDoc)
        except :
            pass

    return resultat



def ValidationEmail(email):
    """Compatibilité historique : délègue au validateur moderne unique."""
    return UTILS_Mailing.IsValidEmail(email)


def GetAdresseExpDefaut():
    """ Retourne les paramètres de l'adresse d'expéditeur par défaut """
    return GetAdresseExp(IDadresse=None)

def GetAdresseExp(IDadresse=None):
    """ Si IDadresse = None, retourne l'adresse par défaut"""
    if IDadresse == None :
        condition = "defaut=1"
    else :
        condition = "IDadresse=%d" % IDadresse
    # Récupération des données
    DB = GestionDB.DB()        
    req = """SELECT IDadresse, moteur, adresse, nom_adresse, motdepasse, smtp, port, defaut, connexionAuthentifiee, startTLS, utilisateur, parametres
    FROM adresses_mail WHERE %s ORDER BY adresse;""" % condition
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) == 0 : return None
    IDadresse, moteur, adresse, nom_adresse, motdepasse, smtp, port, defaut, auth, startTLS, utilisateur, parametres = listeDonnees[0]
    dictAdresse = {"adresse":adresse, "moteur": moteur, "nom_adresse":nom_adresse, "motdepasse":motdepasse,
                   "smtp":smtp, "port":port, "auth" : auth, "startTLS":startTLS, "utilisateur" : utilisateur, "parametres": parametres}
    return dictAdresse

def GetAdresseFamille(IDfamille=None, choixMultiple=True, muet=False, nomTitulaires=None):
    """ Récupère l'adresse email de la famille """
    # Récupération du nom de la famille
    if nomTitulaires == None :
        dictTitulaires = UTILS_Titulaires.GetTitulaires([IDfamille,])
        if IDfamille in dictTitulaires:
            nomTitulaires = dictTitulaires[IDfamille]["titulairesSansCivilite"]
        else :
            nomTitulaires = _(u"Famille inconnue")
    # Récupération des adresses mails de chaque membre de la famille
    DB = GestionDB.DB()
    req = """
    SELECT 
    rattachements.IDindividu, IDcategorie,
    individus.nom, individus.prenom, individus.mail, individus.travail_mail
    FROM rattachements 
    LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
    WHERE IDcategorie IN (1, 2) AND IDfamille=%d
    ;""" % IDfamille
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close() 
    listeAdresses = []
    listeTemp = []
    for IDindividu,  IDcategorie, nom, prenom, mailPerso, mailTravail in listeDonnees :
        if mailPerso != None and mailPerso != "" and mailPerso not in listeTemp :
            listeAdresses.append((_(u"%s (Adresse perso de %s)") % (mailPerso, prenom), mailPerso))
            listeTemp.append(mailPerso)
        if mailTravail != None and mailTravail != "" and mailTravail not in listeTemp :
            listeAdresses.append((_(u"%s (Adresse pro de %s)") % (mailTravail, prenom), mailTravail))
            listeTemp.append(mailTravail)
    if len(listeAdresses) == 0 :
        if muet == False :
            dlg = wx.MessageDialog(None, _(u"Aucun membre de la famille de %s ne dispose d'adresse mail !") % nomTitulaires, "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        return []
    elif len(listeAdresses) == 1 :
        listeMails = [listeAdresses[0][1],]
    else:
        listeLabels = []
        listeMails = []
        for label, adresse in listeAdresses :
            listeLabels.append(label)
        if choixMultiple == True :
            dlg = wx.MultiChoiceDialog(None, _(u"%d adresses internet sont disponibles pour la famille de %s.\nSélectionnez celles que vous souhaitez utiliser puis cliquez sur le bouton 'Ok' :") % (len(listeAdresses), nomTitulaires), _(u"Choix d'adresses Emails"), listeLabels)
        else :
            dlg = wx.SingleChoiceDialog(None, _(u"%d adresses internet sont disponibles pour la famille de %s.\nSélectionnez celle que vous souhaitez utiliser puis cliquez sur le bouton 'Ok' :") % (len(listeAdresses), nomTitulaires), _(u"Choix d'une adresse Email"), listeLabels)
        dlg.SetSize((450, -1))
        dlg.CenterOnScreen() 
        if dlg.ShowModal() == wx.ID_OK :
            if choixMultiple == True :
                selections = dlg.GetSelections()
            else :
                selections = [dlg.GetSelection(),]
            dlg.Destroy()
            if len(selections) == 0 :
                dlg = wx.MessageDialog(None, _(u"Vous n'avez sélectionné aucune adresse mail !"), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return []
            for index in selections :
                listeMails.append(listeAdresses[index][1])
        else:
            dlg.Destroy()
            return []
    
    if choixMultiple == True :
        return listeMails
    else :
        return listeMails[0]





class Message():
    def __init__(self, destinataires=None, sujet="", texte_html="", fichiers=None, images=None, champs=None):
        if destinataires is None:
            destinataires = []
        if fichiers is None:
            fichiers = []
        if images is None:
            images = []
        if champs is None:
            champs = {}
        self.destinataires = destinataires
        self.sujet = sujet
        self.fichiers = fichiers
        self.images = images
        self.texte_html = texte_html
        self.champs = champs

        # Corrige le pb des images embarquées
        index = 0
        for img in images:
            img = img.replace(u"\\", u"/")
            img = img.replace(u":", u"%3a")
            self.texte_html = self.texte_html.replace(u"file:/%s" % img, u"cid:image%d" % index)
            index += 1

        # Conversion du html en texte plain
        self.texte_plain = UTILS_Html2text.html2text(self.texte_html)

    def AttacheImagesIncluses(self, email=None):
        index = 0
        for img in self.images:
            fp = open(img, 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            msgImage.add_header('Content-ID', '<image%d>' % index)
            msgImage.add_header('Content-Disposition', 'inline', filename=img)
            email.attach(msgImage)
            index += 1

    def AttacheFichiersJoints(self, email=None):
        for fichier in self.fichiers:
            """Guess the content type based on the file's extension. Encoding
            will be ignored, altough we should check for simple things like
            gzip'd or compressed files."""
            ctype, encoding = mimetypes.guess_type(fichier)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compresses), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            if maintype == 'text':
                fp = open(fichier)
                # Note : we should handle calculating the charset
                part = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'image':
                fp = open(fichier, 'rb')
                part = MIMEImage(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(fichier, 'rb')
                part = MIMEBase(maintype, subtype)
                part.set_payload(fp.read())
                fp.close()
                # Encode the payload using Base64
                encoders.encode_base64(part)
            # Set the filename parameter
            nomFichier = os.path.basename(fichier)
            if isinstance(nomFichier, str):
                nomFichier = FonctionsPerso.Supprime_accent(nomFichier)
            # changement cosmetique pour ajouter les guillements autour du filename
            part.add_header('Content-Disposition', "attachment; filename=\"%s\"" % nomFichier)
            email.attach(part)

    def GetLabelDestinataires(self):
        return ";".join(self.destinataires)



def Messagerie(backend='smtp', **kwds):
    """Construit un backend après validation déterministe de sa configuration."""
    config = UTILS_Mailing.ValidateBackendConfig(
        backend=backend,
        email_exp=kwds.get("email_exp"),
        host=kwds.get("hote"),
        port=kwds.get("port"),
        username=kwds.get("utilisateur"),
        password=kwds.get("motdepasse"),
        use_tls=kwds.get("use_tls", False),
        parameters=kwds.get("parametres"),
    )

    kwds["hote"] = config["host"]
    kwds["port"] = config["port"]
    kwds["utilisateur"] = config["username"]
    kwds["motdepasse"] = config["password"]
    kwds["email_exp"] = config["email_exp"]
    kwds["use_tls"] = config["use_tls"]
    kwds["parametres"] = UTILS_Mailing.SerializeBackendParameters(config["parameters"])

    classes = {
        "smtp_obsolete": SmtpV1,
        "smtp": SmtpV2,
        "mailjet": Mailjet,
    }
    return classes[config["backend"]](**kwds)




class Base_messagerie():
    def __init__(self, hote=None, port=None, utilisateur=None, motdepasse=None, email_exp=None, nom_exp=None, timeout=None, use_tls=False, fail_silently=False, parametres=None):
        self.hote = hote
        self.port = port
        self.utilisateur = utilisateur
        self.motdepasse = motdepasse
        self.email_exp = email_exp
        self.nom_exp = nom_exp
        self.timeout = timeout
        self.use_tls = use_tls
        self.fail_silently = fail_silently
        self.parametres = parametres

        if self.utilisateur == "" : self.utilisateur = None
        if self.motdepasse == "" : self.motdepasse = None

        # Timeout
        timeout = UTILS_Parametres.Parametres(mode="get", categorie="email", nom="timeout", valeur=None)
        if timeout not in ("", None):
            self.timeout = int(timeout)

        # Préparation de l'adresse d'expédition
        if self.nom_exp not in ("", None):
            self.from_email = u"%s <%s>" % (self.nom_exp, self.email_exp)
        else :
            self.from_email = self.email_exp

        # Formatage des paramètres
        self.dict_parametres = UTILS_Mailing.ParseBackendParameters(parametres, strict=True)


    def Connecter(self):
        pass

    def Envoyer(self, message=None):
        pass

    def Fermer(self):
        pass





    def Envoyer_lot(self, messages=None, dlg_progress=None,
                   afficher_confirmation_envoi=True):
        """Compatibilite de l'ancien contrat : connexion deja ouverte."""
        from Utils import UTILS_MailingSession
        return UTILS_MailingSession.envoyer_lot_heritage(
            self, messages=messages, dlg_progress=dlg_progress,
            afficher_confirmation_envoi=afficher_confirmation_envoi
        )


class SmtpV1(Base_messagerie):
    def __init__(self, **kwds):
        Base_messagerie.__init__(self, **kwds)

    def Connecter(self):
        try :
            if self.utilisateur is None and self.motdepasse is None:
                if self.port is None:
                    self.connection = smtplib.SMTP(self.hote, timeout=self.timeout)
                else:
                    self.connection = smtplib.SMTP(self.hote, self.port, timeout=self.timeout)
            else:
                # Si identification SSL nécessaire :
                self.connection = smtplib.SMTP(self.hote, self.port, timeout=self.timeout)
                self.connection.ehlo()
                if self.use_tls == True:
                    self.connection.starttls()
                    self.connection.ehlo()
                self.connection.login(self.utilisateur.encode('utf-8'), self.motdepasse.encode('utf-8'))
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise

    def Envoyer(self, message=None):
        # Création du message
        email = MIMEMultipart('alternative')
        # msg['Message-ID'] = make_msgid()

        # if accuseReception == True:
        #     msg['Disposition-Notification-To'] = adresseExpediteur

        email.attach(MIMEText(message.texte_plain.encode('utf-8'), 'plain', 'utf-8'))
        email.attach(MIMEText(message.texte_html.encode('utf-8'), 'html', 'utf-8'))

        tmpmsg = email
        email = MIMEMultipart('mixed')
        email.attach(tmpmsg)

        # Ajout des en-têtes à ce Multipart
        if self.nom_exp in ("", None):
            email['From'] = self.email_exp
        else:
            sender = Header(self.nom_exp, "utf-8")
            sender.append(self.email_exp, "ascii")
            email['From'] = sender  # formataddr((nomadresseExpediteur, adresseExpediteur))
        email['To'] = ";".join(message.destinataires)
        email['Date'] = formatdate(localtime=True)
        email['Subject'] = message.sujet

        message.AttacheImagesIncluses(email)
        message.AttacheFichiersJoints(email)

        try:
            refus = self.connection.sendmail(
                self.email_exp, message.destinataires, email.as_string()
            )
            if refus:
                # Un succes partiel ne doit jamais entrainer un renvoi.
                raise RuntimeError("Resultat SMTP partiel : statut incertain")
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False
        return True

    def Fermer(self):
        self.connection.close()





class SmtpV2(Base_messagerie):
    def __init__(self, **kwds):
        Base_messagerie.__init__(self, **kwds)

    def Connecter(self):
        try :
            self.connection = mail.get_connection(backend='Outils.mail.smtp.EmailBackend', fail_silently=self.fail_silently,
                                             host=self.hote, port=self.port, username=self.utilisateur, password=self.motdepasse,
                                             use_tls=self.use_tls, use_ssl=False, timeout=self.timeout, ssl_keyfile=None, ssl_certfile=None)
            self.connection.open()
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise


    def Envoyer(self, message=None):
        email = mail.EmailMultiAlternatives(
            subject=message.sujet,
            body=message.texte_plain,
            from_email=self.from_email,
            to=message.destinataires,
            connection=self.connection,
        )

        email.attach_alternative(message.texte_html, "text/html")

        message.AttacheImagesIncluses(email)
        message.AttacheFichiersJoints(email)

        resultat = email.send()
        return resultat

    def Fermer(self):
        self.connection.close()

class Mailjet(Base_messagerie):
    def __init__(self, **kwds):
        Base_messagerie.__init__(self, **kwds)

    def Connecter(self):
        # Récupération des clés Mailjet
        api_key = self.dict_parametres.get("api_key", None)
        api_secret = self.dict_parametres.get("api_secret", None)
        if not api_key or not api_secret:
            raise ValueError(u"Les codes MAILJET ne sont pas valides.")

        # Connexion à Mailjet
        try:
            from mailjet_rest import Client
            self.connection = Client(auth=(api_key, api_secret), version='v3.1')
        except Exception as err:
            raise

    def Envoyer(self, message=None):
        # Préparation du message
        dict_message = {
            "From": {"Email": self.email_exp, "Name": self.nom_exp},
            "To": [{"Email": destinataire} for destinataire in message.destinataires],
            "Subject": message.sujet,
            "TextPart": message.texte_plain,
            "HTMLPart": message.texte_html,
            "Attachments": [],
            "InlinedAttachments": [],
        }

        # Intégration des images incluses
        index = 0
        for fichier in message.images:
            ctype, encoding = mimetypes.guess_type(fichier)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            with open(fichier, "rb") as file:
                Base64Content = base64.b64encode(file.read())
            nom_fichier = os.path.basename(fichier)

            dict_fichier = {
                "ContentType": ctype,
                "Filename": nom_fichier,
                "ContentID": "image%d" % index,
                "Base64Content": Base64Content.decode("utf-8"),
            }
            dict_message["InlinedAttachments"].append(dict_fichier)
            index += 1

        # Intégration des pièces jointes
        for fichier in message.fichiers:
            ctype, encoding = mimetypes.guess_type(fichier)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            with open(fichier, "rb") as file:
                Base64Content = base64.b64encode(file.read())
            nom_fichier = os.path.basename(fichier)

            dict_fichier = {
                "ContentType": ctype,
                "Filename": nom_fichier,
                "Base64Content": Base64Content.decode("utf-8"),
            }
            dict_message["Attachments"].append(dict_fichier)

        # Envoi de la requête à Mailjet
        resultats = self.connection.send.create(data={"Messages": [dict_message,]})

        # Un Status JSON positif ne suffit pas si la requete HTTP a echoue.
        # Ne pas exposer de donnees de la reponse brute dans le diagnostic.
        statut_http = getattr(resultats, "status_code", None)
        if type(statut_http) is not int or not 200 <= statut_http < 300:
            raise RuntimeError(
                "Mailjet : statut HTTP non confirme, resultat d'envoi incertain"
            )

        # Analyse du résultat
        try:
            resultat = resultats.json()["Messages"][0][u'Status']
        except (ValueError, TypeError, KeyError, IndexError) as err:
            # La reponse API peut contenir des adresses et pieces jointes.
            # Ne jamais imprimer le JSON brut ni son contenu dans les logs.
            raise RuntimeError(
                "Reponse Mailjet illisible : statut d'envoi incertain"
            ) from err

        if resultat != u'success':
            raise RuntimeError("Mailjet : le serveur n'a pas confirme l'envoi")

        return resultat

    def Fermer(self):
        # Le client Mailjet n'expose pas necessairement close().
        fermer = getattr(getattr(self, "connection", None), "close", None)
        if callable(fermer):
            fermer()



if __name__ == u"__main__":
    # Préparation du message
    message = Message(destinataires=[""], sujet=u"Sujet du mail", texte_html="<p>Ceci est le <b>texte</b> html</p>", fichiers=[], images=[])

    # Envoi du message
    messagerie = Messagerie(backend='Mailjet', hote=None, port=None, utilisateur=None, motdepasse=None, email_exp=None, nom_exp=None, timeout=None, use_tls=False)
    messagerie.Connecter()
    messagerie.Envoyer(message)
    messagerie.Fermer()
