from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation, localcontext
from typing import Sequence

from data_adapter import (
    ContractView,
    PersonCoordinateView,
    PersonGeneralitiesView,
    PersonView,
    ReimbursementView,
    ScenarioView,
    TeamworksReadAdapter,
    TripView,
)
from infrastructure.persistence.ccns_data_reader import CcnsDataReader
from infrastructure.persistence.individual_activity_reader import IndividualActivityReader
from infrastructure.persistence.person_reader import PersonReader
from infrastructure.persistence.teamworks_contract_conversions import as_date


EMPTY = "—"


class TeamworksProductionReadAdapter(TeamworksReadAdapter):
    """Adaptateur lecture seule vers les readers historiques Teamworks.

    Cette classe ne contient aucun SQL. Elle coordonne les readers dédiés puis
    produit les DTO de présentation attendus par Qt.
    """

    def __init__(self, person_reader=None, contract_reader=None, activity_reader=None):
        self._closed = False
        self.startup_timings: dict[str, float | int | bool] = {
            "person_reader_construction_seconds": 0.0,
            "contract_reader_construction_seconds": 0.0,
            "activity_reader_construction_seconds": 0.0,
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
        self._activity_reader = activity_reader or IndividualActivityReader(
            db_factory=lambda: self._profiled_db_factory("activity")
        )
        activity_ready = time.perf_counter()
        self.startup_timings.update(
            {
                "person_reader_construction_seconds": person_ready - started,
                "contract_reader_construction_seconds": contract_ready - person_ready,
                "activity_reader_construction_seconds": activity_ready - contract_ready,
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

    def get_person_generalities(self, person_id: str | int) -> PersonGeneralitiesView | None:
        self._ensure_open()
        historical_id = self._require_historical_id(person_id)
        record = self._person_reader.lire_generalites(historical_id)
        if record is None:
            return None
        coordinates = tuple(
            PersonCoordinateView(
                key=int(item.IDcoord),
                category=_text(item.categorie),
                text=_text(item.texte),
                label=_text(item.intitule, empty=""),
            )
            for item in self._person_reader.lire_coordonnees(historical_id)
        )
        return PersonGeneralitiesView(
            civility=_text(record.civilite),
            maiden_name=_text(record.nom_jfille),
            last_name=_text(record.nom),
            first_name=_text(record.prenom),
            birth_date=_format_date(record.date_naiss),
            birth_country=_text(record.pays_naiss),
            birth_postcode=_format_postcode(record.cp_naiss),
            birth_city=_text(record.ville_naiss),
            nationality=_text(record.nationalite),
            social_situation=_text(record.situation),
            address=_text(record.adresse_resid, empty=""),
            postcode=_format_postcode(record.cp_resid),
            city=_text(record.ville_resid),
            memo=_text(record.memo, empty=""),
            coordinates=coordinates,
        )

    def list_contracts(self, person_id: str | int) -> Sequence[ContractView]:
        self._ensure_open()
        historical_id = self._require_historical_id(person_id)
        records = self._contract_reader.lire_contrats_personne(historical_id)
        return tuple(self._contract_to_view(record) for record in records)

    def list_scenarios(self, person_id: str | int) -> Sequence[ScenarioView]:
        self._ensure_open()
        historical_id = self._require_historical_id(person_id)
        records = self._activity_reader.lire_scenarios_personne(historical_id)
        return tuple(
            ScenarioView(
                name=_text(record.nom),
                period=_scenario_period(record.date_debut, record.date_fin),
                description=_scenario_description(record.description),
            )
            for record in records
        )

    def list_trips(self, person_id: str | int) -> Sequence[TripView]:
        self._ensure_open()
        historical_id = self._require_historical_id(person_id)
        records = self._activity_reader.lire_deplacements_personne(historical_id)
        return tuple(self._trip_to_view(record) for record in records)

    def list_reimbursements(self, person_id: str | int) -> Sequence[ReimbursementView]:
        self._ensure_open()
        historical_id = self._require_historical_id(person_id)
        records = self._activity_reader.lire_remboursements_personne(historical_id)
        return tuple(
            ReimbursementView(
                number=str(record.IDremboursement),
                date=_format_date(record.date),
                amount=_format_money(record.montant),
                attached_trips=_format_attached_trip_ids(record.listeIDdeplacement),
            )
            for record in records
        )

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
    def _trip_to_view(record) -> TripView:
        start = _text(record.ville_depart, empty="")
        end = _text(record.ville_arrivee, empty="")
        if not start and not end:
            route = EMPTY
        else:
            separator = " <--> " if _is_round_trip(record.aller_retour) else " -> "
            route = f"{start}{separator}{end}".strip()
        reimbursement = (
            ""
            if record.IDremboursement in (None, 0, "")
            else f"N°{record.IDremboursement}"
        )
        return TripView(
            number=str(record.IDdeplacement),
            date=_format_date(record.date),
            purpose=_text(record.objet),
            route=route,
            distance=_format_unit(record.distance, "Km"),
            tariff=_format_unit(record.tarif_km, "€/km"),
            amount=_format_product_money(record.distance, record.tarif_km),
            reimbursement=reimbursement,
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
        for reader in (self._activity_reader, self._contract_reader, self._person_reader):
            try:
                reader.close()
            except Exception as exc:
                errors.append(exc)
        self._closed = True
        if errors:
            raise errors[0]


def _format_date(value) -> str:
    parsed = as_date(value)
    return EMPTY if parsed is None else parsed.strftime("%d/%m/%Y")


def _format_postcode(value) -> str:
    if value is None or isinstance(value, bool):
        return EMPTY
    text = str(value).strip()
    if not text:
        return EMPTY
    try:
        return f"{int(text):05d}"
    except (TypeError, ValueError):
        return text


def _format_hours(value) -> str:
    if value is None:
        return EMPTY
    text = str(value).strip()
    if not text:
        return EMPTY
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"{text} h"


def _text(value, *, empty: str = EMPTY) -> str:
    if value is None:
        return empty
    text = str(value).strip()
    return text or empty


def _scenario_period(start, end) -> str:
    start_text = _format_date(start)
    end_text = _format_date(end)
    if EMPTY in (start_text, end_text):
        return EMPTY
    return f"Du {start_text} au {end_text}"


def _scenario_description(value) -> str:
    text = _text(value, empty="")
    return text or "Aucune description"


def _is_round_trip(value) -> bool:
    return value is True or str(value) == "True"


def _format_unit(value, unit: str) -> str:
    text = _text(value, empty="")
    return EMPTY if not text else f"{text} {unit}"


def _decimal(value) -> Decimal:
    if value is None or isinstance(value, bool):
        raise InvalidOperation
    text = str(value).strip().replace(",", ".")
    if not text:
        raise InvalidOperation
    return Decimal(text)


def _format_money(value) -> str:
    try:
        with localcontext() as context:
            context.prec = 28
            amount = _decimal(value)
            return f"{amount:.2f} €"
    except (InvalidOperation, ValueError):
        return EMPTY


def _format_product_money(left, right) -> str:
    try:
        with localcontext() as context:
            context.prec = 28
            amount = _decimal(left) * _decimal(right)
            return f"{amount:.2f} €"
    except (InvalidOperation, ValueError):
        return EMPTY


def _format_attached_trip_ids(value) -> str:
    if value is None or value == "":
        return "Aucun déplacement rattaché"
    if isinstance(value, bool):
        return EMPTY
    if isinstance(value, int):
        ids = [str(value)]
    else:
        text = str(value).strip()
        ids = [part for part in text.split("-") if part] if text else []
    if not ids:
        return "Aucun déplacement rattaché"
    return "N° " + ", ".join(ids)


def build_production_adapter() -> TeamworksProductionReadAdapter:
    return TeamworksProductionReadAdapter()
