# -*- coding: utf-8 -*-
"""TW-UI-01 Phase 3 : qualification des vraies methodes, sans reseau.

On compile les classes de UTILS_Envoi_email.py directement depuis l'AST :
les dependances wx/MySQL ne sont jamais importees et les methodes
transportees sont bien celles de l'application, pas des copies dans les tests.
"""
import ast
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import mimetypes
from pathlib import Path
import smtplib
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
if str(TEAMWORKS) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS))

from Utils import UTILS_Mailing
from Utils import UTILS_MailingSession


def _types_transport(fake_smtp=None, fake_mail=None):
    source = (TEAMWORKS / "Utils" / "UTILS_Envoi_email.py").read_text(
        encoding="utf-8"
    )
    arbre = ast.parse(source)
    noms = {"Base_messagerie", "SmtpV1", "SmtpV2", "Mailjet"}
    classes = [
        item for item in arbre.body
        if isinstance(item, ast.ClassDef) and item.name in noms
    ]
    assert [item.name for item in classes] == [
        "Base_messagerie", "SmtpV1", "SmtpV2", "Mailjet"
    ]
    fake_smtp = fake_smtp or types.SimpleNamespace(
        SMTP=lambda *a, **k: None,
        SMTPException=smtplib.SMTPException,
    )
    scope = {
        "smtplib": fake_smtp,
        "MIMEMultipart": MIMEMultipart,
        "MIMEText": MIMEText,
        "Header": Header,
        "formatdate": formatdate,
        "mail": fake_mail,
        "mimetypes": mimetypes,
        "os": __import__("os"),
        "base64": __import__("base64"),
        "UTILS_Mailing": UTILS_Mailing,
        "UTILS_Parametres": types.SimpleNamespace(
            Parametres=lambda **kw: None
        ),
    }
    exec(
        compile(ast.Module(body=classes, type_ignores=[]), "UTILS_Envoi_email.py", "exec"),
        scope,
    )
    return scope


class MessageFictif:
    destinataires = ["fictif@example.test"]
    sujet = "Test fictif"
    texte_plain = "Test"
    texte_html = "<p>Test</p>"
    images = ()
    fichiers = ()

    def AttacheImagesIncluses(self, email):
        pass

    def AttacheFichiersJoints(self, email):
        pass


class FausseSMTP:
    def __init__(self, reponse=None, erreur=None, erreur_connexion=None):
        self.reponse = reponse
        self.erreur = erreur
        self.erreur_connexion = erreur_connexion
        self.appels = []
        self.fermetures = 0

    def sendmail(self, adresse, destinataires, texte):
        self.appels.append((adresse, destinataires, texte))
        if self.erreur:
            raise self.erreur
        return self.reponse

    def close(self):
        self.fermetures += 1

    def ehlo(self):
        pass

    def starttls(self):
        pass

    def login(self, user, password):
        if self.erreur_connexion:
            raise self.erreur_connexion


def _backend(classes, nom):
    return classes[nom](
        hote="smtp.invalid", port=2525,
        email_exp="expediteur@example.test", nom_exp=None, timeout=3,
        utilisateur=None, motdepasse=None,
        parametres="api_key==FAUX##api_secret==FAUX",
    )


def test_smtp_v1_accepte_une_reponse_smtp_vide(monkeypatch):
    smtp = FausseSMTP(reponse={})
    classes = _types_transport(
        fake_smtp=types.SimpleNamespace(
            SMTP=lambda *a, **kw: smtp,
            SMTPException=smtplib.SMTPException,
        ),
    )
    backend = _backend(classes, "SmtpV1")
    bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
        lambda: backend, [MessageFictif()], delai=0,
    )
    assert len(bilan.succes) == 1
    assert not bilan.incertains
    assert len(smtp.appels) == 1
    assert smtp.fermetures == 1


def test_smtp_v1_acceptation_partielle_n_est_pas_un_succes():
    smtp = FausseSMTP(reponse={"nonaccepte@example.test": (550, "refus")})
    classes = _types_transport(
        fake_smtp=types.SimpleNamespace(
            SMTP=lambda *a, **kw: smtp,
            SMTPException=smtplib.SMTPException,
        ),
    )
    backend = _backend(classes, "SmtpV1")
    messages = [MessageFictif(), MessageFictif()]
    bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
        lambda: backend, messages, delai=0,
    )
    assert not bilan.succes
    assert len(bilan.incertains) == 1
    assert bilan.non_tentes == [messages[1]]
    assert len(smtp.appels) == 1


def test_smtp_v1_deconnexion_apres_essai_n_est_pas_renvoyee():
    smtp = FausseSMTP(erreur=smtplib.SMTPServerDisconnected("deconnexion"))
    classes = _types_transport(
        fake_smtp=types.SimpleNamespace(
            SMTP=lambda *a, **kw: smtp,
            SMTPException=smtplib.SMTPException,
        ),
    )
    bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
        lambda: _backend(classes, "SmtpV1"), [MessageFictif()], delai=0,
    )
    assert not bilan.succes
    assert len(bilan.incertains) == 1
    assert len(smtp.appels) == 1


