#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Migration sûre des rattachements remboursements / déplacements.

Décision d'architecture : ``deplacements.IDremboursement`` est la source
canonique. ``remboursements.listeIDdeplacement`` est une projection de
compatibilité régénérable.

Le module est volontairement indépendant de wxPython et de GestionDB. Les
écritures SQLite sont regroupées dans une transaction explicite et toute
application crée d'abord un snapshot externe vérifiable permettant le rollback.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from teamworks.CcnsCore.diagnostic_remboursements_deplacements import lire_projection

_FORMAT_SNAPSHOT = "teamworks-remboursements-deplacements-snapshot"
_VERSION_SNAPSHOT = 1
_LONGUEUR_PROJECTION_HISTORIQUE = 300
_ENTIER_TEXTE = re.compile(r"^[+-]?\d+$")


class MigrationBloquee(RuntimeError):
    """Le plan contient au moins un conflit de la source canonique."""


class SnapshotInvalide(RuntimeError):
    """Le snapshot est illisible, altéré ou incompatible."""


class RollbackRefuse(RuntimeError):
    """Le rollback serait dangereux au vu de l'état courant."""


@dataclass(frozen=True)
class DeplacementBrut:
    IDdeplacement: int
    IDpersonne: object
    IDremboursement: object


@dataclass(frozen=True)
class RemboursementBrut:
    IDremboursement: int
    IDpersonne: object
    listeIDdeplacement: object


@dataclass(frozen=True)
class EtatRattachements:
    deplacements: tuple[DeplacementBrut, ...]
    remboursements: tuple[RemboursementBrut, ...]


@dataclass(frozen=True)
class BlocageMigration:
    type_blocage: str
    entite: str
    details: str


@dataclass(frozen=True)
class ActionMigration:
    table: str
    identifiant: int
    colonne: str
    avant: object
    apres: object
    motif: str


@dataclass(frozen=True)
class PlanMigration:
    recuperer_parent_unique: bool
    etat_avant_sha256: str
    actions_enfants: tuple[ActionMigration, ...]
    actions_projections: tuple[ActionMigration, ...]
    blocages: tuple[BlocageMigration, ...]
    avertissements: tuple[str, ...]
    deplacements_null: tuple[int, ...]
    deplacements_zero: tuple[int, ...]

    @property
    def applicable(self) -> bool:
        return not self.blocages

    @property
    def actions(self) -> tuple[ActionMigration, ...]:
        return self.actions_enfants + self.actions_projections

    def render_text(self) -> str:
        lignes = [
            "Migration remboursements ↔ déplacements",
            "Source canonique : deplacements.IDremboursement",
            "Projection dérivée : remboursements.listeIDdeplacement",
            "Mode récupération parent unique : %s"
            % ("activé" if self.recuperer_parent_unique else "désactivé"),
            "État source SHA-256 : %s" % self.etat_avant_sha256,
            "IDremboursement NULL : %s"
            % (", ".join(map(str, self.deplacements_null)) or "aucun"),
            "IDremboursement 0 : %s"
            % (", ".join(map(str, self.deplacements_zero)) or "aucun"),
            "",
        ]
        if self.blocages:
            lignes.append("BLOQUÉ — aucun changement ne doit être appliqué :")
            for blocage in self.blocages:
                lignes.append(
                    "- %s [%s] : %s"
                    % (blocage.entite, blocage.type_blocage, blocage.details)
                )
        else:
            lignes.append("Plan applicable atomiquement.")

        lignes.extend(("", "Avant → état canonique proposé :"))
        if not self.actions:
            lignes.append("- aucun changement")
        for action in self.actions:
            lignes.append(
                "- %s %d.%s : %r → %r (%s)"
                % (
                    action.table,
                    action.identifiant,
                    action.colonne,
                    action.avant,
                    action.apres,
                    action.motif,
                )
            )

        if self.avertissements:
            lignes.extend(("", "Avertissements :"))
            lignes.extend("- %s" % texte for texte in self.avertissements)
        return "\n".join(lignes)


@dataclass(frozen=True)
class ResultatMigration:
    plan: PlanMigration
    snapshot: Path
    etat_apres_sha256: str


