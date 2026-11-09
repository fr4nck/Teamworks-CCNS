# -*- coding: utf-8 -*-
"""TW-UI-01 phase 2 : SMTP/Mailjet fictifs, sans serveur et sans base RH."""
import ast
from pathlib import Path
import queue
import re
import sys
import threading
import time
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "teamworks"))
from Utils import UTILS_MailingSession as session


class Transport:
    def __init__(self, reponses, connexion_erreur=None):
        self.reponses = list(reponses)
        self.connexion_erreur = connexion_erreur
        self.appels = []
        self.connexions = 0
        self.fermetures = 0

    def Connecter(self):
        self.connexions += 1
        if self.connexion_erreur:
            raise self.connexion_erreur

    def Envoyer(self, message):
        self.appels.append(message)
        response = self.reponses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def Fermer(self):
        self.fermetures += 1


@pytest.mark.parametrize("reponse", [False, 0, None, "error", "partial", {}, -1])
def test_reponse_non_confirmee_jamais_comptee_comme_succes(reponse):
    transport = Transport([reponse])
    bilan = session.envoyer_lot_sans_wx(lambda: transport, ["fictif"], delai=0)
    assert bilan.succes == []
    assert len(bilan.refuses) == 1
    assert bilan.incertains == []
    assert transport.appels == ["fictif"]
    assert transport.fermetures == 1


@pytest.mark.parametrize("reponse", [True, 1, 2, "success"])
def test_reponses_positives_precises_de_smtp_et_mailjet(reponse):
    transport = Transport([reponse])
    bilan = session.envoyer_lot_sans_wx(lambda: transport, ["fictif"], delai=0)
    assert bilan.succes == ["fictif"]
    assert not bilan.refuses and not bilan.incertains


def test_deconnexion_apres_emission_est_incertaine_sans_repetition():
    transport = Transport([ConnectionResetError("deconnexion"), 1])
    decisions = []
    bilan = session.envoyer_lot_sans_wx(
        lambda: transport, ["a", "b"], delai=0,
        decision=lambda categorie, msg, err, i, n: (
            decisions.append((categorie, msg)) or True
        ),
    )
    assert transport.appels == ["a", "b"]
    assert bilan.succes == ["b"]
    assert [m for m, _ in bilan.incertains] == ["a"]
    assert decisions == [("incertain", "a")]
    assert transport.connexions == 1


def test_diagnostic_des_anciens_parcours_utilise_une_seule_definition():
    source = (ROOT / "teamworks/Utils/UTILS_Envoi_email.py").read_text(encoding="utf-8")
    arbre = ast.parse(source)
    definitions = [
        (cls.name, item)
        for cls in arbre.body if isinstance(cls, ast.ClassDef)
        for item in cls.body
        if isinstance(item, ast.FunctionDef) and item.name == "Envoyer_lot"
    ]
    assert [nom for nom, fn in definitions] == ["Base_messagerie"]
    assert "wx.ProgressDialog" not in source
    assert "time.sleep(1)" not in source
    assert "Tentative de reconnexion du serveur" not in source
    assert "envoyer_lot_heritage(" in source
    # Les trois transports heritent du meme adaptateur sans duplicata de boucle.
    assert "class SmtpV1(Base_messagerie)" in source
    assert "class SmtpV2(Base_messagerie)" in source
    assert "class Mailjet(Base_messagerie)" in source


