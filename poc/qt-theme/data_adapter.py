from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class PersonView:
    id: str
    name: str
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
    kind: str
    start: str
    end: str
    classification: str
    duration: str
    status: str
    active: bool


class TeamworksReadAdapter(Protocol):
    """Contrat de lecture attendu par la future UI Qt.

    Aucun objet wx, SQL brut ou widget ne doit franchir cette frontière.
    """

    def list_people(self) -> Sequence[PersonView]: ...

    def list_contracts(self, person_id: str) -> Sequence[ContractView]: ...


class DemoAdapter:
    """Source factice du POC, remplaçable plus tard par un adaptateur métier réel."""

    def list_people(self) -> Sequence[PersonView]:
        return (
            PersonView("SAL-001", "Gaëlle Desson", "Animatrice", "Groupe 3", "CDI", "35 h", "Dossier complet", "La Guerche-de-Bretagne", "À jour", "Affiliée"),
            PersonView("SAL-002", "Thomas Loddé", "Éducateur sportif", "Groupe 4", "CDI intermittent", "24 h", "À contrôler", "Bais", "Échéance proche", "Affilié"),
            PersonView("SAL-003", "Léa Drouillé", "Animatrice", "Groupe 2", "CDD", "21 h", "Pièce manquante", "Moutiers", "À planifier", "Dispense"),
        )

    def list_contracts(self, person_id: str) -> Sequence[ContractView]:
        return (
            ContractView("CDI", "01/09/2024", "—", "Groupe 4", "35 h", "Actif", True),
            ContractView("Avenant", "01/09/2026", "31/08/2027", "Groupe 4", "24 h", "À vérifier", True),
            ContractView("CDD saisonnier", "06/07/2026", "31/07/2026", "Groupe 2", "35 h", "Terminé", False),
        )


class ProductionAdapterStub:
    """Emplacement volontairement inactif du futur branchement Teamworks.

    Le jour où le POC passe GO, cette classe devra appeler les services applicatifs
    ou repositories existants. Elle ne doit jamais importer la couche wxPython.
    """

    def list_people(self) -> Sequence[PersonView]:
        raise RuntimeError("Adaptateur production désactivé dans le POC isolé")

    def list_contracts(self, person_id: str) -> Sequence[ContractView]:
        raise RuntimeError("Adaptateur production désactivé dans le POC isolé")