def test_smtp_v1_connexion_authentifiee_refusee_ne_transmet_rien():
    smtp = FausseSMTP(erreur_connexion=smtplib.SMTPAuthenticationError(535, b"refus"))
    classes = _types_transport(
        fake_smtp=types.SimpleNamespace(
            SMTP=lambda *a, **kw: smtp,
            SMTPException=smtplib.SMTPException,
        ),
    )
    backend = _backend(classes, "SmtpV1")
    backend.utilisateur, backend.motdepasse = "fictif", "fictif"
    bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
        lambda: backend, [MessageFictif()], delai=0,
    )
    assert bilan.erreur_connexion is not None
    assert len(bilan.non_tentes) == 1
    assert smtp.appels == []


@pytest.mark.parametrize("reponse,accepte", [(0, False), (1, True)])
def test_smtp_v2_reponse_de_bibliotheque_et_fermeture(reponse, accepte):
    connexions = []
    transmissions = []

    class Connexion:
        def open(self):
            connexions.append("open")
        def close(self):
            connexions.append("close")

    connection = Connexion()

    class MessageSMTPV2:
        def __init__(self, **kwargs):
            assert kwargs["connection"] is connection
        def attach_alternative(self, html, mime):
            assert mime == "text/html"
        def send(self):
            transmissions.append("send")
            return reponse

    mail = types.SimpleNamespace(
        get_connection=lambda **kwargs: connection,
        EmailMultiAlternatives=MessageSMTPV2,
    )
    classes = _types_transport(fake_mail=mail)
    bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
        lambda: _backend(classes, "SmtpV2"), [MessageFictif()], delai=0,
    )
    assert len(bilan.succes) == int(accepte)
    assert len(bilan.refuses) == int(not accepte)
    assert transmissions == ["send"]
    assert connexions == ["open", "close"]


@pytest.mark.parametrize("code,etat,ok", [
    (200, "success", True),
    (201, "success", True),
    (400, "success", False),
    (429, "success", False),
    (500, "success", False),
    (200, "error", False),
    (200, None, False),
])
def test_mailjet_contrat_http_et_reponse_json(monkeypatch, code, etat, ok):
    appels = []
    fermetures = []
    class Reponse:
        status_code = code
        def json(self):
            return {"Messages": [{"Status": etat}]}
    class Client:
        def __init__(self, auth, version):
            assert auth == ("FAUX", "FAUX") and version == "v3.1"
            self.send = types.SimpleNamespace(create=self._envoyer)
        def _envoyer(self, data):
            appels.append(data)
            return Reponse()
        def close(self):
            fermetures.append("close")
    monkeypatch.setitem(sys.modules, "mailjet_rest", types.SimpleNamespace(Client=Client))
    classes = _types_transport()
    bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
        lambda: _backend(classes, "Mailjet"), [MessageFictif()], delai=0,
    )
    assert len(appels) == 1
    assert appels[0]["Messages"][0]["To"] == [
        {"Email": "fictif@example.test"}
    ]
    assert len(bilan.succes) == int(ok)
    assert len(bilan.incertains) == int(not ok)
    assert fermetures == ["close"]


def test_mailjet_reponse_malformee_est_incertaine_sans_trace_sensitive(monkeypatch, capsys):
    class Client:
        def __init__(self, auth, version):
            self.send = types.SimpleNamespace(create=lambda data: self)
        status_code = 200
        def json(self):
            raise ValueError("secret ne doit pas apparaitre dans les logs")
        def close(self):
            pass
    monkeypatch.setitem(sys.modules, "mailjet_rest", types.SimpleNamespace(Client=Client))
    classes = _types_transport()
    bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
        lambda: _backend(classes, "Mailjet"), [MessageFictif()], delai=0,
    )
    assert len(bilan.incertains) == 1
    assert "secret" not in (capsys.readouterr().out + capsys.readouterr().err)


def test_mailjet_timeout_apres_envoi_reste_incertain(monkeypatch):
    appels = []
    class Client:
        def __init__(self, auth, version):
            self.send = types.SimpleNamespace(create=self._envoyer)
        def _envoyer(self, data):
            appels.append(data)
            raise TimeoutError("transmission possiblement acceptee")
        def close(self):
            pass
    monkeypatch.setitem(sys.modules, "mailjet_rest", types.SimpleNamespace(Client=Client))
    classes = _types_transport()
    bilan = UTILS_MailingSession.envoyer_lot_sans_wx(
        lambda: _backend(classes, "Mailjet"), [MessageFictif()], delai=0,
    )
    assert len(appels) == 1
    assert len(bilan.incertains) == 1
    assert len(bilan.succes) == 0


def test_smtp_et_mailjet_sont_produits_par_les_methodes_reelles():
    source = (TEAMWORKS / "Utils" / "UTILS_Envoi_email.py").read_text(encoding="utf-8")
    assert "statut_http = getattr(resultats, \"status_code\", None)" in source
    assert "200 <= statut_http < 300" in source
    assert "self.connection.sendmail(" in source
    assert "email.send()" in source
