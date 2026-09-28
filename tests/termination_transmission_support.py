"""Aides de test SORTIE-003 : franchir PRET -> TRANSMIS par la seule voie légitime."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from domain.employment.termination import CheckState, ContractTermination, TerminationWorkflowStatus
from domain.employment.termination_transmission import (
    HR_CATEGORIES,
    CommunicatedHrItem,
    TransmissionChannel,
    TransmitTermination,
    create_transmission_snapshot,
)

RECORDED_AT = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)
TRANSMITTED_AT = datetime(2026, 11, 3, 9, 30, tzinfo=timezone.utc)


def hr_items_for(termination: ContractTermination, label: str = "détail communiqué") -> tuple:
    """Un élément décrit par catégorie PROVIDED ; aucun pour NONE."""
    return tuple(
        CommunicatedHrItem(category, "%s — %s" % (label, category))
        for category in HR_CATEGORIES
        if getattr(termination.hr_checks, category) is CheckState.PROVIDED
    )


def transmit_in_memory(termination: ContractTermination):
    """Transmission V1 purement domaine (sans base)."""
    if termination.workflow_status is TerminationWorkflowStatus.A_PREPARER:
        termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    snapshot = create_transmission_snapshot(
        termination,
        previous=None,
        hr_items=hr_items_for(termination),
        created_at=RECORDED_AT,
        created_by="director-1",
        transmitted_at=TRANSMITTED_AT,
        transmitted_by="director-1",
        channel=TransmissionChannel.EMAIL,
    )
    termination.record_first_transmission(snapshot)
    return snapshot


def transmit_command(termination: ContractTermination, *, command_id=None, **overrides) -> TransmitTermination:
    values = dict(
        command_id=command_id or "cmd-" + uuid4().hex,
        termination_id=termination.termination_id,
        expected_version=termination.version,
        actor_id="director-1",
        transmitted_at=TRANSMITTED_AT,
        transmitted_by="director-1",
        channel=TransmissionChannel.EMAIL,
        hr_items=hr_items_for(termination),
    )
    values.update(overrides)
    return TransmitTermination(**values)


def fixed_clock():
    return RECORDED_AT
