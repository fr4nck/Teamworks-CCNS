from datetime import date
from pathlib import Path

import pytest

from application.services.hr_connections.employee_protection import EmployeeProtectionService
from application.services.hr_connections.employee_protection_actions import (
    EmployeeProtectionActionService,
    EmployeeProtectionCreateRequest,
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

    def supersede_employee_protection(self, *, ended_record, successor_record):
        self._records[(ended_record.structure_ref, ended_record.record_id)] = ended_record
        self._records[(successor_record.structure_ref, successor_record.record_id)] = successor_record
        return ended_record, successor_record


def _profile(kind=OrganizationKind.MUTUELLE, code="mutuelle-demo"):
    return ConnectionProfile.create(
        structure_ref="structure-1",
        organization=HrOrganization.create(
            code=code,
            label="Organisme Démo",
            kind=kind,
        ),
    )


def _request(
    *,
    kind=OrganizationKind.MUTUELLE,
    code="mutuelle-demo",
    relation=EmployeeProtectionRelationKind.AFFILIATION,
    status=EmployeeProtectionStatus.ACTIVE,
    starts_on=date(2026, 9, 1),
    ends_on=None,
    waiver_reason_code=None,
):
    return EmployeeProtectionCreateRequest(
        organization_code=code,
        organization_kind=kind,
        relation_kind=relation,
        status=status,
        starts_on=starts_on,
        ends_on=ends_on,
        contribution_profile_code="NON_CADRE",
        waiver_reason_code=waiver_reason_code,
        source="teamworks",
    )


def _service(*, profiles=None, record_id="generated-1"):
    repository = FakeEmployeeProtectionRepository()
    profile_repository = FakeProfileRepository(
        profiles if profiles is not None else [_profile()]
    )
    protection_service = EmployeeProtectionService(
        repository=repository,
        profile_repository=profile_repository,
    )
    actions = EmployeeProtectionActionService(
        protection_service=protection_service,
        record_id_factory=lambda: record_id,
    )
    return actions, protection_service, repository


def test_register_generates_opaque_record_id_and_keeps_ui_away_from_structure_key():
    actions, _service_instance, repository = _service(record_id="record-created")

    view = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-42",
        request=_request(),
    )

    assert view.record.record_id == "record-created"
    assert view.record.structure_ref == "structure-1"
    assert view.record.employee_ref == "employee-42"
    assert view.record.contribution_profile_code == "NON_CADRE"
    assert repository.get_employee_protection(
        structure_ref="structure-1",
        record_id="record-created",
    ) == view.record


def test_register_refuses_generated_identifier_collision_instead_of_overwriting_history():
    actions, protection_service, repository = _service(record_id="same-id")
    existing = EmployeeProtectionRecord.create(
        record_id="same-id",
        structure_ref="structure-1",
        employee_ref="employee-existing",
        organization_code="mutuelle-demo",
        organization_kind=OrganizationKind.MUTUELLE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=EmployeeProtectionStatus.ACTIVE,
        effective_period=EffectivePeriod(starts_on=date(2026, 1, 1)),
    )
    protection_service.save(existing)

    with pytest.raises(RuntimeError, match="Collision"):
        actions.register(
            structure_ref="structure-1",
            employee_ref="employee-new",
            request=_request(),
        )

    assert repository.get_employee_protection(
        structure_ref="structure-1",
        record_id="same-id",
    ) == existing


def test_register_still_requires_configured_organization():
    actions, _service_instance, _repository = _service(profiles=[], record_id="record-1")

    with pytest.raises(ValueError, match="configuré"):
        actions.register(
            structure_ref="structure-1",
            employee_ref="employee-1",
            request=_request(),
        )


def test_register_waiver_keeps_domain_requirement_for_coded_reason():
    actions, _service_instance, _repository = _service(record_id="waiver-1")

    with pytest.raises(ValueError, match="motif codifié"):
        actions.register(
            structure_ref="structure-1",
            employee_ref="employee-1",
            request=_request(
                relation=EmployeeProtectionRelationKind.WAIVER,
                waiver_reason_code=None,
            ),
        )


def test_end_closes_active_period_without_changing_business_metadata():
    actions, _service_instance, _repository = _service(record_id="active-1")
    created = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-1",
        request=_request(),
    ).record

    ended = actions.end(
        structure_ref="structure-1",
        employee_ref="employee-1",
        record_id=created.record_id,
        ends_on=date(2026, 12, 31),
    ).record

    assert ended.record_id == created.record_id
    assert ended.status is EmployeeProtectionStatus.ENDED
    assert ended.effective_period == EffectivePeriod(
        starts_on=date(2026, 9, 1),
        ends_on=date(2026, 12, 31),
    )
    assert ended.organization_code == created.organization_code
    assert ended.relation_kind == created.relation_kind
    assert ended.contribution_profile_code == created.contribution_profile_code
    assert ended.source == created.source


def test_end_refuses_a_pending_record_instead_of_turning_it_into_history():
    actions, _service_instance, _repository = _service(record_id="pending-1")
    created = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-1",
        request=_request(
            status=EmployeeProtectionStatus.PENDING,
            starts_on=None,
        ),
    ).record

    with pytest.raises(ValueError, match="actif"):
        actions.end(
            structure_ref="structure-1",
            employee_ref="employee-1",
            record_id=created.record_id,
            ends_on=date(2026, 12, 31),
        )


def test_end_refuses_cross_employee_mutation():
    actions, _service_instance, _repository = _service(record_id="active-1")
    created = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-1",
        request=_request(),
    ).record

    with pytest.raises(ValueError, match="n'appartient pas"):
        actions.end(
            structure_ref="structure-1",
            employee_ref="employee-2",
            record_id=created.record_id,
            ends_on=date(2026, 12, 31),
        )


def test_end_refuses_date_before_effective_start():
    actions, _service_instance, _repository = _service(record_id="active-1")
    created = actions.register(
        structure_ref="structure-1",
        employee_ref="employee-1",
        request=_request(),
    ).record

    with pytest.raises(ValueError, match="précéder"):
        actions.end(
            structure_ref="structure-1",
            employee_ref="employee-1",
            record_id=created.record_id,
            ends_on=date(2026, 8, 31),
        )


def test_action_service_exposes_no_free_form_edit_or_delete_operation():
    public_names = {
        name
        for name in dir(EmployeeProtectionActionService)
        if not name.startswith("_")
    }

    assert public_names == {"end", "register", "supersede"}

    source = Path(
        "application/services/hr_connections/employee_protection_actions.py"
    ).read_text(encoding="utf-8")
    for token in (
        "import wx",
        "webbrowser",
        "requests",
        "DELETE FROM",
        "UPDATE tw_hr_",
    ):
        assert token not in source
