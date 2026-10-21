"""Moteur pur de comparaison des effectifs et ETP, sans wx ni SQL.

Les profils de simulation NE CONSTITUENT PAS des référentiels déclaratifs.
Toutes les dates de contrat sont inclusives. Les valeurs internes sont en Decimal.
"""
from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_DOWN
from enum import Enum
from typing import Iterable


class Categorie(str, Enum):
    CDI = "CDI"
    CDD = "CDD"
    CDII = "CDII"
    CEE = "CEE"
    APPRENTISSAGE = "APPRENTISSAGE"
    PROFESSIONNALISATION = "PROFESSIONNALISATION"
    STAGE = "STAGE"
    SERVICE_CIVIQUE = "SERVICE_CIVIQUE"
    AUTRE = "AUTRE"


class Mesure(str, Enum):
    ETP = "ETP"
    PERSONNES = "PERSONNES"


class MoisRetenus(str, Enum):
    DOUZE = "DOUZE"
    AVEC_SALARIES = "AVEC_SALARIES"


@dataclass(frozen=True)
class Profil:
    code: str
    version: str
    libelle: str
    categories_incluses: frozenset[Categorie]
    mesure: Mesure = Mesure.ETP
    mois_retenus: MoisRetenus = MoisRetenus.DOUZE
    heures_temps_plein: Decimal = Decimal("35")
    exclure_cdd_remplacement: bool = False
    annee_debut: int = 2025
    annee_fin: int | None = None
    reglementaire_valide: bool = False
    sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all(isinstance(s, str) and s.strip() for s in (self.code, self.version, self.libelle)):
            raise ValueError("Code, version et libellé du profil obligatoires")
        cats = frozenset(self.categories_incluses)
        if not all(isinstance(c, Categorie) for c in cats):
            raise ValueError("Catégorie contractuelle inconnue")
        object.__setattr__(self, "categories_incluses", cats)
        if not isinstance(self.mesure, Mesure) or not isinstance(self.mois_retenus, MoisRetenus):
            raise ValueError("Type de mesure ou de dénominateur invalide")
        if not isinstance(self.heures_temps_plein, Decimal) or not self.heures_temps_plein.is_finite() or self.heures_temps_plein <= 0:
            raise ValueError("Référence hebdomadaire invalide")
        if not 1900 <= self.annee_debut <= 2100 or (self.annee_fin is not None and self.annee_fin < self.annee_debut):
            raise ValueError("Période du profil invalide")
        if self.reglementaire_valide and not self.sources:
            raise ValueError("Un profil réglementaire validé exige ses sources")


@dataclass(frozen=True)
class ContratETP:
    id_contrat: str
    id_salarie: str
    categorie: Categorie
    debut: date
    fin: date | None
    heures_hebdo: Decimal | None
    remplace_absent: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id_contrat, str) or not self.id_contrat.strip():
            raise ValueError("Identifiant contrat obligatoire")
        if not isinstance(self.id_salarie, str) or not self.id_salarie.strip():
            raise ValueError("Identifiant salarié obligatoire")
        if not isinstance(self.categorie, Categorie):
            raise ValueError("Catégorie de contrat invalide")
        if type(self.debut) is not date or (self.fin is not None and type(self.fin) is not date):
            raise ValueError("Dates de contrat invalides")
        if self.fin is not None and self.fin < self.debut:
            raise ValueError("Fin de contrat antérieure au début")
        if self.heures_hebdo is not None and (
            not isinstance(self.heures_hebdo, Decimal)
            or not self.heures_hebdo.is_finite()
            or self.heures_hebdo <= 0
        ):
            raise ValueError("Heures contractuelles invalides")
        if self.remplace_absent is not None and type(self.remplace_absent) is not bool:
            raise ValueError("Statut de remplacement invalide")


@dataclass(frozen=True)
class Anomalie:
    code: str
    id_contrat: str
    message: str
    bloquante: bool = True


@dataclass(frozen=True)
class DetailSalarie:
    id_salarie: str
    valeur: Decimal
    contrats: tuple[str, ...]


@dataclass(frozen=True)
class DetailMois:
    mois: int
    total: Decimal
    salaries: tuple[DetailSalarie, ...]


@dataclass(frozen=True)
class ResultatETP:
    annee: int
    profil: Profil
    mois: tuple[DetailMois, ...]
    total_brut: Decimal
    total_affiche: Decimal
    diviseur: int
    exclus: tuple[str, ...]
    anomalies: tuple[Anomalie, ...]

    @property
    def complet(self) -> bool:
        return self.diviseur > 0 and not any(a.bloquante for a in self.anomalies)

    @property
    def declarable(self) -> bool:
        return self.complet and self.profil.reglementaire_valide


def profil_simulation(*, inclure_cee: bool, inclure_apprentis: bool) -> Profil:
    """Une combinaison de simulation parmi les quatre possibles."""
    categories = {Categorie.CDI, Categorie.CDD, Categorie.CDII}
    if inclure_cee:
        categories.add(Categorie.CEE)
    if inclure_apprentis:
        categories.add(Categorie.APPRENTISSAGE)
    return Profil(
        code="SIM-CEE%d-APP%d" % (inclure_cee, inclure_apprentis),
        version="2025-01",
        libelle="Simulation CEE=%s apprentis=%s" % (inclure_cee, inclure_apprentis),
        categories_incluses=frozenset(categories),
    )


