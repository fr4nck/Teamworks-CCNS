# -*- coding: utf-8 -*-
"""TW-UI-01 : aucun réseau réel, aucun wx graphique, aucune donnée RH."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "teamworks"))
from Utils.UTILS_MailingSession import envoyer_lot_sans_wx


class BackendFictif:
    def __init__(self, reponses=None, connexion_erreur=None, fermeture_erreur=None):
        self.reponses = list(reponses or [])
        self.connexion_erreur = connexion_erreur
        self.fermeture_erreur = fermeture_erreur
        self.appels = []
        self.fermetures = 0

    def Connecter(self):
        if self.connexion_erreur:
            raise self.connexion_erreur

    def Envoyer(self, message):
        self.appels.append(message)
        resultat = self.reponses.pop(0)
        if isinstance(resultat, Exception):
            raise resultat
        return resultat

    def Fermer(self):
        self.fermetures += 1
        if self.fermeture_erreur:
            raise self.fermeture_erreur


def test_timeout_apres_emission_est_incertain_et_ne_declenche_aucun_renvoi():
    backend = BackendFictif([TimeoutError("résultat inconnu"), True])
    decisions = []
    bilan = envoyer_lot_sans_wx(lambda: backend, ["a", "b"],
        decision=lambda categorie, message, err, numero, total:
            decisions.append((categorie, message)) or True,
        delai=0)
    assert backend.appels == ["a", "b"]
    assert len(bilan.incertains) == 1
    assert bilan.incertains[0][0] == "a"
    assert bilan.succes == ["b"]
    assert decisions == [("incertain", "a")]
    assert backend.fermetures == 1


def test_refus_n_est_pas_declare_accepte_et_arret_conserve_non_tentes():
    backend = BackendFictif([False, True, True])
    bilan = envoyer_lot_sans_wx(lambda: backend, ["a", "b", "c"], delai=0)
    assert backend.appels == ["a"]
    assert bilan.succes == []
    assert len(bilan.refuses) == 1
    assert bilan.non_tentes == ["b", "c"]
    assert backend.fermetures == 1


def test_erreur_de_connexion_n_entraine_aucune_tentative():
    backend = BackendFictif(connexion_erreur=OSError("offline"))
    bilan = envoyer_lot_sans_wx(lambda: backend, ["a", "b"], delai=0)
    assert backend.appels == []
    assert bilan.non_tentes == ["a", "b"]
    assert isinstance(bilan.erreur_connexion, OSError)
    assert backend.fermetures == 1


def test_lent_travail_d_attente_reste_hors_de_la_couche_wx():
    backend = BackendFictif([True, True])
    pauses = []
    progression = []
    bilan = envoyer_lot_sans_wx(lambda: backend, ["a", "b"],
        progression=lambda i, n: progression.append((i, n)),
        delai=1, pause=pauses.append)
    assert bilan.succes == ["a", "b"]
    assert pauses == [1]
    assert progression == [(1, 2), (2, 2)]


def test_fermeture_en_erreur_ne_change_pas_un_succes_en_echec():
    backend = BackendFictif([1], fermeture_erreur=OSError("close"))
    bilan = envoyer_lot_sans_wx(lambda: backend, ["a"], delai=0)
    assert bilan.succes == ["a"]
    assert isinstance(bilan.erreur_fermeture, OSError)


def test_le_mailer_conserve_son_contrat_synchrone_et_son_proprietaire():
    mailer = (ROOT / "teamworks" / "Dlg" / "DLG_Mailer.py").read_text(encoding="utf-8")
    session = (ROOT / "teamworks" / "Utils" / "UTILS_MailingSession.py").read_text(encoding="utf-8")
    assert "envoyer_avec_progression(" in mailer
    assert "proprietaire_visible(self, wx)" in mailer
    assert "worker = Thread(" in session
    assert "wx.CallAfter(" in session
    assert "dialogue.ShowModal()" in session
    assert "time.sleep(" not in mailer
