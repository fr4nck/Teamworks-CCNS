from datetime import date

import pytest

from application.services.hr_connections.employee_protection import EmployeeProtectionService
from application.services.hr_connections.employee_protection_actions import (
    EmployeeProtectionActionService,
    EmployeeProtectionCreateRequest,
)
from domain.hr_connections import (
    ConnectionProfile,
    EffectivePeriod,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    HrOrganization,
    OrganizationKind,
)


class FakeProfileRepository:
    def __init__(self, profiles=()):
        self._profiles = {
            (profile.structure_ref, profile.organization.code): profile for profile in profiles
        }

    def get_profile(self, *, structure_ref, organization_code):
        return self._profiles.get((structure_ref, organization_code))

    def remove(self, *, structure_ref, organization_code):
        self._profiles.pop((structure_ref, organization_code), None)


class AtomicFakeEmployeeProtectionRepository:
    def __init__(self):
        self._records = {}
        self.supersede_calls = 0

    def save_employee_protection(self, record):
        self._records[(record.structure_ref, record.record_id)] = record
        return record

    def get_employee_protection(self, *, structure_ref, record_id):
        return self._records.get((structure_ref, record_id))

    def list_employee_protection(self, *, structure_ref, employee_ref):
        return tuple(
            record
            for (ref, _), record in self._records.items()
            if ref == structure_ref and record.employee_ref == employee_ref
        )

    def supersede_employee_protection(self, *, ended_record, successor_record):
        self.supersede_calls += 1
        self._records[(ended_record.structure_ref, ended_record.record_id)] = ended_record
        self._records[(successor_record.structure_ref, successor_record.record_id)] = successor_record
        return ended_record, successor_record


def _profile(*, code, kind, label):
    return ConnectionProfile.create(
        structure_ref="structure-1",
        organization=HrOrganization.create(code=code, label=label, kind=kind),
    )


def _request(
    *,
    code,
    kind,
    starts_on,
    contribution_profile_code,
    status=EmployeeProtectionStatus.ACTIVE,
):
    return EmployeeProtectionCreateRequest(
        organization_code=code,
        organization_kind=kind,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=status,
        starts_on=starts_on,
        contribution_profile_code=contribution_profile_code,
        source="teamworks",
    )


def _actions(ids):
    repository = AtomicFakeEmployeeProtectionRepository()
    profiles = FakeProfileRepository(
        [
            _profile(
                code="mutuelle-a",
                kind=OrganizationKind.MUTUELLE,
                label="Mutuelle A",
            ),
            _profile(
                code="prevoyance-b",
                kind=OrganizationKind.PREVOYANCE,
                label="Prévoyance B",
            ),
        ]
    )
    service = EmployeeProtectionService(
        repository=repository,
        profile_repository=profiles,
    )
    iterator = iter(ids)
    actions = EmployeeProtectionActionService(
        protection_service=service,
        record_id_factory=lambda: next(iterator),
    )
    return actions, repository, profiles


def test_supersede_closes_previous_day_and_creates_new_historized_period():
    actions, repository, _profiles = _actions(["old-period", "new-period"])
    old = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-1",
        request=_request(
            code="mutuelle-a",
            kind=OrganizationKind.MUTUELLE,
            starts_on=date(2026, 1, 1),
            contribution_profile_code="NON_CADRE",
        ),
    ).record

    result = actions.supersede(
        structure_ref="structure-1",
        employee_ref="employee-1",
        record_id=old.record_id,
        request=_request(
            code="prevoyance-b",
            kind=OrganizationKind.PREVOYANCE,
            starts_on=date(2026, 10, 1),
            contribution_profile_code="CADRE",
        ),
    )

    assert repository.supersede_calls == 1
    assert result.previous.record.record_id == "old-period"
    assert result.previous.record.status is EmployeeProtectionStatus.ENDED
    assert result.previous.record.effective_period == EffectivePeriod(
        starts_on=date(2026, 1, 1),
        ends_on=date(2026, 9, 30),
    )
    assert result.previous.record.contribution_profile_code == "NON_CADRE"

    assert result.successor.record.record_id == "new-period"
    assert result.successor.record.status is EmployeeProtectionStatus.ACTIVE
    assert result.successor.record.effective_period.starts_on == date(2026, 10, 1)
    assert result.successor.record.organization_code == "prevoyance-b"
    assert result.successor.record.contribution_profile_code == "CADRE"


def test_supersede_can_close_history_even_if_previous_organization_profile_was_removed():
    actions, _repository, profiles = _actions(["old-period", "new-period"])
    old = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-1",
        request=_request(
            code="mutuelle-a",
            kind=OrganizationKind.MUTUELLE,
            starts_on=date(2026, 1, 1),
            contribution_profile_code="NON_CADRE",
        ),
    ).record
    profiles.remove(structure_ref="structure-1", organization_code="mutuelle-a")

    result = actions.supersede(
        structure_ref="structure-1",
        employee_ref="employee-1",
        record_id=old.record_id,
        request=_request(
            code="prevoyance-b",
            kind=OrganizationKind.PREVOYANCE,
            starts_on=date(2026, 10, 1),
            contribution_profile_code="CADRE",
        ),
    )

    assert not result.previous.organization_configured
    assert result.successor.organization_configured


def test_supersede_requires_active_successor_with_explicit_later_start():
    actions, repository, _profiles = _actions(["old-period", "new-period"])
    old = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-1",
        request=_request(
            code="mutuelle-a",
            kind=OrganizationKind.MUTUELLE,
            starts_on=date(2026, 9, 1),
            contribution_profile_code="NON_CADRE",
        ),
    ).record

    with pytest.raises(ValueError, match="statut actif"):
        actions.supersede(
            structure_ref="structure-1",
            employee_ref="employee-1",
            record_id=old.record_id,
            request=_request(
                code="prevoyance-b",
                kind=OrganizationKind.PREVOYANCE,
                starts_on=date(2026, 10, 1),
                contribution_profile_code="CADRE",
                status=EmployeeProtectionStatus.PENDING,
            ),
        )

    with pytest.raises(ValueError, match="après"):
        actions.supersede(
            structure_ref="structure-1",
            employee_ref="employee-1",
            record_id=old.record_id,
            request=_request(
                code="prevoyance-b",
                kind=OrganizationKind.PREVOYANCE,
                starts_on=date(2026, 9, 1),
                contribution_profile_code="CADRE",
            ),
        )

    assert repository.supersede_calls == 0


def test_supersede_does_not_extend_an_already_scheduled_end_date():
    actions, repository, _profiles = _actions(["old-period", "new-period"])
    old = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-1",
        request=EmployeeProtectionCreateRequest(
            organization_code="mutuelle-a",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
            status=EmployeeProtectionStatus.ACTIVE,
            starts_on=date(2026, 9, 1),
            ends_on=date(2026, 9, 30),
            contribution_profile_code="NON_CADRE",
        ),
    ).record

    with pytest.raises(ValueError, match="prolonger"):
        actions.supersede(
            structure_ref="structure-1",
            employee_ref="employee-1",
            record_id=old.record_id,
            request=_request(
                code="prevoyance-b",
                kind=OrganizationKind.PREVOYANCE,
                starts_on=date(2026, 10, 2),
                contribution_profile_code="CADRE",
            ),
        )

    assert repository.supersede_calls == 0
