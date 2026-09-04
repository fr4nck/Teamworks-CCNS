import sqlite3
from datetime import date

from domain.hr_connections import (
    EffectivePeriod,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    OrganizationKind,
)
from infrastructure.persistence.employee_protection_repository import (
    EMPLOYEE_PROTECTION_SCHEMA_VERSION,
    SqliteEmployeeProtectionRepository,
)


def _repo(tmp_path):
    return SqliteEmployeeProtectionRepository(tmp_path / "employee-protection.sqlite")


def _record(
    *,
    structure_ref="PMSL",
    record_id="MUT-001",
    employee_ref="42",
    status=EmployeeProtectionStatus.ACTIVE,
    ends_on=None,
    option_code="base",
):
    return EmployeeProtectionRecord.create(
        record_id=record_id,
        structure_ref=structure_ref,
        employee_ref=employee_ref,
        organization_code="unimutuelle",
        organization_kind=OrganizationKind.MUTUELLE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=status,
        effective_period=EffectivePeriod(
            starts_on=date(2026, 1, 1),
            ends_on=ends_on,
        ),
        scheme_code="collectif",
        option_code=option_code,
        contribution_profile_code="non_cadre",
        external_reference="ADH-42",
        document_ref="DOC-42",
        administrative_deadline=date(2026, 1, 15),
        source="fiche_salarie",
    )


def test_schema_is_idempotent_and_versioned(tmp_path):
    path = tmp_path / "employee-protection.sqlite"
    repo = SqliteEmployeeProtectionRepository(path)
    repo.ensure_schema()

    assert repo.schema_version() == EMPLOYEE_PROTECTION_SCHEMA_VERSION == 1
    with sqlite3.connect(path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tw_hr_%'"
            ).fetchall()
        }
    assert "tw_hr_employee_protection_schema" in tables
    assert "tw_hr_employee_protection" in tables


def test_round_trip_preserves_payroll_ready_metadata(tmp_path):
    repo = _repo(tmp_path)
    record = _record()

    repo.save_employee_protection(record)
    loaded = repo.get_employee_protection(structure_ref="PMSL", record_id="MUT-001")

    assert loaded == record
    assert loaded.scheme_code == "collectif"
    assert loaded.option_code == "base"
    assert loaded.contribution_profile_code == "non_cadre"


def test_save_updates_current_projection_without_duplicate_row(tmp_path):
    repo = _repo(tmp_path)
    repo.save_employee_protection(_record(option_code="base"))
    updated = _record(option_code="famille")

    repo.save_employee_protection(updated)

    assert repo.get_employee_protection(
        structure_ref="PMSL", record_id="MUT-001"
    ) == updated
    assert repo.list_employee_protection(
        structure_ref="PMSL", employee_ref="42"
    ) == (updated,)


def test_same_record_id_is_isolated_by_structure(tmp_path):
    repo = _repo(tmp_path)
    pmsl = _record(structure_ref="PMSL")
    other = _record(structure_ref="AUTRE")

    repo.save_employee_protection(pmsl)
    repo.save_employee_protection(other)

    assert repo.get_employee_protection(
        structure_ref="PMSL", record_id="MUT-001"
    ) == pmsl
    assert repo.get_employee_protection(
        structure_ref="AUTRE", record_id="MUT-001"
    ) == other


def test_list_is_isolated_by_employee(tmp_path):
    repo = _repo(tmp_path)
    first = _record(record_id="MUT-001", employee_ref="42")
    second = _record(record_id="MUT-002", employee_ref="84")
    repo.save_employee_protection(first)
    repo.save_employee_protection(second)

    assert repo.list_employee_protection(
        structure_ref="PMSL", employee_ref="42"
    ) == (first,)
    assert repo.list_employee_protection(
        structure_ref="PMSL", employee_ref="84"
    ) == (second,)


def test_ended_record_round_trip_preserves_effective_end(tmp_path):
    repo = _repo(tmp_path)
    record = _record(
        status=EmployeeProtectionStatus.ENDED,
        ends_on=date(2026, 8, 31),
    )

    repo.save_employee_protection(record)

    assert repo.get_employee_protection(
        structure_ref="PMSL", record_id="MUT-001"
    ) == record