def test_ancienne_signature_et_resultat_liste_conserves(monkeypatch):
    source = (ROOT / "teamworks/Utils/UTILS_Envoi_email.py").read_text(encoding="utf-8")
    arbre = ast.parse(source)
    classe = next(c for c in arbre.body if isinstance(c, ast.ClassDef) and c.name == "Base_messagerie")
    fonction = next(f for f in classe.body if isinstance(f, ast.FunctionDef) and f.name == "Envoyer_lot")
    scope = {}
    exec(compile(ast.Module(body=[fonction], type_ignores=[]), "<heritage>", "exec"), scope)
    appels = []
    monkeypatch.setattr(session, "envoyer_lot_heritage",
                        lambda *a, **k: appels.append((a, k)) or ["ok"])
    transport = Transport([1])
    resultat = scope["Envoyer_lot"](transport, messages=["fictif"],
                                      afficher_confirmation_envoi=False)
    assert resultat == ["ok"]
    assert appels[0][0][0] is transport
    assert appels[0][1]["messages"] == ["fictif"]


def test_adaptateur_legacy_reutilise_connexion_ouverte_sans_fermeture(monkeypatch):
    wx = types.ModuleType("wx")
    wx.IsMainThread = lambda: True
    monkeypatch.setitem(sys.modules, "wx", wx)
    parent = object()
    monkeypatch.setattr(session, "proprietaire_visible", lambda p, w: parent)
    backend = Transport([1])
    backend.connection = object()
    class Progress:
        def __init__(self):
            self.detruit = False
        def GetParent(self):
            return parent
        def Destroy(self):
            self.detruit = True
    progress = Progress()
    def faux_pont(parent, fabrique, messages, afficher_confirmation_envoi):
        transport = fabrique()
        transport.Connecter()
        assert transport.Envoyer("fictif") == 1
        transport.Fermer()
        return session.BilanEnvoi(succes=["fictif"])
    monkeypatch.setattr(session, "envoyer_avec_progression", faux_pont)
    resultat = session.envoyer_lot_heritage(backend, ["fictif"],
                                          dlg_progress=progress)
    assert resultat == ["fictif"]
    assert backend.dernier_bilan.succes == ["fictif"]
    assert backend.appels == ["fictif"]
    assert backend.connexions == 0
    assert backend.fermetures == 0
    assert progress.detruit


def test_adaptateur_legacy_refuse_un_appel_hors_fil_graphique(monkeypatch):
    wx = types.ModuleType("wx")
    wx.IsMainThread = lambda: False
    monkeypatch.setitem(sys.modules, "wx", wx)
    with pytest.raises(RuntimeError, match="fil graphique"):
        session.envoyer_lot_heritage(Transport([1]), ["fictif"])


def test_inventory_du_transport_ne_reintroduit_pas_des_anciens_appels():
    """Surveille l'ensemble des fichiers applicatifs, y compris les futurs."""
    racine = ROOT / "teamworks"
    appels_lot = set()
    constructeurs = set()
    for chemin in racine.rglob("*.py"):
        texte = chemin.read_text(encoding="utf-8")
        relatif = chemin.relative_to(racine).as_posix()
        if re.search(r"\.Envoyer_lot\s*\(", texte):
            appels_lot.add(relatif)
        if re.search(r"\.Messagerie\s*\(", texte):
            constructeurs.add(relatif)
    assert appels_lot == set(), "Appelants directs a qualifier : %r" % sorted(appels_lot)
    assert constructeurs == {
        "Dlg/DLG_Mailer.py", "Utils/UTILS_Sauvegarde.py",
        "Utils/UTILS_Envoi_rapport_bug.py",
    }, "Nouveaux points d'entree de messagerie a auditer : %r" % sorted(constructeurs)


def test_dialogue_erreur_avec_parent_ne_force_pas_le_topmost():
    source = (ROOT / "teamworks/Dlg/DLG_Messagebox.py").read_text(encoding="utf-8")
    assert "style_parent = wx.DEFAULT_DIALOG_STYLE" in source
    assert "if parent is None:" in source
    assert "wx.Dialog.__init__(self, parent, -1, style=style_parent)" in source