@dataclass(frozen=True)
class ResultatRollback:
    snapshot: Path
    etat_restaure_sha256: str


def _normaliser_id_remboursement_brut(valeur: object) -> tuple[str, Optional[int]]:
    """Retourne (état, identifiant) sans coercition silencieuse dangereuse.

    États : ``libre``, ``valide`` ou ``invalide``.
    Les entiers SQLite et les chaînes composées uniquement d'un entier sont
    acceptés. Une chaîne vide, un réel, un blob ou un identifiant négatif sont
    considérés comme invalides et bloquent la migration.
    """
    if valeur is None:
        return "libre", None

    if isinstance(valeur, bool):
        return "invalide", None

    if isinstance(valeur, int):
        identifiant = valeur
    elif isinstance(valeur, str) and _ENTIER_TEXTE.match(valeur.strip()):
        identifiant = int(valeur.strip())
    else:
        return "invalide", None

    if identifiant == 0:
        return "libre", None
    if identifiant < 0:
        return "invalide", None
    return "valide", identifiant


def _personnes_compatibles(enfant: object, parent: object) -> bool:
    return enfant is not None and parent is not None and enfant == parent


def _lire_etat(connexion: sqlite3.Connection) -> EtatRattachements:
    curseur = connexion.cursor()
    try:
        curseur.execute(
            "SELECT IDdeplacement, IDpersonne, IDremboursement "
            "FROM deplacements ORDER BY IDdeplacement"
        )
        deplacements = tuple(DeplacementBrut(*ligne) for ligne in curseur.fetchall())
        curseur.execute(
            "SELECT IDremboursement, IDpersonne, listeIDdeplacement "
            "FROM remboursements ORDER BY IDremboursement"
        )
        remboursements = tuple(
            RemboursementBrut(*ligne) for ligne in curseur.fetchall()
        )
    finally:
        curseur.close()
    return EtatRattachements(deplacements, remboursements)


def _encoder_valeur_sqlite(valeur: object) -> dict[str, object]:
    if valeur is None:
        return {"type": "null"}
    if isinstance(valeur, bool):
        return {"type": "integer", "value": int(valeur)}
    if isinstance(valeur, int):
        return {"type": "integer", "value": valeur}
    if isinstance(valeur, float):
        if not math.isfinite(valeur):
            raise ValueError("valeur SQLite réelle non finie")
        return {"type": "real", "value": valeur}
    if isinstance(valeur, str):
        return {"type": "text", "value": valeur}
    if isinstance(valeur, (bytes, bytearray, memoryview)):
        brut = bytes(valeur)
        return {
            "type": "blob",
            "value": base64.b64encode(brut).decode("ascii"),
        }
    raise TypeError("type SQLite non pris en charge : %s" % type(valeur).__name__)


def _decoder_valeur_sqlite(valeur: object) -> object:
    if not isinstance(valeur, dict) or "type" not in valeur:
        raise SnapshotInvalide("valeur typée manquante dans le snapshot")
    type_valeur = valeur["type"]
    if type_valeur == "null":
        return None
    if type_valeur == "integer":
        contenu = valeur.get("value")
        if isinstance(contenu, bool) or not isinstance(contenu, int):
            raise SnapshotInvalide("entier invalide dans le snapshot")
        return contenu
    if type_valeur == "real":
        contenu = valeur.get("value")
        if isinstance(contenu, bool) or not isinstance(contenu, (int, float)):
            raise SnapshotInvalide("réel invalide dans le snapshot")
        contenu = float(contenu)
        if not math.isfinite(contenu):
            raise SnapshotInvalide("réel non fini dans le snapshot")
        return contenu
    if type_valeur == "text":
        contenu = valeur.get("value")
        if not isinstance(contenu, str):
            raise SnapshotInvalide("texte invalide dans le snapshot")
        return contenu
    if type_valeur == "blob":
        contenu = valeur.get("value")
        if not isinstance(contenu, str):
            raise SnapshotInvalide("blob invalide dans le snapshot")
        try:
            return base64.b64decode(contenu.encode("ascii"), validate=True)
        except Exception as exc:
            raise SnapshotInvalide("blob base64 invalide") from exc
    raise SnapshotInvalide("type de valeur inconnu : %r" % type_valeur)