def profils_comparaison() -> tuple[Profil, ...]:
    return tuple(
        profil_simulation(inclure_cee=cee, inclure_apprentis=app)
        for cee, app in ((False, False), (True, False), (False, True), (True, True))
    )


def calculer_etp(
    contrats: Iterable[ContratETP],
    annee: int,
    profil: Profil,
    anomalies_import: Iterable[Anomalie] = (),
) -> ResultatETP:
    """Calcule douze mois, avec prorata des jours calendaires et du temps contractuel.

    Les situations non documentées produisent des anomalies bloquantes. Deux
    contrats simultanés d'une même personne sont plafonnés à une unité PAR JOUR
    pour éviter le double comptage, mais l'ambiguïté reste bloquante.
    """
    if type(annee) is not int or not 1900 <= annee <= 2100:
        raise ValueError("Année invalide")
    if not isinstance(profil, Profil):
        raise TypeError("Profil requis")
    incidents = list(anomalies_import)
    if annee < profil.annee_debut or (profil.annee_fin is not None and annee > profil.annee_fin):
        incidents.append(Anomalie("PROFIL_HORS_PERIODE", "", "Profil non applicable à cet exercice"))
    retenus: dict[str, list[ContratETP]] = {}
    exclus: set[str] = set()
    identifiants: set[str] = set()
    for contrat in contrats:
        if not isinstance(contrat, ContratETP):
            raise TypeError("ContratETP requis")
        if contrat.id_contrat in identifiants:
            incidents.append(Anomalie("CONTRAT_DUPLIQUE", contrat.id_contrat, "Identifiant de contrat répété"))
            continue
        identifiants.add(contrat.id_contrat)
        if contrat.debut > date(annee, 12, 31) or (contrat.fin and contrat.fin < date(annee, 1, 1)):
            continue
        if contrat.categorie is Categorie.AUTRE:
            incidents.append(Anomalie("TYPE_NON_QUALIFIE", contrat.id_contrat, "Type de contrat à qualifier"))
            continue
        if contrat.categorie not in profil.categories_incluses:
            exclus.add(contrat.id_contrat)
            continue
        if contrat.categorie is Categorie.CDD and profil.exclure_cdd_remplacement:
            if contrat.remplace_absent is None:
                incidents.append(Anomalie("REMPLACEMENT_INCONNU", contrat.id_contrat, "Motif du CDD absent"))
                continue
            if contrat.remplace_absent:
                exclus.add(contrat.id_contrat)
                continue
        if profil.mesure is Mesure.ETP and contrat.heures_hebdo is None:
            incidents.append(Anomalie("HEURES_MANQUANTES", contrat.id_contrat, "Horaire contractuel absent"))
            continue
        retenus.setdefault(contrat.id_salarie, []).append(contrat)

    mois_calcules: list[DetailMois] = []
    chevauchements_vus: set[tuple[str, tuple[str, ...]]] = set()
    for mois in range(1, 13):
        nb_jours = monthrange(annee, mois)[1]
        debut_mois, fin_mois = date(annee, mois, 1), date(annee, mois, nb_jours)
        details: list[DetailSalarie] = []
        for id_salarie, contrats_salarie in sorted(retenus.items()):
            contrats_actifs = [
                c for c in contrats_salarie
                if c.debut <= fin_mois and (c.fin is None or c.fin >= debut_mois)
            ]
            if not contrats_actifs:
                continue
            cumul = Decimal(0)
            utilises: set[str] = set()
            for jour in range(1, nb_jours + 1):
                date_jour = date(annee, mois, jour)
                actifs = [c for c in contrats_actifs if c.debut <= date_jour and (c.fin is None or c.fin >= date_jour)]
                if not actifs:
                    continue
                utilises.update(c.id_contrat for c in actifs)
                if len(actifs) > 1:
                    signature = (id_salarie, tuple(sorted(c.id_contrat for c in actifs)))
                    if signature not in chevauchements_vus:
                        chevauchements_vus.add(signature)
                        incidents.append(Anomalie(
                            "CONTRATS_CHEVAUCHANTS", ",".join(signature[1]),
                            "Contrats simultanés d'un même salarié : vérification nécessaire",
                        ))
                if profil.mesure is Mesure.PERSONNES:
                    cumul += Decimal(1)
                else:
                    fraction = sum((c.heures_hebdo / profil.heures_temps_plein for c in actifs), Decimal(0))
                    cumul += min(Decimal(1), fraction)
            if cumul:
                details.append(DetailSalarie(id_salarie, cumul / Decimal(nb_jours), tuple(sorted(utilises))))
        mois_calcules.append(DetailMois(mois, sum((d.valeur for d in details), Decimal(0)), tuple(details)))

    if not retenus:
        incidents.append(Anomalie("AUCUN_CONTRAT_RETENU", "", "Aucun contrat évaluable dans le périmètre"))
    if profil.mois_retenus is MoisRetenus.DOUZE:
        diviseur = 12
    else:
        diviseur = sum(1 for m in mois_calcules if m.salaries)
    if diviseur == 0:
        incidents.append(Anomalie("DIVISEUR_NUL", "", "Aucun mois avec salarié retenu"))
    brut = sum((m.total for m in mois_calcules), Decimal(0)) / Decimal(diviseur) if diviseur else Decimal(0)
    total = brut.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    return ResultatETP(
        annee, profil, tuple(mois_calcules), brut, total, diviseur,
        tuple(sorted(exclus)), tuple(incidents),
    )
