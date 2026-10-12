from datetime import date

from application.services.hr_connections.employee_protection import EmployeeProtectionService
from application.services.hr_connections.employee_protection_summary import (
    EmployeeProtectionSummaryService,
)
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


class FakeEmployeeRepository:
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


def _profile(*, code, label, kind):
    return ConnectionProfile.create(
        structure_ref="PMSL",
        organization=HrOrganization.create(code=code, label=label, kind=kind),
    )


def _record(
    *,
    record_id,
    organization_code,
    organization_kind,
    relation_kind,
    status,
    start=None,
    end=None,
    deadline=None,
):
    return EmployeeProtectionRecord.create(
        record_id=record_id,
        structure_ref="PMSL",
        employee_ref="42",
        organization_code=organization_code,
        organization_kind=organization_kind,
        relation_kind=relation_kind,
        status=status,
        effective_period=EffectivePeriod(starts_on=start, ends_on=end),
        administrative_deadline=deadline,
        contribution_profile_code=(
            "non_cadre"
            if organization_kind
            in {
                OrganizationKind.MUTUELLE,
                OrganizationKind.PREVOYANCE,
                OrganizationKind.RETRAITE_COMPLEMENTAIRE,
            }
            else None
        ),
    )


def test_summary_counts_descriptive_attention_and_payroll_items():
    profiles = FakeProfileRepository(
        [
            _profile(
                code="unimutuelle",
                label="Unimutuelle",
                kind=OrganizationKind.MUTUELLE,
            ),
            _profile(code="pst35", label="PST 35", kind=OrganizationKind.SPST),
        ]
    )
    repository = FakeEmployeeRepository()
    service = EmployeeProtectionService(
        repository=repository,
        profile_repository=profiles,
    )
    service.save(
        _record(
            record_id="mut-1",
            organization_code="unimutuelle",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
            status=EmployeeProtectionStatus.ACTIVE,
            start=date(2026, 1, 1),
        )
    )
    service.save(
        _record(
            record_id="spst-1",
            organization_code="pst35",
            organization_kind=OrganizationKind.SPST,
            relation_kind=EmployeeProtectionRelationKind.MONITORING,
            status=EmployeeProtectionStatus.PENDING,
            deadline=date(2026, 8, 31),
        )
    )

    summary = EmployeeProtectionSummaryService(
        protection_service=service
    ).build(
        structure_ref="PMSL",
        employee_ref="42",
        as_of=date(2026, 9, 1),
    )

    assert summary.total_count == 2
    assert summary.effective_count == 1
    assert summary.pending_count == 1
    assert summary.due_count == 1
    assert summary.payroll_relevant_count == 1
    assert summary.orphan_configuration_count == 0
    assert summary.has_attention_items
    assert [row.record_id for row in summary.rows] == ["mut-1", "spst-1"]
    assert summary.rows[0].payroll_relevant
    assert not summary.rows[0].due
    assert not summary.rows[1].payroll_relevant
    assert summary.rows[1].due


def test_summary_flags_removed_organization_without_losing_history():
    profiles = FakeProfileRepository(
        [
            _profile(
                code="unimutuelle",
                label="Unimutuelle",
                kind=OrganizationKind.MUTUELLE,
            )
        ]
    )
    repository = FakeEmployeeRepository()
    service = EmployeeProtectionService(
        repository=repository,
        profile_repository=profiles,
    )
    service.save(
        _record(
            record_id="mut-1",
            organization_code="unimutuelle",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
            status=EmployeeProtectionStatus.ACTIVE,
            start=date(2026, 1, 1),
        )
    )
    profiles.remove(structure_ref="PMSL", organization_code="unimutuelle")

    summary = EmployeeProtectionSummaryService(
        protection_service=service
    ).build(
        structure_ref="PMSL",
        employee_ref="42",
        as_of=date(2026, 9, 1),
    )

    assert summary.orphan_configuration_count == 1
    assert summary.rows[0].organization_label is None
    assert not summary.rows[0].organization_configured
    assert summary.has_attention_items


def test_summary_does_not_mark_ended_non_effective_record_as_payroll_relevant_now():
    profiles = FakeProfileRepository(
        [
            _profile(
                code="unimutuelle",
                label="Unimutuelle",
                kind=OrganizationKind.MUTUELLE,
            )
        ]
    )
    repository = FakeEmployeeRepository()
    service = EmployeeProtectionService(
        repository=repository,
        profile_repository=profiles,
    )
    service.save(
        _record(
            record_id="mut-old",
            organization_code="unimutuelle",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
            status=EmployeeProtectionStatus.ENDED,
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
        )
    )

    summary = EmployeeProtectionSummaryService(
        protection_service=service
    ).build(
        structure_ref="PMSL",
        employee_ref="42",
        as_of=date(2026, 9, 1),
    )

    assert summary.total_count == 1
    assert summary.effective_count == 0
    assert summary.payroll_relevant_count == 0
    assert not summary.has_attention_items
