#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Réutilisation bornée des connexions réseau pour une action métier.

Le mécanisme est volontairement opt-in et limité au thread qui ouvre le
contexte. SQLite n'est jamais intercepté : seuls les appels à
``GestionDB.GetConnexionReseau`` peuvent être réutilisés.

Chaque ``GestionDB.DB`` conserve sa frontière logique : son ``Close()`` rend la
connexion au petit pool de l'action après un rollback de sécurité. Si deux DB
sont ouvertes en même temps, elles reçoivent deux connexions physiques
indépendantes ; seules les ouvertures séquentielles réutilisent une connexion.
Toutes les connexions physiques restantes sont fermées à la sortie du contexte,
y compris en cas d'exception.
"""

from contextlib import contextmanager
import threading


_ETAT = threading.local()
_INSTALL_LOCK = threading.RLock()


class _BailConnexion(object):
    """Proxy de connexion rendu au scope au lieu d'être fermé physiquement."""

    def __init__(self, scope, cle, connexion):
        self._scope = scope
        self._cle = cle
        self._connexion = connexion
        self._rendue = False

    def __getattr__(self, nom):
        return getattr(self._connexion, nom)

    def close(self):
        if self._rendue:
            return
        self._rendue = True
        self._scope.rendre(self._cle, self._connexion)


class _ScopeConnexions(object):
    def __init__(self, module, ouverture_originale):
        self.module = module
        self.ouverture_originale = ouverture_originale
        self.inactives = {}
        # Certaines implémentations DB ne garantissent pas que l'objet connexion
        # soit hashable : indexer par id() évite de dépendre de ce détail.
        self.connexions = {}
        self.actif = True
        self.profondeur = 1
        self.stats = {
            "ouvertures_physiques": 0,
            "reutilisations": 0,
            "fermetures_physiques": 0,
        }

    def acquerir(self, nomFichier):
        cle = str(nomFichier)
        entree = self.inactives.pop(cle, None)
        if entree is None:
            connexion, nom_base = self.ouverture_originale(nomFichier)
            self.connexions[id(connexion)] = connexion
            self.stats["ouvertures_physiques"] += 1
        else:
            connexion, nom_base = entree
            self.stats["reutilisations"] += 1
        return _BailConnexion(self, cle, connexion), nom_base

    def _est_connue(self, connexion):
        return self.connexions.get(id(connexion)) is connexion

    def _fermer_physiquement(self, connexion):
        if not self._est_connue(connexion):
            return
        self.connexions.pop(id(connexion), None)
        try:
            connexion.close()
        finally:
            self.stats["fermetures_physiques"] += 1

    def rendre(self, cle, connexion):
        if not self._est_connue(connexion):
            return
        try:
            connexion.rollback()
        except Exception:
            self._fermer_physiquement(connexion)
            return

        if not self.actif:
            self._fermer_physiquement(connexion)
            return

        # Un seul slot inactif par base suffit pour les lectures séquentielles.
        # Une deuxième connexion simultanée reste indépendante puis est fermée.
        if cle in self.inactives:
            self._fermer_physiquement(connexion)
        else:
            self.inactives[cle] = (connexion, self._nom_base(cle))

    def _nom_base(self, cle):
        # Le nom de base est recalculé sans ouvrir de connexion.
        try:
            pos = cle.index("[RESEAU]")
            return cle[pos:].replace("[RESEAU]", "").lower()
        except Exception:
            return ""

    def fermer(self):
        self.actif = False
        self.inactives.clear()
        for connexion in list(self.connexions.values()):
            self._fermer_physiquement(connexion)


def _scopes():
    if not hasattr(_ETAT, "scopes"):
        _ETAT.scopes = {}
    return _ETAT.scopes


def _installer(module):
    """Installe une fois un routeur thread-local autour de GetConnexionReseau."""
    with _INSTALL_LOCK:
        original = getattr(module, "_teamworks_get_connexion_reseau_original", None)
        if original is not None:
            return original

        original = module.GetConnexionReseau

        def ouverture_routee(nomFichier=""):
            scope = _scopes().get(id(module))
            if scope is None:
                return original(nomFichier)
            return scope.acquerir(nomFichier)

        module._teamworks_get_connexion_reseau_original = original
        module.GetConnexionReseau = ouverture_routee
        return original


@contextmanager
def connexions_reseau_partagees(module):
    """Réutilise les connexions MySQL pendant une séquence logique bornée.

    Le contexte est sans effet sur SQLite, car le chemin local n'appelle jamais
    ``GetConnexionReseau``. Les scopes imbriqués sur le même thread partagent le
    même pool et la fermeture physique n'a lieu qu'à la sortie du scope externe.
    """
    original = _installer(module)
    scopes = _scopes()
    cle_module = id(module)
    scope = scopes.get(cle_module)
    if scope is not None:
        scope.profondeur += 1
        try:
            yield scope.stats
        finally:
            scope.profondeur -= 1
        return

    scope = _ScopeConnexions(module, original)
    scopes[cle_module] = scope
    try:
        yield scope.stats
    finally:
        try:
            scope.fermer()
        finally:
            scopes.pop(cle_module, None)