def _etat_vers_objet(etat: EtatRattachements) -> dict[str, object]:
    return {
        "deplacements": [
            {
                "IDdeplacement": ligne.IDdeplacement,
                "IDpersonne": _encoder_valeur_sqlite(ligne.IDpersonne),
                "IDremboursement": _encoder_valeur_sqlite(ligne.IDremboursement),
            }
            for ligne in etat.deplacements
        ],
        "remboursements": [
            {
                "IDremboursement": ligne.IDremboursement,
                "IDpersonne": _encoder_valeur_sqlite(ligne.IDpersonne),
                "listeIDdeplacement": _encoder_valeur_sqlite(
                    ligne.listeIDdeplacement
                ),
            }
            for ligne in etat.remboursements
        ],
    }


def _json_canonique(objet: object) -> bytes:
    return json.dumps(
        objet,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def empreinte_etat(etat: EtatRattachements) -> str:
    return hashlib.sha256(_json_canonique(_etat_vers_objet(etat))).hexdigest()


def _ajouter_avertissement_unique(cible: list[str], texte: str) -> None:
    if texte not in cible:
        cible.append(texte)


def planifier_etat(
    etat: EtatRattachements,
    *,
    recuperer_parent_unique: bool = False,
) -> PlanMigration:
    deplacements = tuple(sorted(etat.deplacements, key=lambda x: x.IDdeplacement))
    remboursements = tuple(
        sorted(etat.remboursements, key=lambda x: x.IDremboursement)
    )
    deplacements_par_id = {x.IDdeplacement: x for x in deplacements}
    remboursements_par_id = {x.IDremboursement: x for x in remboursements}

    projections = {
        x.IDremboursement: lire_projection(x.listeIDdeplacement)
        for x in remboursements
    }
    revendications: dict[int, set[int]] = {}
    for remboursement in remboursements:
        projection = projections[remboursement.IDremboursement]
        for IDdeplacement in projection.ids:
            revendications.setdefault(IDdeplacement, set()).add(
                remboursement.IDremboursement
            )

    blocages: list[BlocageMigration] = []
    avertissements: list[str] = []
    nulls: list[int] = []
    zeros: list[int] = []
    cible_enfant: dict[int, Optional[int]] = {}
    actions_enfants: list[ActionMigration] = []

    for deplacement in deplacements:
        brut = deplacement.IDremboursement
        if brut is None:
            nulls.append(deplacement.IDdeplacement)
        elif isinstance(brut, int) and not isinstance(brut, bool) and brut == 0:
            zeros.append(deplacement.IDdeplacement)
        elif isinstance(brut, str) and _ENTIER_TEXTE.match(brut.strip()):
            if int(brut.strip()) == 0:
                zeros.append(deplacement.IDdeplacement)

        etat_id, IDremboursement = _normaliser_id_remboursement_brut(brut)
        if etat_id == "invalide":
            cible_enfant[deplacement.IDdeplacement] = None
            blocages.append(
                BlocageMigration(
                    "id_remboursement_enfant_invalide",
                    "déplacement %d" % deplacement.IDdeplacement,
                    "IDremboursement brut %r ne peut pas être interprété sans ambiguïté"
                    % brut,
                )
            )
            continue

        if etat_id == "valide":
            cible_enfant[deplacement.IDdeplacement] = IDremboursement
            parent = remboursements_par_id.get(IDremboursement)
            if parent is None:
                blocages.append(
                    BlocageMigration(
                        "reference_enfant_orpheline",
                        "déplacement %d" % deplacement.IDdeplacement,
                        "IDremboursement=%d pointe vers un remboursement inexistant"
                        % IDremboursement,
                    )
                )
                continue
            if not _personnes_compatibles(
                deplacement.IDpersonne, parent.IDpersonne
            ):
                blocages.append(
                    BlocageMigration(
                        "personne_canonique_incoherente",
                        "déplacement %d" % deplacement.IDdeplacement,
                        "IDpersonne enfant=%r, parent=%r pour le remboursement %d"
                        % (
                            deplacement.IDpersonne,
                            parent.IDpersonne,
                            IDremboursement,
                        ),
                    )
                )
            continue

        # Enfant libre : la clé canonique gagne par défaut. La récupération d'une
        # revendication parent unique est une option explicite, jamais implicite.
        cible_enfant[deplacement.IDdeplacement] = None
        parents = tuple(sorted(revendications.get(deplacement.IDdeplacement, ())))
        if not parents:
            continue

        parents_compatibles = tuple(
            IDparent
            for IDparent in parents
            if _personnes_compatibles(
                deplacement.IDpersonne, remboursements_par_id[IDparent].IDpersonne
            )
        )
        if recuperer_parent_unique and len(parents) == 1 and len(parents_compatibles) == 1:
            IDparent = parents_compatibles[0]
            cible_enfant[deplacement.IDdeplacement] = IDparent
            actions_enfants.append(
                ActionMigration(
                    "deplacements",
                    deplacement.IDdeplacement,
                    "IDremboursement",
                    brut,
                    IDparent,
                    "récupération non ambiguë depuis l'unique projection parent de la même personne",
                )
            )
        else:
            if len(parents) == 1 and len(parents_compatibles) == 1:
                _ajouter_avertissement_unique(
                    avertissements,
                    "déplacement %d : revendication parent unique ignorée en mode strict ; la clé enfant libre reste canonique"
                    % deplacement.IDdeplacement,
                )
            elif len(parents) > 1:
                _ajouter_avertissement_unique(
                    avertissements,
                    "déplacement %d : revendications parent multiples %s supprimées de la projection ; la clé enfant libre reste canonique"
                    % (deplacement.IDdeplacement, list(parents)),
                )
            else:
                _ajouter_avertissement_unique(
                    avertissements,
                    "déplacement %d : revendication parent incompatible avec IDpersonne ; la clé enfant libre reste canonique"
                    % deplacement.IDdeplacement,
                )

    for remboursement in remboursements:
        projection = projections[remboursement.IDremboursement]
        if projection.tokens_invalides:
            _ajouter_avertissement_unique(
                avertissements,
                "remboursement %d : token(s) de projection invalide(s) %s ; la projection sera régénérée"
                % (
                    remboursement.IDremboursement,
                    list(projection.tokens_invalides),
                ),
            )
        if projection.ids_dupliques:
            _ajouter_avertissement_unique(
                avertissements,
                "remboursement %d : ID(s) dupliqué(s) %s ; la projection sera dédupliquée"
                % (
                    remboursement.IDremboursement,
                    sorted(set(projection.ids_dupliques)),
                ),
            )
        absents = sorted(
            {x for x in projection.ids if x not in deplacements_par_id}
        )
        if absents:
            _ajouter_avertissement_unique(
                avertissements,
                "remboursement %d : déplacement(s) absent(s) %s retiré(s) de la projection"
                % (remboursement.IDremboursement, absents),
            )

    actions_projections: list[ActionMigration] = []
    for remboursement in remboursements:
        projection = projections[remboursement.IDremboursement]
        ids_cibles = tuple(
            sorted(
                IDdeplacement
                for IDdeplacement, IDparent in cible_enfant.items()
                if IDparent == remboursement.IDremboursement
            )
        )
        texte_cible = "-".join(map(str, ids_cibles))
        doit_regenerer = bool(
            projection.tokens_invalides
            or projection.ids_dupliques
            or projection.ids != ids_cibles
        )
        if len(texte_cible) > _LONGUEUR_PROJECTION_HISTORIQUE:
            message_longueur = (
                "remboursement %d : projection canonique de %d caractères > VARCHAR(%d) historique"
                % (
                    remboursement.IDremboursement,
                    len(texte_cible),
                    _LONGUEUR_PROJECTION_HISTORIQUE,
                )
            )
            if doit_regenerer:
                blocages.append(
                    BlocageMigration(
                        "projection_depasse_longueur_historique",
                        "remboursement %d" % remboursement.IDremboursement,
                        message_longueur,
                    )
                )
            else:
                _ajouter_avertissement_unique(avertissements, message_longueur)

        if doit_regenerer:
            actions_projections.append(
                ActionMigration(
                    "remboursements",
                    remboursement.IDremboursement,
                    "listeIDdeplacement",
                    remboursement.listeIDdeplacement,
                    texte_cible,
                    "régénération déterministe depuis les clés enfants canoniques",
                )
            )

    blocages.sort(key=lambda x: (x.type_blocage, x.entite, x.details))
    actions_enfants.sort(key=lambda x: x.identifiant)
    actions_projections.sort(key=lambda x: x.identifiant)
    avertissements.sort()
    return PlanMigration(
        recuperer_parent_unique=recuperer_parent_unique,
        etat_avant_sha256=empreinte_etat(etat),
        actions_enfants=tuple(actions_enfants),
        actions_projections=tuple(actions_projections),
        blocages=tuple(blocages),
        avertissements=tuple(avertissements),
        deplacements_null=tuple(sorted(nulls)),
        deplacements_zero=tuple(sorted(zeros)),
    )


def _appliquer_actions_en_memoire(
    etat: EtatRattachements, plan: PlanMigration
) -> EtatRattachements:
    enfants = {x.identifiant: x for x in plan.actions_enfants}
    projections = {x.identifiant: x for x in plan.actions_projections}
    deplacements = tuple(
        DeplacementBrut(
            ligne.IDdeplacement,
            ligne.IDpersonne,
            enfants.get(ligne.IDdeplacement, None).apres
            if ligne.IDdeplacement in enfants
            else ligne.IDremboursement,
        )
        for ligne in etat.deplacements
    )
    remboursements = tuple(
        RemboursementBrut(
            ligne.IDremboursement,
            ligne.IDpersonne,
            projections.get(ligne.IDremboursement, None).apres
            if ligne.IDremboursement in projections
            else ligne.listeIDdeplacement,
        )
        for ligne in etat.remboursements
    )
    return EtatRattachements(deplacements, remboursements)


def _uri_sqlite(chemin: Path, mode: str) -> str:
    return chemin.resolve().as_uri() + "?mode=" + mode


def planifier_base_sqlite(
    chemin,
    *,
    recuperer_parent_unique: bool = False,
) -> PlanMigration:
    chemin = Path(chemin)
    connexion = sqlite3.connect(
        _uri_sqlite(chemin, "ro"), uri=True, isolation_level=None
    )
    try:
        connexion.execute("BEGIN")
        etat = _lire_etat(connexion)
        return planifier_etat(
            etat, recuperer_parent_unique=recuperer_parent_unique
        )
    finally:
        if connexion.in_transaction:
            connexion.rollback()
        connexion.close()


def _chemin_snapshot_defaut(chemin_base: Path) -> Path:
    horodatage = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return chemin_base.with_name(
        "%s.remboursements-%s.snapshot.json" % (chemin_base.name, horodatage)
    )


def _ecrire_snapshot(
    chemin_snapshot: Path,
    *,
    chemin_base: Path,
    etat_avant: EtatRattachements,
    plan: PlanMigration,
    etat_apres_prevu: EtatRattachements,
) -> None:
    document = {
        "format": _FORMAT_SNAPSHOT,
        "version": _VERSION_SNAPSHOT,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": str(chemin_base.resolve()),
        "before_state_sha256": empreinte_etat(etat_avant),
        "planned_after_state_sha256": empreinte_etat(etat_apres_prevu),
        "recuperer_parent_unique": plan.recuperer_parent_unique,
        "state": _etat_vers_objet(etat_avant),
        "actions": [
            {
                "table": action.table,
                "identifiant": action.identifiant,
                "colonne": action.colonne,
                "avant": _encoder_valeur_sqlite(action.avant),
                "apres": _encoder_valeur_sqlite(action.apres),
                "motif": action.motif,
            }
            for action in plan.actions
        ],
    }
    checksum = hashlib.sha256(_json_canonique(document)).hexdigest()
    document["snapshot_sha256"] = checksum
    donnees = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ).encode("utf-8") + b"\n"

    chemin_snapshot.parent.mkdir(parents=True, exist_ok=True)
    with chemin_snapshot.open("xb") as fichier:
        fichier.write(donnees)
        fichier.flush()
        os.fsync(fichier.fileno())


