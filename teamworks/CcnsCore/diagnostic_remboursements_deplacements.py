#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Diagnostic en lecture seule des rattachements remboursements/déplacements.

Décision d'architecture issue de la PR #372 :
- ``deplacements.IDremboursement`` est la source canonique cible ;
- ``remboursements.listeIDdeplacement`` reste une projection de compatibilité.

Ce module n'importe ni wxPython ni GestionDB et n'exécute aucune écriture SQL.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional


class Classification(str, Enum):
    COHERENT = "cohérent"
    PROJECTION_OBSOLETE = "projection obsolète"
    REFERENCE_ORPHELINE = "référence orpheline"
    CONFLIT_ARBITRAGE = "conflit nécessitant arbitrage"


@dataclass(frozen=True)
class Deplacement:
    IDdeplacement: int
    IDpersonne: Optional[int]
    IDremboursement: object


@dataclass(frozen=True)
class Remboursement:
    IDremboursement: int
    IDpersonne: Optional[int]
    listeIDdeplacement: object


@dataclass(frozen=True)
class ProjectionLue:
    ids: tuple[int, ...]
    tokens_invalides: tuple[str, ...]
    ids_dupliques: tuple[int, ...]


@dataclass(frozen=True)
class CasDiagnostic:
    type_cas: str
    entite: str
    classification: Classification
    avant: str
    canonique_propose: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectionCanonique:
    IDremboursement: int
    avant_brut: object
    avant_ids: tuple[int, ...]
    canonique_ids: tuple[int, ...]
    canonique_texte: str
    classification: Classification
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class RapportDiagnostic:
    nombre_deplacements: int
    nombre_remboursements: int
    deplacements_reference_orpheline: tuple[int, ...]
    revendications_projection_incoherentes: tuple[CasDiagnostic, ...]
    revendications_multiples: tuple[CasDiagnostic, ...]
    deplacements_idremboursement_null: tuple[int, ...]
    deplacements_idremboursement_zero: tuple[int, ...]
    projections_canoniques: tuple[ProjectionCanonique, ...]
    cas: tuple[CasDiagnostic, ...]

    def render_text(self) -> str:
        lignes = [
            "Diagnostic remboursements ↔ déplacements — lecture seule",
            "Source canonique cible : deplacements.IDremboursement",
            "Projection de compatibilité : remboursements.listeIDdeplacement",
            "",
            "Synthèse : %d déplacement(s), %d remboursement(s)"
            % (self.nombre_deplacements, self.nombre_remboursements),
            "IDremboursement NULL : %s"
            % (", ".join(map(str, self.deplacements_idremboursement_null)) or "aucun"),
            "IDremboursement 0 : %s"
            % (", ".join(map(str, self.deplacements_idremboursement_zero)) or "aucun"),
            "",
            "Avant → état canonique proposé :",
        ]
        if not self.cas:
            lignes.append("- aucun écart")
        else:
            for cas in self.cas:
                lignes.append(
                    "- [%s] %s : %s → %s"
                    % (
                        cas.classification.value,
                        cas.entite,
                        cas.avant,
                        cas.canonique_propose,
                    )
                )
                for detail in cas.details:
                    lignes.append("  · %s" % detail)

        lignes.extend(("", "Projections canoniques proposées :"))
        for projection in self.projections_canoniques:
            lignes.append(
                "- remboursement %d : %r → %r [%s]"
                % (
                    projection.IDremboursement,
                    projection.avant_brut,
                    projection.canonique_texte,
                    projection.classification.value,
                )
            )
            for detail in projection.details:
                lignes.append("  · %s" % detail)
        return "\n".join(lignes)


def lire_projection(valeur: object) -> ProjectionLue:
    if valeur is None or valeur == "":
        return ProjectionLue((), (), ())

    ids: list[int] = []
    invalides: list[str] = []
    dupliques: list[int] = []
    vus: set[int] = set()
    for token in str(valeur).split("-"):
        token = token.strip()
        if not token:
            invalides.append("<vide>")
            continue
        try:
            IDdeplacement = int(token)
        except (TypeError, ValueError):
            invalides.append(token)
            continue
        if IDdeplacement <= 0:
            invalides.append(token)
            continue
        if IDdeplacement in vus:
            dupliques.append(IDdeplacement)
        else:
            vus.add(IDdeplacement)
        ids.append(IDdeplacement)
    return ProjectionLue(tuple(ids), tuple(invalides), tuple(dupliques))


