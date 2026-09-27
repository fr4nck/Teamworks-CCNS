"""Façade applicative DPAE de Teamworks."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PrepareDpae:
    command_id: str
    case_key: str
    employee_id: str
    contract_id: str
    establishment_id: str
    expected_hiring_at: object
    actor_id: str


@dataclass(frozen=True)
class SubmitDpae:
    command_id: str
    case_id: str
    payload_hash: str
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
    outcome: str  # SENT | REJECTED | UNKNOWN
    external_flux_id: Optional[str] = None
    reason_code: Optional[str] = None


class DpaeService:
    """Unique façade métier appelée par Teamworks.

    Le transport est un port injecté. Il ne connaît ni MariaDB ni les états du Case.
    """

    def __init__(self, adapter, transport=None):
        self._adapter = adapter
        self._transport = transport

    def prepare(self, command: PrepareDpae):
        return self._adapter.prepare(command)

    def submit(self, command: SubmitDpae):
        durable = self._adapter.submit(command)
        if durable.get("replayed") or self._transport is None:
            return durable
        submission_id = durable["submission_id"]
        self._adapter.start_transmission(submission_id)
        try:
            result = self._transport.send(submission_id=submission_id, payload_hash=command.payload_hash)
        except Exception:
            self._adapter.finish_transmission(submission_id, TransmissionResult("UNKNOWN", reason_code="TRANSPORT_EXCEPTION"))
            raise
        self._adapter.finish_transmission(submission_id, result)
        durable["transmission_outcome"] = result.outcome
        durable["external_flux_id"] = result.external_flux_id
        return durable

    def ingest_return(self, command: IngestDpaeReturn):
        return self._adapter.ingest_return(command)

    def get_case(self, case_id: str):
        return self._adapter.get_case(case_id)
