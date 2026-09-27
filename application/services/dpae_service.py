"""Façade applicative DPAE de Teamworks.

DATA-001 : l'appelant fournit la référence contrat. Les valeurs RH déclarables
sont résolues par un port read-only avant d'être figées par la persistance DPAE.
"""
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class PrepareDpae:
    command_id: str
    case_key: str
    contract_id: str
    actor_id: str


@dataclass(frozen=True)
class DpaeBusinessData:
    """Résultat canonique du resolver Teamworks, sans dépendance au schéma legacy."""
    contract_id: str
    canonical_payload: str
    source_fingerprint: str
    rules_version: str
    payload_hash: str


class DpaeBusinessDataResolver(Protocol):
    def resolve(self, contract_id: str) -> DpaeBusinessData:
        ...


@dataclass(frozen=True)
class SubmitDpae:
    command_id: str
    case_id: str
    actor_id: str


@dataclass(frozen=True)
class IngestDpaeReturn:
    provider: str
    return_type: str
    raw_hash: str
    received_at: object
    external_return_id: Optional[str] = None
    external_flux_id: Optional[str] = None
    employer_siret: Optional[str] = None


@dataclass(frozen=True)
class TransmissionResult:
    outcome: str
    external_flux_id: Optional[str] = None
    reason_code: Optional[str] = None


class DpaeService:
    """Façade DPAE ; les retries de transport travaillent sur le snapshot durable."""

    def __init__(self, adapter, transport=None, resolver: Optional[DpaeBusinessDataResolver] = None):
        self._adapter = adapter
        self._transport = transport
        self._resolver = resolver

    def prepare(self, command: PrepareDpae):
        # DATA-001 : reconnaître un replay durable AVANT de relire les données
        # RH vivantes. Une correction Teamworks ne transforme donc pas un replay
        # exact en nouvelle préparation.
        replayed = self._adapter.replay_prepare(command)
        if replayed is not None:
            return replayed
        if self._resolver is None:
            raise RuntimeError("DPAE_BUSINESS_RESOLVER_REQUIRED")
        business_data = self._resolver.resolve(command.contract_id)
        if business_data.contract_id != command.contract_id:
            raise ValueError("DPAE_RESOLVER_CONTRACT_MISMATCH")
        return self._adapter.prepare(command, business_data)

    def submit(self, command: SubmitDpae):
        durable = self._adapter.submit(command)
        if durable.get("replayed") or self._transport is None:
            return durable
        submission_id = durable["submission_id"]
        self._adapter.start_transmission(submission_id)
        try:
            result = self._transport.send(
                submission_id=submission_id,
                payload_hash=durable["payload_hash"],
            )
        except Exception:
            self._adapter.finish_transmission(
                submission_id,
                TransmissionResult("UNKNOWN", reason_code="TRANSPORT_EXCEPTION"),
            )
            raise
        self._adapter.finish_transmission(submission_id, result)
        durable["transmission_outcome"] = result.outcome
        durable["external_flux_id"] = result.external_flux_id
        return durable

    def ingest_return(self, command: IngestDpaeReturn):
        return self._adapter.ingest_return(command)

    def get_case(self, case_id: str):
        return self._adapter.get_case(case_id)
