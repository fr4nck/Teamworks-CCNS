from __future__ import annotations

import time
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

    ``startup_timings`` ne modifie aucun comportement métier : il expose
    uniquement des mesures monotones permettant de distinguer import de
    ``GestionDB``, ouverture de connexion, lecture SQL et mapping Python.
    """

    def __init__(self, person_reader=None, contract_reader=None):
        self._closed = False
        self.startup_timings: dict[str, float | int | bool] = {
            "person_reader_construction_seconds": 0.0,
            "contract_reader_construction_seconds": 0.0,
            "people_gestiondb_import_seconds": 0.0,
            "people_db_open_seconds": 0.0,
            "people_db_is_network": False,
            "people_reader_seconds": 0.0,
            "people_mapping_seconds": 0.0,
            "people_count": 0,
        }

        started = time.perf_counter()
        self._person_reader = person_reader or PersonReader(
            db_factory=lambda: self._profiled_db_factory("people")
        )
        person_ready = time.perf_counter()
        self._contract_reader = contract_reader or CcnsDataReader(
            db_factory=lambda: self._profiled_db_factory("contracts")
        )
        contract_ready = time.perf_counter()
        self.startup_timings.update(
            {
                "person_reader_construction_seconds": person_ready - started,
                "contract_reader_construction_seconds": contract_ready - person_ready,
            }
        )

    def _profiled_db_factory(self, prefix: str):
        phase = time.perf_counter()
        import GestionDB
        imported = time.perf_counter()
        db = GestionDB.DB()
        opened = time.perf_counter()

        self.startup_timings[f"{prefix}_gestiondb_import_seconds"] = imported - phase
        self.startup_timings[f"{prefix}_db_open_seconds"] = opened - imported
        self.startup_timings[f"{prefix}_db_is_network"] = bool(getattr(db, "isNetwork", False))
        return db

    def list_people(self) -> Sequence[PersonView]:
        self._ensure_open()

        # Force explicitement la première ouverture afin de ne pas mélanger le
        # coût d'import/connexion historique avec celui du SELECT lui-même.
        _ = self._person_reader.db

        reader_started = time.perf_counter()
        records = self._person_reader.lire_identites()
        reader_finished = time.perf_counter()

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
        mapping_finished = time.perf_counter()
        self.startup_timings.update(
            {
                "people_reader_seconds": reader_finished - reader_started,
                "people_mapping_seconds": mapping_finished - reader_finished,
                "people_count": len(records),
            }
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
