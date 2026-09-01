from datetime import date

import pytest

from application.services.hr_connections.employee_protection import EmployeeProtectionService
from domain.hr_connections import (
    ConnectionProfile,
    EffectivePeriod,
    EmployeeProtectionRecord,
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

    def save_profile(self, profile):
        self._profiles[(profile.structure_ref, profile.organization.code)] = profile
        return profile

    def get_profile(self, *, structure_ref, organization_code):
        return self._profiles.get((structure_ref, organization_code))

    def list_profiles(self, *, structure_ref):
        return tuple(
            profile
            for (ref, _), profile in self._profiles.items()
            if ref == structure_ref
        )

    def remove(self, *, structure_ref, organization_code):
        self._profiles.pop((structure_ref, organization_code), None)


class FakeEmployeeProtectionRepository:
    def __init__(self):
        self._records = {}

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


def _profile(kind=OrganizationKind.MUTUELLE, code="unimutuelle", label="Unimutuelle"):
    return ConnectionProfile.create(
        structure_ref="structure-1",
        organization=HrOrganization.create(code=code, label=label, kind=kind),
    )


def _record(
    *,
    record_id="record-1",
    kind=OrganizationKind.MUTUELLE,
    code="unimutuelle",
    relation=EmployeeProtectionRelationKind.AFFILIATION,
    status=EmployeeProtectionStatus.ACTIVE,
    starts_on=date(2026, 1, 1),
    deadline=None,
):
    return EmployeeProtectionRecord.create(
        record_id=record_id,
        structure_ref="structure-1",
        employee_ref="employee-1",
        organization_code=code,
        organization_kind=kind,
        relation_kind=relation,
        status=status,
        effective_period=EffectivePeriod(starts_on=starts_on),
        administrative_deadline=deadline,
    )


def test_save_requires_configured_organization_and_returns_labeled_view():
    repository = FakeEmployeeProtectionRepository()
    profiles = FakeProfileRepository([_profile()])
    service = EmployeeProtectionService(repository=repository, profile_repository=profiles)

    view = service.save(_record())

    assert view.organization_configured
    assert view.organization_label == "Unimutuelle"
    assert view.payroll_relevant


def test_save_rejects_orphan_organization():
    service = EmployeeProtectionService(
        repository=FakeEmployeeProtectionRepository(),
        profile_repository=FakeProfileRepository(),
    )

    with pytest.raises(ValueError, match="configuré"):
        service.save(_record())


def test_save_rejects_organization_kind_mismatch():
    service = EmployeeProtectionService(
        repository=FakeEmployeeProtectionRepository(),
        profile_repository=FakeProfileRepository(
            [_profile(kind=OrganizationKind.PREVOYANCE, code="unimutuelle")]
        ),
    )

    with pytest.raises(ValueError, match="ne correspond pas"):
        service.save(_record())


def test_history_remains_readable_after_profile_removal():
    repository = FakeEmployeeProtectionRepository()
    profiles = FakeProfileRepository([_profile()])
    service = EmployeeProtectionService(repository=repository, profile_repository=profiles)
    saved = service.save(_record()).record

    profiles.remove(structure_ref="structure-1", organization_code="unimutuelle")
    view = service.get(structure_ref="structure-1", record_id=saved.record_id)

    assert view is not None
    assert not view.organization_configured
    assert view.organization_label is None
    assert view.record == saved


def test_payroll_relevant_filter_excludes_spst_but_keeps_mutuelle():
    repository = FakeEmployeeProtectionRepository()
    profiles = FakeProfileRepository(
        [
            _profile(),
            _profile(kind=OrganizationKind.SPST, code="pst35", label="PST 35"),
        ]
    )
    service = EmployeeProtectionService(repository=repository, profile_repository=profiles)
    service.save(_record())
    service.save(
        _record(
            record_id="spst-1",
            kind=OrganizationKind.SPST,
            code="pst35",
            relation=EmployeeProtectionRelationKind.MONITORING,
        )
    )

    views = service.payroll_relevant_on(
        structure_ref="structure-1",
        employee_ref="employee-1",
        as_of=date(2026, 9, 1),
    )

    assert [view.record.record_id for view in views] == ["record-1"]


def test_due_filter_keeps_pending_administrative_deadlines():
    repository = FakeEmployeeProtectionRepository()
    profiles = FakeProfileRepository(
        [_profile(kind=OrganizationKind.SPST, code="pst35", label="PST 35")]
    )
    service = EmployeeProtectionService(repository=repository, profile_repository=profiles)
    service.save(
        _record(
            record_id="spst-due",
            kind=OrganizationKind.SPST,
            code="pst35",
            relation=EmployeeProtectionRelationKind.MONITORING,
            status=EmployeeProtectionStatus.PENDING,
            starts_on=None,
            deadline=date(2026, 9, 15),
        )
    )

    assert service.due_on_or_before(
        structure_ref="structure-1",
        employee_ref="employee-1",
        as_of=date(2026, 9, 14),
    ) == ()
    assert [
        view.record.record_id
        for view in service.due_on_or_before(
            structure_ref="structure-1",
            employee_ref="employee-1",
            as_of=date(2026, 9, 15),
        )
    ] == ["spst-due"]