def _id_remboursement_canonique(valeur: object) -> Optional[int]:
    if valeur is None or valeur == "":
        return None
    IDremboursement = int(valeur)
    return None if IDremboursement == 0 else IDremboursement


def _priorite(classification: Classification) -> int:
    return {
        Classification.COHERENT: 0,
        Classification.PROJECTION_OBSOLETE: 1,
        Classification.REFERENCE_ORPHELINE: 2,
        Classification.CONFLIT_ARBITRAGE: 3,
    }[classification]


def _plus_forte(classifications: Iterable[Classification]) -> Classification:
    return max(classifications, default=Classification.COHERENT, key=_priorite)


class DiagnosticCoherenceRemboursements:
    """Compare les deux représentations persistées sans les modifier."""

    def analyser(
        self,
        deplacements: Iterable[Deplacement],
        remboursements: Iterable[Remboursement],
    ) -> RapportDiagnostic:
        deplacements = tuple(sorted(deplacements, key=lambda x: x.IDdeplacement))
        remboursements = tuple(sorted(remboursements, key=lambda x: x.IDremboursement))
        deplacements_par_id = {x.IDdeplacement: x for x in deplacements}
        remboursements_par_id = {x.IDremboursement: x for x in remboursements}
        projections = {
            x.IDremboursement: lire_projection(x.listeIDdeplacement)
            for x in remboursements
        }

        revendications: dict[int, set[int]] = {}
        for remboursement in remboursements:
            for IDdeplacement in projections[remboursement.IDremboursement].ids:
                revendications.setdefault(IDdeplacement, set()).add(
                    remboursement.IDremboursement
                )

        cas: list[CasDiagnostic] = []
        revendications_incoherentes: list[CasDiagnostic] = []
        revendications_multiples: list[CasDiagnostic] = []
        orphelins: list[int] = []
        valeurs_null: list[int] = []
        valeurs_zero: list[int] = []

        for deplacement in deplacements:
            brut = deplacement.IDremboursement
            canonique = _id_remboursement_canonique(brut)
            parents = tuple(sorted(revendications.get(deplacement.IDdeplacement, set())))

            if brut is None:
                valeurs_null.append(deplacement.IDdeplacement)
            else:
                try:
                    if int(brut) == 0:
                        valeurs_zero.append(deplacement.IDdeplacement)
                except (TypeError, ValueError):
                    pass

            if canonique is not None and canonique not in remboursements_par_id:
                orphelins.append(deplacement.IDdeplacement)
                cas.append(
                    CasDiagnostic(
                        type_cas="reference_enfant_orpheline",
                        entite="déplacement %d" % deplacement.IDdeplacement,
                        classification=Classification.REFERENCE_ORPHELINE,
                        avant="IDremboursement=%s" % canonique,
                        canonique_propose=(
                            "non résolu : remboursement %s inexistant" % canonique
                        ),
                        details=(
                            "Aucune remise à 0 n'est proposée automatiquement : la source canonique elle-même est orpheline.",
                        ),
                    )
                )

            if len(parents) > 1:
                multiple = CasDiagnostic(
                    type_cas="revendication_multiple",
                    entite="déplacement %d" % deplacement.IDdeplacement,
                    classification=Classification.CONFLIT_ARBITRAGE,
                    avant="revendiqué par les remboursements %s" % list(parents),
                    canonique_propose=(
                        "IDremboursement canonique=%s"
                        % (canonique if canonique is not None else "aucun")
                    ),
                )
                revendications_multiples.append(multiple)
                cas.append(multiple)

            if canonique in remboursements_par_id:
                remboursement = remboursements_par_id[canonique]
                if (
                    deplacement.IDpersonne is not None
                    and remboursement.IDpersonne is not None
                    and deplacement.IDpersonne != remboursement.IDpersonne
                ):
                    cas.append(
                        CasDiagnostic(
                            type_cas="personnes_incoherentes",
                            entite="déplacement %d" % deplacement.IDdeplacement,
                            classification=Classification.CONFLIT_ARBITRAGE,
                            avant=(
                                "IDpersonne=%s, IDremboursement=%s, parent IDpersonne=%s"
                                % (
                                    deplacement.IDpersonne,
                                    canonique,
                                    remboursement.IDpersonne,
                                )
                            ),
                            canonique_propose=(
                                "conserver le pointeur dans le diagnostic, arbitrer l'incohérence de personne avant toute migration"
                            ),
                        )
                    )

        for remboursement in remboursements:
            projection = projections[remboursement.IDremboursement]
            if projection.tokens_invalides:
                cas.append(
                    CasDiagnostic(
                        type_cas="projection_invalide",
                        entite="remboursement %d" % remboursement.IDremboursement,
                        classification=Classification.CONFLIT_ARBITRAGE,
                        avant="listeIDdeplacement=%r" % remboursement.listeIDdeplacement,
                        canonique_propose="projection régénérée depuis les clés enfants canoniques",
                        details=(
                            "token(s) invalide(s) : %s" % list(projection.tokens_invalides),
                        ),
                    )
                )
            if projection.ids_dupliques:
                cas.append(
                    CasDiagnostic(
                        type_cas="projection_dupliquee",
                        entite="remboursement %d" % remboursement.IDremboursement,
                        classification=Classification.PROJECTION_OBSOLETE,
                        avant="listeIDdeplacement=%r" % remboursement.listeIDdeplacement,
                        canonique_propose="projection triée avec identifiants uniques",
                        details=(
                            "ID(s) dupliqué(s) : %s"
                            % sorted(set(projection.ids_dupliques)),
                        ),
                    )
                )

            for IDdeplacement in sorted(set(projection.ids)):
                deplacement = deplacements_par_id.get(IDdeplacement)
                if deplacement is None:
                    incoherent = CasDiagnostic(
                        type_cas="projection_reference_deplacement_absent",
                        entite="remboursement %d" % remboursement.IDremboursement,
                        classification=Classification.REFERENCE_ORPHELINE,
                        avant="listeIDdeplacement contient %d" % IDdeplacement,
                        canonique_propose="retirer %d de la projection canonique" % IDdeplacement,
                    )
                    revendications_incoherentes.append(incoherent)
                    cas.append(incoherent)
                    continue

                canonique = _id_remboursement_canonique(deplacement.IDremboursement)
                if canonique == remboursement.IDremboursement:
                    continue
                if canonique is None:
                    classification = Classification.PROJECTION_OBSOLETE
                    proposition = (
                        "déplacement non remboursé ; retirer %d de cette projection"
                        % IDdeplacement
                    )
                else:
                    classification = Classification.CONFLIT_ARBITRAGE
                    proposition = (
                        "rattachement canonique au remboursement %s ; retirer %d de cette projection"
                        % (canonique, IDdeplacement)
                    )
                incoherent = CasDiagnostic(
                    type_cas="projection_contredit_enfant",
                    entite="remboursement %d" % remboursement.IDremboursement,
                    classification=classification,
                    avant=(
                        "revendique déplacement %d, enfant IDremboursement=%r"
                        % (IDdeplacement, deplacement.IDremboursement)
                    ),
                    canonique_propose=proposition,
                )
                revendications_incoherentes.append(incoherent)
                cas.append(incoherent)

        projections_canoniques: list[ProjectionCanonique] = []
        for remboursement in remboursements:
            projection = projections[remboursement.IDremboursement]
            canonique_ids = tuple(
                sorted(
                    deplacement.IDdeplacement
                    for deplacement in deplacements
                    if _id_remboursement_canonique(deplacement.IDremboursement)
                    == remboursement.IDremboursement
                )
            )
            avant_uniques = tuple(sorted(set(projection.ids)))
            classifications: list[Classification] = []
            details: list[str] = []

            if projection.tokens_invalides:
                classifications.append(Classification.CONFLIT_ARBITRAGE)
                details.append(
                    "token(s) invalide(s) : %s" % list(projection.tokens_invalides)
                )
            if projection.ids_dupliques:
                classifications.append(Classification.PROJECTION_OBSOLETE)
                details.append(
                    "ID(s) dupliqué(s) : %s" % sorted(set(projection.ids_dupliques))
                )

            absents = [x for x in avant_uniques if x not in deplacements_par_id]
            if absents:
                classifications.append(Classification.REFERENCE_ORPHELINE)
                details.append("ID(s) de déplacement inexistant(s) : %s" % absents)

            contradictions = []
            for IDdeplacement in avant_uniques:
                deplacement = deplacements_par_id.get(IDdeplacement)
                if deplacement is None:
                    continue
                canonique = _id_remboursement_canonique(deplacement.IDremboursement)
                if canonique not in (None, remboursement.IDremboursement):
                    contradictions.append((IDdeplacement, canonique))
            if contradictions:
                classifications.append(Classification.CONFLIT_ARBITRAGE)
                details.append(
                    "revendication(s) contredisant la clé enfant : %s" % contradictions
                )

            multiples = [
                x
                for x in avant_uniques
                if len(revendications.get(x, set())) > 1
            ]
            if multiples:
                classifications.append(Classification.CONFLIT_ARBITRAGE)
                details.append("revendication(s) multiple(s) : %s" % multiples)

            personnes = []
            for IDdeplacement in canonique_ids:
                deplacement = deplacements_par_id[IDdeplacement]
                if (
                    deplacement.IDpersonne is not None
                    and remboursement.IDpersonne is not None
                    and deplacement.IDpersonne != remboursement.IDpersonne
                ):
                    personnes.append(IDdeplacement)
            if personnes:
                classifications.append(Classification.CONFLIT_ARBITRAGE)
                details.append("incohérence(s) de personne : %s" % personnes)

            if projection.ids != canonique_ids:
                classifications.append(Classification.PROJECTION_OBSOLETE)
                details.append(
                    "projection actuelle %s, projection canonique %s"
                    % (list(projection.ids), list(canonique_ids))
                )

            projections_canoniques.append(
                ProjectionCanonique(
                    IDremboursement=remboursement.IDremboursement,
                    avant_brut=remboursement.listeIDdeplacement,
                    avant_ids=projection.ids,
                    canonique_ids=canonique_ids,
                    canonique_texte="-".join(map(str, canonique_ids)),
                    classification=_plus_forte(classifications),
                    details=tuple(details),
                )
            )

        cas.sort(
            key=lambda x: (
                -_priorite(x.classification),
                x.type_cas,
                x.entite,
                x.avant,
            )
        )
        return RapportDiagnostic(
            nombre_deplacements=len(deplacements),
            nombre_remboursements=len(remboursements),
            deplacements_reference_orpheline=tuple(sorted(orphelins)),
            revendications_projection_incoherentes=tuple(revendications_incoherentes),
            revendications_multiples=tuple(revendications_multiples),
            deplacements_idremboursement_null=tuple(sorted(valeurs_null)),
            deplacements_idremboursement_zero=tuple(sorted(valeurs_zero)),
            projections_canoniques=tuple(projections_canoniques),
            cas=tuple(cas),
        )


def analyser_connexion(connexion) -> RapportDiagnostic:
    """Analyse une connexion DB-API compatible en exécutant uniquement deux SELECT."""
    curseur = connexion.cursor()
    curseur.execute(
        "SELECT IDdeplacement, IDpersonne, IDremboursement "
        "FROM deplacements ORDER BY IDdeplacement;"
    )
    deplacements = [Deplacement(*ligne) for ligne in curseur.fetchall()]
    curseur.execute(
        "SELECT IDremboursement, IDpersonne, listeIDdeplacement "
        "FROM remboursements ORDER BY IDremboursement;"
    )
    remboursements = [Remboursement(*ligne) for ligne in curseur.fetchall()]
    return DiagnosticCoherenceRemboursements().analyser(deplacements, remboursements)


def analyser_base_sqlite(chemin) -> RapportDiagnostic:
    """Ouvre un fichier SQLite existant explicitement en lecture seule puis l'analyse."""
    uri = Path(chemin).resolve().as_uri() + "?mode=ro"
    connexion = sqlite3.connect(uri, uri=True)
    try:
        return analyser_connexion(connexion)
    finally:
        connexion.close()
