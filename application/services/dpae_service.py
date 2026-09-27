"""Façade applicative DPAE de Teamworks.

Aucun SQL ici : le service orchestre les cas d'usage et délègue les garanties
durables à l'adaptateur transactionnel.
"""
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


class DpaeService:
    """Unique façade d'écriture/lecture appelée par Teamworks."""

    def __init__(self, adapter):
        self._adapter = adapter

    def prepare(self, command: PrepareDpae):
        return self._adapter.prepare(command)

    def submit(self, command: SubmitDpae):
        return self._adapter.submit(command)

    def mark_sent(self, submission_id: str, external_flux_id: str):
        """Frontière transport interne ; ne doit pas être exposée à l'UI."""
        return self._adapter.mark_sent(submission_id, external_flux_id)

    def ingest_return(self, command: IngestDpaeReturn):
        return self._adapter.ingest_return(command)

    def get_case(self, case_id: str):
        return self._adapter.get_case(case_id)
