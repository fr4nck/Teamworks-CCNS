from __future__ import annotations

from typing import Sequence

from data_adapter import ContractView, PersonView, TeamworksReadAdapter
from infrastructure.persistence.ccns_data_reader import CcnsDataReader
from infrastructure.persistence.person_reader import PersonReader
from infrastructure.persistence.teamworks_contract_conversions import as_date


EMPTY = "—"


class TeamworksProductionReadAdapter(TeamworksReadAdapter):
    """Adaptateur lecture seule vers les readers historiques Teamworks.

    Cette classe ne contient aucun SQL. Elle coordonne exclusivement les API
    actuelles de ``PersonReader`` et ``CcnsDataReader`` puis produit les DTO de
    présentation attendus par Qt.
    """

    def __init__(self, person_reader=None, contract_reader=None):
        self._person_reader = person_reader or PersonReader()
        self._contract_reader = contract_reader or CcnsDataReader()
        self._closed = False

    def list_people(self) -> Sequence[PersonView]:
        self._ensure_open()
        records = self._person_reader.lire_identites()
        views = []
        for record in records:
            historical_id = self._require_historical_id(record.IDpersonne)
            first_name = (record.prenom or "").strip() or EMPTY
            last_name = (record.nom or "").strip() or EMPTY
            name = " ".join(part for part in (record.prenom, record.nom) if part).strip() or EMPTY
            views.append(
                PersonView(
                    id=EMPTY,
                    id_historique=historical_id,
                    name=name,
                    first_name=first_name,
                    last_name=last_name,
                    birth_date=EMPTY,
                    role=EMPTY,
                    classification=EMPTY,
                    contract=EMPTY,
                    weekly_hours=EMPTY,
                    status=EMPTY,
                    site=EMPTY,
                    medical=EMPTY,
                    mutual=EMPTY,
                )
            )
        return tuple(views)

    def list_contracts(self, person_id: str | int) -> Sequence[ContractView]:
        self._ensure_open()
        historical_id = self._require_historical_id(person_id)
        records = self._contract_reader.lire_contrats_personne(historical_id)
        return tuple(self._contract_to_view(record) for record in records)

    @staticmethod
    def _contract_to_view(record) -> ContractView:
        return ContractView(
            kind=record.type_contrat or EMPTY,
            start=_format_date(record.date_debut),
            end=_format_date(record.date_fin),
            classification=record.classification or EMPTY,
            duration=_format_hours(record.temps_hebdo),
            status=EMPTY,
        )

    @staticmethod
    def _require_historical_id(value) -> int:
        if value is None or isinstance(value, bool):
            raise ValueError("IDpersonne historique obligatoire pour la lecture production")
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("IDpersonne historique invalide") from exc
        if result <= 0:
            raise ValueError("IDpersonne historique invalide")
        return result

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Adaptateur de production déjà fermé")

    def close(self) -> None:
        if self._closed:
            return
        errors = []
        for reader in (self._contract_reader, self._person_reader):
            try:
                reader.close()
            except Exception as exc:  # nettoyage best-effort des deux ressources
                errors.append(exc)
        self._closed = True
        if errors:
            raise errors[0]


def _format_date(value) -> str:
    parsed = as_date(value)
    return EMPTY if parsed is None else parsed.strftime("%d/%m/%Y")


def _format_hours(value) -> str:
    if value is None:
        return EMPTY
    text = str(value).strip()
    if not text:
        return EMPTY
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"{text} h"


def build_production_adapter() -> TeamworksProductionReadAdapter:
    return TeamworksProductionReadAdapter()
