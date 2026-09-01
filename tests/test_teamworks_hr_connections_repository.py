import sqlite3
from datetime import date
from pathlib import Path

from application.services.hr_connections import EmployeeProtectionService
from application.services.hr_connections.employee_protection_summary import (
    EmployeeProtectionSummaryService,
)
from domain.hr_connections import (
    ConnectionProfile,
    ConnectorCapability,
    EffectivePeriod,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TEAMWORKS_HR_SCHEMA_VERSION,
    TeamworksHrConnectionsRepository,
    _adapt_placeholders,
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


class NetworkMarker:
    isNetwork = True


def _repository(tmp_path):
    path = tmp_path / "teamworks-data.sqlite"
    return (
        TeamworksHrConnectionsRepository(
            db_factory=lambda: LocalGestionDb(path),
        ),
        path,
    )


def _mutuelle_profile(structure_ref="PMSL"):
    return ConnectionProfile.create(
        structure_ref=structure_ref,
        organization=HrOrganization.create(
            code="unimutuelle",
            label="Unimutuelle",
            kind=OrganizationKind.MUTUELLE,
        ),
        capabilities=(
            ConnectorCapability.DEEP_LINK,
            ConnectorCapability.MANUAL_STATUS,
        ),
        references=(
            OrganizationReference.create(
                reference_type="contract_number",
                value="CTR-2026",
                label="Contrat collectif",
            ),
        ),
        portal_links=(
            PortalLink.create(
                url="https://example.org/employeur",
                label="Portail employeur",
            ),
        ),
        effective_period=EffectivePeriod(starts_on=date(2026, 1, 1)),
    )


def _protection_record(
    *,
    record_id="mutuelle-employee-42",
    employee_ref="42",
    status=EmployeeProtectionStatus.ACTIVE,
):
    return EmployeeProtectionRecord.create(
        record_id=record_id,
        structure_ref="PMSL",
        employee_ref=employee_ref,
        organization_code="unimutuelle",
        organization_kind=OrganizationKind.MUTUELLE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=status,
        effective_period=EffectivePeriod(starts_on=date(2026, 9, 1)),
        scheme_code="BASE",
        option_code="FAMILLE",
        contribution_profile_code="NON_CADRE",
        external_reference="AFF-42",
        document_ref="doc:mutuelle-42",
        administrative_deadline=date(2026, 9, 10),
        source="embauche",
    )


def test_teamworks_hr_schema_is_additive_versioned_and_indexed(tmp_path):
    repository, path = _repository(tmp_path)

    assert repository.schema_version() == TEAMWORKS_HR_SCHEMA_VERSION == 1

    with sqlite3.connect(path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tw_hr_%'"
            ).fetchall()
        }
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_tw_hr_%'"
            ).fetchall()
        }

    assert {
        "tw_hr_schema_versions",
        "tw_hr_connection_profiles",
        "tw_hr_connection_capabilities",
        "tw_hr_organization_references",
        "tw_hr_portal_links",
        "tw_hr_employee_protection",
    }.issubset(tables)
    assert "idx_tw_hr_employee_protection_employee" in indexes
    assert "idx_tw_hr_employee_protection_deadline" in indexes


def test_connection_profile_round_trip_and_update_use_teamworks_store(tmp_path):
    repository, _path = _repository(tmp_path)
    profile = _mutuelle_profile()

    assert repository.save_profile(profile) == profile
    assert repository.get_profile(
        structure_ref="PMSL",
        organization_code="unimutuelle",
    ) == profile

    updated = ConnectionProfile.create(
        structure_ref="PMSL",
        organization=HrOrganization.create(
            code="unimutuelle",
            label="Unimutuelle 2027",
            kind=OrganizationKind.MUTUELLE,
        ),
        capabilities=(ConnectorCapability.DEEP_LINK,),
        references=(
            OrganizationReference.create(
                reference_type="contract_number",
                value="CTR-2027",
            ),
        ),
        portal_links=(
            PortalLink.create(
                url="https://example.org/nouveau",
                label="Nouveau portail",
            ),
        ),
        effective_period=EffectivePeriod(starts_on=date(2027, 1, 1)),
    )
    repository.save_profile(updated)

    assert repository.list_profiles(structure_ref="PMSL") == (updated,)


def test_employee_protection_round_trip_update_and_structure_isolation(tmp_path):
    repository, _path = _repository(tmp_path)
    record = _protection_record()

    repository.save_employee_protection(record)
    assert repository.get_employee_protection(
        structure_ref="PMSL",
        record_id=record.record_id,
    ) == record

    ended = EmployeeProtectionRecord.create(
        record_id=record.record_id,
        structure_ref=record.structure_ref,
        employee_ref=record.employee_ref,
        organization_code=record.organization_code,
        organization_kind=record.organization_kind,
        relation_kind=record.relation_kind,
        status=EmployeeProtectionStatus.ENDED,
        effective_period=EffectivePeriod(
            starts_on=date(2026, 9, 1),
            ends_on=date(2027, 8, 31),
        ),
        scheme_code=record.scheme_code,
        option_code=record.option_code,
        contribution_profile_code=record.contribution_profile_code,
        external_reference=record.external_reference,
        document_ref=record.document_ref,
        source="radiation",
    )
    repository.save_employee_protection(ended)

    assert repository.list_employee_protection(
        structure_ref="PMSL",
        employee_ref="42",
    ) == (ended,)
    assert repository.list_employee_protection(
        structure_ref="AUTRE",
        employee_ref="42",
    ) == ()


def test_production_repository_runs_employee_service_and_summary_end_to_end(tmp_path):
    repository, _path = _repository(tmp_path)
    repository.save_profile(_mutuelle_profile())

    employee_service = EmployeeProtectionService(
        repository=repository,
        profile_repository=repository,
    )
    saved = employee_service.save(_protection_record())

    assert saved.organization_configured
    assert saved.payroll_relevant

    summary = EmployeeProtectionSummaryService(
        protection_service=employee_service,
    ).build(
        structure_ref="PMSL",
        employee_ref="42",
        as_of=date(2026, 9, 1),
    )

    assert summary.total_count == 1
    assert summary.effective_count == 1
    assert summary.payroll_relevant_count == 1
    assert summary.orphan_configuration_count == 0


def test_sql_placeholder_adapter_preserves_sqlite_and_mysql_historical_contracts():
    local = type("LocalMarker", (), {"isNetwork": False})()

    assert _adapt_placeholders(local, "a = ? AND b = ?") == "a = ? AND b = ?"
    assert (
        _adapt_placeholders(NetworkMarker(), "a = ? AND b = ?")
        == "a = %s AND b = %s"
    )


def test_production_repository_source_avoids_sqlite_only_upserts_and_historical_foreign_keys():
    source = Path(
        "infrastructure/persistence/teamworks_hr_connections_repository.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "on conflict",
        "insert or ignore",
        "replace into",
        "pragma ",
        "foreign key",
        "references personnes",
        "references contrats",
        "import wx",
        "requests",
        "webbrowser",
    ):
        assert forbidden not in lowered

    assert "GestionDB" in source
    assert "isNetwork" in source
    assert "CREATE TABLE IF NOT EXISTS" in source