def test_fausse_boucle_wx_reste_active_pendant_un_transport_lent(monkeypatch):
    """Simulation de boucle wx, sans pretendre tester les vrais HWND Windows."""
    evenements = queue.Queue()
    gui_thread = threading.get_ident()
    moments = []
    fenetres = []
    valeurs = []
    wx = types.ModuleType("wx")
    for nom, val in {"DEFAULT_DIALOG_STYLE": 0, "VERTICAL": 1, "ALL": 2,
                     "EXPAND": 4, "LEFT": 8, "RIGHT": 16, "BOTTOM": 32,
                     "ID_NONE": -3, "ID_OK": 1, "EVT_CLOSE": object()}.items():
        setattr(wx, nom, val)
    wx.CallAfter = lambda callback: evenements.put(callback)
    class Dialogue:
        def __init__(self, parent, title, style):
            self.parent = parent
            self.modal = False
            self.escape_id = None
            fenetres.append(self)
        def SetSizerAndFit(self, obj): pass
        def SetMinSize(self, value): pass
        def SetSize(self, value): pass
        def CenterOnParent(self): pass
        def Bind(self, evt, callback): self.close_callback = callback
        def SetEscapeId(self, value): self.escape_id = value
        def IsModal(self): return self.modal
        def EndModal(self, code): self.modal = False
        def Destroy(self): self.destroyed = True
        def ShowModal(self):
            self.modal = True
            limite = time.monotonic() + 4
            while self.modal and time.monotonic() < limite:
                try:
                    evenements.get(timeout=0.2)()
                except queue.Empty:
                    pass
            assert not self.modal, "Le worker a bloque la boucle modale fictive"
            return wx.ID_OK
    class BoxSizer:
        def __init__(self, orientation): pass
        def Add(self, *a): pass
    class StaticText:
        def __init__(self, parent, label):
            self.parent = parent
        def SetLabel(self, value):
            valeurs.append((value, threading.get_ident()))
    class Gauge:
        def __init__(self, parent, range): pass
        def SetValue(self, value): pass
    wx.Dialog, wx.BoxSizer, wx.StaticText, wx.Gauge = Dialogue, BoxSizer, StaticText, Gauge
    monkeypatch.setitem(sys.modules, "wx", wx)
    dlg_pkg = types.ModuleType("Dlg")
    dlg_pkg.DLG_Messagebox = types.SimpleNamespace(Dialog=object)
    monkeypatch.setitem(sys.modules, "Dlg", dlg_pkg)
    trad = types.ModuleType("Utils.UTILS_Traduction")
    trad._ = lambda s: s
    monkeypatch.setitem(sys.modules, "Utils.UTILS_Traduction", trad)
    class Lent:
        def Connecter(self):
            moments.append(("debut", threading.get_ident(), time.monotonic()))
            time.sleep(0.07)
        def Envoyer(self, message):
            moments.append(("envoi", threading.get_ident(), time.monotonic()))
            time.sleep(0.07)
            return 1
        def Fermer(self):
            moments.append(("ferme", threading.get_ident(), time.monotonic()))
    parent = types.SimpleNamespace(IsShownOnScreen=lambda: True)
    def battement():
        moments.append(("gui", threading.get_ident(), time.monotonic()))
    timer = threading.Thread(target=lambda: (time.sleep(0.03), wx.CallAfter(battement)))
    timer.start()
    resultat = session.envoyer_avec_progression(
        parent=parent, fabrique=Lent, messages=["fictif"],
        afficher_confirmation_envoi=False,
    )
    timer.join(timeout=1)
    assert resultat.succes == ["fictif"]
    assert fenetres[0].parent is parent and fenetres[0].destroyed
    assert fenetres[0].escape_id == wx.ID_NONE
    assert any(v.startswith("Envoi ") for v, _ in valeurs)
    assert all(thread == gui_thread for _, thread in valeurs)
    assert all(thread != gui_thread for name, thread, _ in moments if name != "gui")
    assert any(name == "gui" for name, _, _ in moments)
    assert next(t for name, _, t in moments if name == "gui") < next(
        t for name, _, t in moments if name == "ferme"
    )
