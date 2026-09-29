"""Façade applicative DPAE de Teamworks.

DATA-001 : l'appelant fournit la référence contrat. Les valeurs RH déclarables
sont résolues par un port read-only avant d'être figées par la persistance DPAE.
"""
from dataclasses import dataclass
from typing import Optional, Protocol

from application.services.dpae_errors import DpaeConfigurationError, DpaeDataError


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
class RetryDpaeSubmission:
    """Retry purement technique d'une tentative durable, sans résolution RH."""
    submission_id: str


@dataclass(frozen=True)
class RecoverInterruptedDpaeSubmission:
    """Matérialise l'issue inconnue d'une tentative restée durablement SENDING."""
    submission_id: str


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
        replayed = self._adapter.replay_prepare(command)
        if replayed is not None:
            return replayed
        if self._resolver is None:
            raise DpaeConfigurationError(
                "DPAE_BUSINESS_RESOLVER_REQUIRED",
                entity_type="contract",
                entity_id=command.contract_id,
            )
        business_data = self._resolver.resolve(command.contract_id)
        if business_data.contract_id != command.contract_id:
            raise DpaeDataError(
                "DPAE_RESOLVER_CONTRACT_MISMATCH",
                field="contract_id",
                entity_type="contract",
                entity_id=command.contract_id,
            )
        return self._adapter.prepare(command, business_data)

    def _send_durable(self, durable):
        if self._transport is None:
            return durable
        submission_id = durable["submission_id"]
        try:
            result = self._transport.send(
                submission_id=submission_id,
                payload_hash=durable["payload_hash"],
                canonical_payload=durable["canonical_payload"],
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

    def submit(self, command: SubmitDpae):
        durable = self._adapter.submit(command)
        if durable.get("replayed") or self._transport is None:
            return durable
        self._adapter.start_transmission(durable["submission_id"])
        return self._send_durable(durable)

    def recover_interrupted_submission(self, command: RecoverInterruptedDpaeSubmission):
        """Récupère un SENDING abandonné sans transport ni relecture Teamworks."""
        return self._adapter.recover_interrupted_submission(command.submission_id)

    def retry_submission(self, command: RetryDpaeSubmission):
        """Reprend la même Submission et son snapshot ; ne consulte jamais le resolver."""
        durable = self._adapter.retry_submission(command.submission_id)
        return self._send_durable(durable)

    def ingest_return(self, command: IngestDpaeReturn):
        return self._adapter.ingest_return(command)

    def get_case(self, case_id: str):
        return self._adapter.get_case(case_id)
