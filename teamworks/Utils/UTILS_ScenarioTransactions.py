#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Transactions atomiques pour les opérations multi-étapes des scénarios.

Ce module ne dépend pas de wx. Une opération métier ouvre une seule transaction
sur l'objet ``GestionDB.DB`` fourni par l'appelant et ne committe qu'après la
dernière écriture. Toute exception déclenche un rollback complet.
"""


class ScenarioReferenceError(Exception):
    """Le scénario est encore référencé par un report automatique."""


class ScenarioTransactionError(Exception):
    """La transaction scénario n'a pas pu être menée à son terme."""


CHAMPS_SCENARIO_AUTORISES = {
    "IDpersonne",
    "nom",
    "description",
    "mode_heure",
    "detail_mois",
    "date_debut",
    "date_fin",
    "toutes_categories",
}


def _execute(db, sql, params=()):
    if db.isNetwork:
        sql = sql.replace("?", "%s")
    db.cursor.execute(sql, tuple(params))
    return db.cursor


def _rollback(db):
    if getattr(db, "connexion", None):
        db.connexion.rollback()


def compter_reports_vers_scenario(db, IDscenario):
    """Compte les reports automatiques ``A<IDscenario>;...`` vers un scénario."""
    prefixe = "A%d;%%" % int(IDscenario)
    curseur = _execute(
        db,
        "SELECT COUNT(*) FROM scenarios_cat WHERE report LIKE ?",
        (prefixe,),
    )
    resultat = curseur.fetchone()
    return int(resultat[0]) if resultat else 0


def supprimer_scenario_atomique(db, IDscenario):
    """Supprime catégories puis scénario dans une transaction unique.

    La suppression est refusée tant qu'un autre ``scenarios_cat`` contient un
    report automatique vers le scénario visé. Cette règle évite de créer des
    reports orphelins.
    """
    try:
        nbre_reports = compter_reports_vers_scenario(db, IDscenario)
        if nbre_reports:
            raise ScenarioReferenceError(
                "%d report(s) utilisent encore ce scénario" % nbre_reports
            )

        _execute(db, "DELETE FROM scenarios_cat WHERE IDscenario=?", (IDscenario,))
        _execute(db, "DELETE FROM scenarios WHERE IDscenario=?", (IDscenario,))
        db.Commit()
    except Exception:
        _rollback(db)
        raise


def dupliquer_scenario_atomique(db, IDscenario, prefixe_nom=u"Copie de "):
    """Duplique un scénario et toutes ses catégories avec un seul commit."""
    try:
        curseur = _execute(
            db,
            "SELECT IDpersonne, nom, description, mode_heure, detail_mois, "
            "date_debut, date_fin, toutes_categories "
            "FROM scenarios WHERE IDscenario=?",
            (IDscenario,),
        )
        source = curseur.fetchone()
        if source is None:
            raise ScenarioTransactionError("Scénario source introuvable")

        IDpersonne, nom, description, mode_heure, detail_mois, date_debut, date_fin, toutes_categories = source
        curseur = _execute(
            db,
            "INSERT INTO scenarios "
            "(IDpersonne, nom, description, mode_heure, detail_mois, date_debut, date_fin, toutes_categories) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                IDpersonne,
                prefixe_nom + nom,
                description,
                mode_heure,
                detail_mois,
                date_debut,
                date_fin,
                toutes_categories,
            ),
        )
        newIDscenario = curseur.lastrowid
        if not newIDscenario:
            raise ScenarioTransactionError("Identifiant du scénario dupliqué indisponible")

        curseur = _execute(
            db,
            "SELECT IDcategorie, prevision, report, date_debut_realise, date_fin_realise "
            "FROM scenarios_cat WHERE IDscenario=?",
            (IDscenario,),
        )
        categories = curseur.fetchall()

        for IDcategorie, prevision, report, date_debut_realise, date_fin_realise in categories:
            _execute(
                db,
                "INSERT INTO scenarios_cat "
                "(IDscenario, IDcategorie, prevision, report, date_debut_realise, date_fin_realise) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    newIDscenario,
                    IDcategorie,
                    prevision,
                    report,
                    date_debut_realise,
                    date_fin_realise,
                ),
            )

        db.Commit()
        return newIDscenario
    except Exception:
        _rollback(db)
        raise


