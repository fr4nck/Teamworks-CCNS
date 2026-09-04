from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class PersonView:
    """Projection de présentation agrégée pour l'écran Individus / Contrats.

    Tous les champs affichés sont des chaînes prêtes à rendre. ``id_historique``
    conserve séparément l'identifiant entier de la base historique lorsqu'il est
    réellement disponible. Les valeurs absentes d'une source métier canonique
    sont neutralisées par ``—`` dans l'adaptateur, jamais inventées dans la vue Qt.

    ``first_name`` et ``last_name`` sont conservés séparément afin que la page
    Généralités respecte les champs historiques Nom / Prénom sans tenter de
    redécouper artificiellement ``name``.
    """

    id: str
    id_historique: int | None
    name: str
    first_name: str
    last_name: str
    birth_date: str
    role: str
    classification: str
    contract: str
    weekly_hours: str
    status: str
    site: str
    medical: str
    mutual: str


@dataclass(frozen=True)
class ContractView:
    """Projection de consultation d'un contrat pour l'UI Qt."""

    kind: str
    start: str
    end: str
    classification: str
    duration: str
    status: str


@dataclass(frozen=True)
class ScenarioView:
    name: str
    period: str
    description: str


@dataclass(frozen=True)
class TripView:
    number: str
    date: str
    purpose: str
    route: str
    distance: str
    tariff: str
    amount: str
    reimbursement: str


@dataclass(frozen=True)
class ReimbursementView:
    number: str
    date: str
    amount: str
    attached_trips: str


class TeamworksReadAdapter(Protocol):
    """Contrat de lecture attendu par la future UI Qt.

    Aucun objet wx, SQL brut ou widget ne doit franchir cette frontière.
    """

    def list_people(self) -> Sequence[PersonView]: ...

    def list_contracts(self, person_id: str | int) -> Sequence[ContractView]: ...

    def list_scenarios(self, person_id: str | int) -> Sequence[ScenarioView]: ...

    def list_trips(self, person_id: str | int) -> Sequence[TripView]: ...

    def list_reimbursements(self, person_id: str | int) -> Sequence[ReimbursementView]: ...


class DemoAdapter:
    """Source factice du POC, remplaçable par un adaptateur métier réel."""

    def list_people(self) -> Sequence[PersonView]:
        return (
            PersonView(
                id="SAL-001",
                id_historique=None,
                name="Gaëlle Desson",
                first_name="Gaëlle",
                last_name="Desson",
                birth_date="12/02/1990",
                role="Animatrice",
                classification="Groupe 3",
                contract="CDI",
                weekly_hours="35 h",
                status="Dossier complet",
                site="La Guerche-de-Bretagne",
                medical="À jour",
                mutual="Affiliée",
            ),
            PersonView(
                id="SAL-002",
                id_historique=None,
                name="Thomas Loddé",
                first_name="Thomas",
                last_name="Loddé",
                birth_date="04/11/1988",
                role="Éducateur sportif",
                classification="Groupe 4",
                contract="CDI intermittent",
                weekly_hours="24 h",
                status="À contrôler",
                site="Bais",
                medical="Échéance proche",
                mutual="Affilié",
            ),
            PersonView(
                id="SAL-003",
                id_historique=None,
                name="Léa Drouillé",
                first_name="Léa",
                last_name="Drouillé",
                birth_date="19/06/2002",
                role="Animatrice",
                classification="Groupe 2",
                contract="CDD",
                weekly_hours="21 h",
                status="Pièce manquante",
                site="Moutiers",
                medical="À planifier",
                mutual="Dispense",
            ),
        )

    def list_contracts(self, person_id: str | int) -> Sequence[ContractView]:
        return (
            ContractView("CDI", "01/09/2024", "—", "Groupe 4", "35 h", "Actif"),
            ContractView("Avenant", "01/09/2026", "31/08/2027", "Groupe 4", "24 h", "À vérifier"),
            ContractView("CDD saisonnier", "06/07/2026", "31/07/2026", "Groupe 2", "35 h", "Terminé"),
        )

    def list_scenarios(self, person_id: str | int) -> Sequence[ScenarioView]:
        return ()

    def list_trips(self, person_id: str | int) -> Sequence[TripView]:
        return ()

    def list_reimbursements(self, person_id: str | int) -> Sequence[ReimbursementView]:
        return ()


class ProductionAdapterStub:
    """Emplacement historique conservé pour compatibilité du POC."""

    def list_people(self) -> Sequence[PersonView]:
        raise RuntimeError("Utiliser TeamworksProductionReadAdapter pour la lecture réelle")

    def list_contracts(self, person_id: str | int) -> Sequence[ContractView]:
        raise RuntimeError("Utiliser TeamworksProductionReadAdapter pour la lecture réelle")

    def list_scenarios(self, person_id: str | int) -> Sequence[ScenarioView]:
        raise RuntimeError("Utiliser TeamworksProductionReadAdapter pour la lecture réelle")

    def list_trips(self, person_id: str | int) -> Sequence[TripView]:
        raise RuntimeError("Utiliser TeamworksProductionReadAdapter pour la lecture réelle")

    def list_reimbursements(self, person_id: str | int) -> Sequence[ReimbursementView]:
        raise RuntimeError("Utiliser TeamworksProductionReadAdapter pour la lecture réelle")