def _charger_snapshot(chemin_snapshot: Path) -> tuple[dict[str, object], EtatRattachements]:
    try:
        document = json.loads(chemin_snapshot.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SnapshotInvalide("snapshot JSON illisible") from exc
    if not isinstance(document, dict):
        raise SnapshotInvalide("racine JSON invalide")
    if document.get("format") != _FORMAT_SNAPSHOT:
        raise SnapshotInvalide("format de snapshot inattendu")
    if document.get("version") != _VERSION_SNAPSHOT:
        raise SnapshotInvalide("version de snapshot non supportée")

    checksum_attendu = document.get("snapshot_sha256")
    if not isinstance(checksum_attendu, str):
        raise SnapshotInvalide("checksum de snapshot absent")
    corps = dict(document)
    corps.pop("snapshot_sha256", None)
    checksum_calcule = hashlib.sha256(_json_canonique(corps)).hexdigest()
    if not hmac.compare_digest(checksum_attendu, checksum_calcule):
        raise SnapshotInvalide("checksum de snapshot invalide")

    state = document.get("state")
    if not isinstance(state, dict):
        raise SnapshotInvalide("état brut absent")
    try:
        deplacements = tuple(
            DeplacementBrut(
                int(ligne["IDdeplacement"]),
                _decoder_valeur_sqlite(ligne["IDpersonne"]),
                _decoder_valeur_sqlite(ligne["IDremboursement"]),
            )
            for ligne in state["deplacements"]
        )
        remboursements = tuple(
            RemboursementBrut(
                int(ligne["IDremboursement"]),
                _decoder_valeur_sqlite(ligne["IDpersonne"]),
                _decoder_valeur_sqlite(ligne["listeIDdeplacement"]),
            )
            for ligne in state["remboursements"]
        )
    except Exception as exc:
        if isinstance(exc, SnapshotInvalide):
            raise
        raise SnapshotInvalide("structure d'état invalide") from exc
    etat = EtatRattachements(deplacements, remboursements)
    empreinte = empreinte_etat(etat)
    if document.get("before_state_sha256") != empreinte:
        raise SnapshotInvalide("empreinte de l'état avant incohérente")
    return document, etat


def appliquer_base_sqlite(
    chemin,
    *,
    recuperer_parent_unique: bool = False,
    chemin_snapshot=None,
) -> ResultatMigration:
    chemin = Path(chemin)
    snapshot = (
        Path(chemin_snapshot)
        if chemin_snapshot is not None
        else _chemin_snapshot_defaut(chemin)
    )
    connexion = sqlite3.connect(
        _uri_sqlite(chemin, "rw"), uri=True, isolation_level=None
    )
    try:
        connexion.execute("BEGIN IMMEDIATE")
        etat_avant = _lire_etat(connexion)
        plan = planifier_etat(
            etat_avant,
            recuperer_parent_unique=recuperer_parent_unique,
        )
        if plan.blocages:
            raise MigrationBloquee(plan.render_text())

        etat_apres_prevu = _appliquer_actions_en_memoire(etat_avant, plan)
        _ecrire_snapshot(
            snapshot,
            chemin_base=chemin,
            etat_avant=etat_avant,
            plan=plan,
            etat_apres_prevu=etat_apres_prevu,
        )

        for action in plan.actions_enfants:
            curseur = connexion.execute(
                "UPDATE deplacements SET IDremboursement = ? WHERE IDdeplacement = ?",
                (action.apres, action.identifiant),
            )
            if curseur.rowcount != 1:
                raise RuntimeError(
                    "déplacement %d introuvable pendant l'application"
                    % action.identifiant
                )
        for action in plan.actions_projections:
            curseur = connexion.execute(
                "UPDATE remboursements SET listeIDdeplacement = ? WHERE IDremboursement = ?",
                (action.apres, action.identifiant),
            )
            if curseur.rowcount != 1:
                raise RuntimeError(
                    "remboursement %d introuvable pendant l'application"
                    % action.identifiant
                )

        etat_apres = _lire_etat(connexion)
        empreinte_apres = empreinte_etat(etat_apres)
        empreinte_prevue = empreinte_etat(etat_apres_prevu)
        if empreinte_apres != empreinte_prevue:
            raise RuntimeError(
                "l'état obtenu ne correspond pas au plan ; transaction annulée"
            )
        plan_recontrole = planifier_etat(
            etat_apres,
            recuperer_parent_unique=False,
        )
        if plan_recontrole.blocages or plan_recontrole.actions:
            raise RuntimeError(
                "la vérification post-migration détecte encore des écarts ; transaction annulée"
            )
        connexion.commit()
        return ResultatMigration(plan, snapshot, empreinte_apres)
    except Exception:
        if connexion.in_transaction:
            connexion.rollback()
        raise
    finally:
        connexion.close()


def restaurer_snapshot_sqlite(chemin, chemin_snapshot) -> ResultatRollback:
    chemin = Path(chemin)
    snapshot = Path(chemin_snapshot)
    document, etat_original = _charger_snapshot(snapshot)
    source_database = document.get("source_database")
    if not isinstance(source_database, str):
        raise SnapshotInvalide("chemin de base source absent")
    if Path(source_database).resolve() != chemin.resolve():
        raise RollbackRefuse(
            "le snapshot appartient à une autre base : %s" % source_database
        )
    empreinte_apres_prevue = document.get("planned_after_state_sha256")
    if not isinstance(empreinte_apres_prevue, str):
        raise SnapshotInvalide("empreinte post-migration absente")

    connexion = sqlite3.connect(
        _uri_sqlite(chemin, "rw"), uri=True, isolation_level=None
    )
    try:
        connexion.execute("BEGIN IMMEDIATE")
        etat_courant = _lire_etat(connexion)
        if empreinte_etat(etat_courant) != empreinte_apres_prevue:
            raise RollbackRefuse(
                "l'état courant diffère de l'état post-migration enregistré ; rollback refusé pour ne pas écraser des changements ultérieurs"
            )

        for ligne in etat_original.deplacements:
            curseur = connexion.execute(
                "UPDATE deplacements SET IDremboursement = ? WHERE IDdeplacement = ?",
                (ligne.IDremboursement, ligne.IDdeplacement),
            )
            if curseur.rowcount != 1:
                raise RollbackRefuse(
                    "déplacement %d absent pendant le rollback"
                    % ligne.IDdeplacement
                )
        for ligne in etat_original.remboursements:
            curseur = connexion.execute(
                "UPDATE remboursements SET listeIDdeplacement = ? WHERE IDremboursement = ?",
                (ligne.listeIDdeplacement, ligne.IDremboursement),
            )
            if curseur.rowcount != 1:
                raise RollbackRefuse(
                    "remboursement %d absent pendant le rollback"
                    % ligne.IDremboursement
                )

        etat_restaure = _lire_etat(connexion)
        empreinte_restauree = empreinte_etat(etat_restaure)
        if empreinte_restauree != document.get("before_state_sha256"):
            raise RuntimeError(
                "le rollback n'a pas restauré exactement l'état snapshot ; transaction annulée"
            )
        connexion.commit()
        return ResultatRollback(snapshot, empreinte_restauree)
    except Exception:
        if connexion.in_transaction:
            connexion.rollback()
        raise
    finally:
        connexion.close()


__all__ = [
    "ActionMigration",
    "BlocageMigration",
    "DeplacementBrut",
    "EtatRattachements",
    "MigrationBloquee",
    "PlanMigration",
    "RemboursementBrut",
    "ResultatMigration",
    "ResultatRollback",
    "RollbackRefuse",
    "SnapshotInvalide",
    "appliquer_base_sqlite",
    "empreinte_etat",
    "planifier_base_sqlite",
    "planifier_etat",
    "restaurer_snapshot_sqlite",
]