def sauvegarder_scenario_atomique(db, IDscenario, donnees_scenario, dict_virtual_db):
    """Crée/met à jour un scénario et synchronise ses catégories atomiquement.

    ``donnees_scenario`` est une séquence ``[(champ, valeur), ...]``.
    ``dict_virtual_db`` suit le contrat historique de ``DLG_Scenario.Tableau``.
    """
    try:
        champs = [champ for champ, valeur in donnees_scenario]
        valeurs = [valeur for champ, valeur in donnees_scenario]

        if len(champs) != len(set(champs)):
            raise ScenarioTransactionError("Champ scénario présent plusieurs fois")
        if set(champs) != CHAMPS_SCENARIO_AUTORISES:
            raise ScenarioTransactionError("Jeu de champs scénario inattendu")

        if IDscenario is None:
            colonnes = ", ".join(champs)
            marqueurs = ", ".join(["?"] * len(champs))
            curseur = _execute(
                db,
                "INSERT INTO scenarios (%s) VALUES (%s)" % (colonnes, marqueurs),
                valeurs,
            )
            IDscenario = curseur.lastrowid
            if not IDscenario:
                raise ScenarioTransactionError("Identifiant du scénario créé indisponible")
        else:
            affectations = ", ".join(["%s=?" % champ for champ in champs])
            _execute(
                db,
                "UPDATE scenarios SET %s WHERE IDscenario=?" % affectations,
                valeurs + [IDscenario],
            )

        curseur = _execute(
            db,
            "SELECT IDscenario_cat FROM scenarios_cat WHERE IDscenario=?",
            (IDscenario,),
        )
        ids_existants = set([row[0] for row in curseur.fetchall()])
        ids_traites = set()

        for IDcategorie, valeurs_cat in dict_virtual_db.items():
            donnees_cat = (
                IDscenario,
                IDcategorie,
                valeurs_cat["prevision"],
                valeurs_cat["report"],
                valeurs_cat["date_debut_realise"],
                valeurs_cat["date_fin_realise"],
            )
            IDscenario_cat = valeurs_cat["IDscenario_cat"]
            if IDscenario_cat is None:
                curseur = _execute(
                    db,
                    "INSERT INTO scenarios_cat "
                    "(IDscenario, IDcategorie, prevision, report, date_debut_realise, date_fin_realise) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    donnees_cat,
                )
                IDscenario_cat = curseur.lastrowid
                if not IDscenario_cat:
                    raise ScenarioTransactionError("Identifiant de catégorie scénario indisponible")
            else:
                if IDscenario_cat not in ids_existants:
                    raise ScenarioTransactionError(
                        "La catégorie scénario %s n'appartient pas au scénario %s"
                        % (IDscenario_cat, IDscenario)
                    )
                if IDscenario_cat in ids_traites:
                    raise ScenarioTransactionError(
                        "La catégorie scénario %s est utilisée plusieurs fois" % IDscenario_cat
                    )
                _execute(
                    db,
                    "UPDATE scenarios_cat SET IDscenario=?, IDcategorie=?, prevision=?, report=?, "
                    "date_debut_realise=?, date_fin_realise=? WHERE IDscenario_cat=?",
                    donnees_cat + (IDscenario_cat,),
                )
            ids_traites.add(IDscenario_cat)

        for IDscenario_cat in ids_existants - ids_traites:
            _execute(
                db,
                "DELETE FROM scenarios_cat WHERE IDscenario_cat=?",
                (IDscenario_cat,),
            )

        db.Commit()
        return IDscenario
    except Exception:
        _rollback(db)
        raise
