import sqlite3
from dataclasses import replace
from datetime import date

import pytest

from domain.hr_connections import (
    EffectivePeriod,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    OrganizationKind,
)
from infrastructure.persistence.teamworks_employee_protection_succession_repository import (
    TeamworksEmployeeProtectionSuccessionRepository,
)


class LocalGestionDb:
    def __init__(self, path):
        self.isNetwork = False
        self.connexion = sqlite3.connect(path)
        self.cursor = self.connexion.cursor()

    def Commit(self):
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


def _factory(path):
    return lambda: LocalGestionDb(path)


def _active(*, record_id, employee_ref="42", starts_on=date(2026, 1, 1)):
    return EmployeeProtectionRecord.create(
        record_id=record_id,
        structure_ref="structure-1",
        employee_ref=employee_ref,
        organization_code="mutuelle-demo",
        organization_kind=OrganizationKind.MUTUELLE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=EmployeeProtectionStatus.ACTIVE,
        effective_period=EffectivePeriod(starts_on=starts_on),
        contribution_profile_code="NON_CADRE",
        source="teamworks",
    )


def _ended(record, *, ends_on):
    return replace(
        record,
        status=EmployeeProtectionStatus.ENDED,
        effective_period=EffectivePeriod(
            starts_on=record.effective_period.starts_on,
            ends_on=ends_on,
        ),
    )


def _successor(*, record_id, employee_ref="42", starts_on=date(2026, 10, 1)):
    return EmployeeProtectionRecord.create(
        record_id=record_id,
        structure_ref="structure-1",
        employee_ref=employee_ref,
        organization_code="prevoyance-demo",
        organization_kind=OrganizationKind.PREVOYANCE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=EmployeeProtectionStatus.ACTIVE,
        effective_period=EffectivePeriod(starts_on=starts_on),
        contribution_profile_code="CADRE",
        source="teamworks",
    )


def test_teamworks_succession_commits_both_periods_in_one_unit_of_work(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    repository = TeamworksEmployeeProtectionSuccessionRepository(
        db_factory=_factory(path)
    )
    current = _active(record_id="old")
    repository.save_employee_protection(current)

    ended = _ended(current, ends_on=date(2026, 9, 30))
    successor = _successor(record_id="new")
    saved_ended, saved_successor = repository.supersede_employee_protection(
        ended_record=ended,
        successor_record=successor,
    )

    assert saved_ended == ended
    assert saved_successor == successor
    assert repository.get_employee_protection(
        structure_ref="structure-1",
        record_id="old",
    ) == ended
    assert repository.get_employee_protection(
        structure_ref="structure-1",
        record_id="new",
    ) == successor


def test_teamworks_succession_rolls_back_previous_closure_if_successor_insert_fails(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    repository = TeamworksEmployeeProtectionSuccessionRepository(
        db_factory=_factory(path)
    )
    current = _active(record_id="old")
    repository.save_employee_protection(current)
    collision = _active(record_id="new", employee_ref="other")
    repository.save_employee_protection(collision)

    with pytest.raises(sqlite3.IntegrityError):
        repository.supersede_employee_protection(
            ended_record=_ended(current, ends_on=date(2026, 9, 30)),
            successor_record=_successor(record_id="new"),
        )

    persisted_current = repository.get_employee_protection(
        structure_ref="structure-1",
        record_id="old",
    )
    persisted_collision = repository.get_employee_protection(
        structure_ref="structure-1",
        record_id="new",
    )
    assert persisted_current == current
    assert persisted_current.status is EmployeeProtectionStatus.ACTIVE
    assert persisted_current.effective_period.ends_on is None
    assert persisted_collision == collision


def test_teamworks_succession_rejects_stale_predecessor_metadata(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    repository = TeamworksEmployeeProtectionSuccessionRepository(
        db_factory=_factory(path)
    )
    current = _active(record_id="old")
    repository.save_employee_protection(current)
    stale = replace(
        _ended(current, ends_on=date(2026, 9, 30)),
        contribution_profile_code="STALE",
    )

    with pytest.raises(RuntimeError, match="changé"):
        repository.supersede_employee_protection(
            ended_record=stale,
            successor_record=_successor(record_id="new"),
        )

    assert repository.get_employee_protection(
        structure_ref="structure-1",
        record_id="old",
    ) == current


def test_teamworks_succession_uses_existing_schema_without_destructive_migration(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    repository = TeamworksEmployeeProtectionSuccessionRepository(
        db_factory=_factory(path)
    )

    with sqlite3.connect(path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "tw_hr_employee_protection" in tables
    assert "tw_hr_schema_versions" in tables
    assert not any("succession" in table for table in tables)
