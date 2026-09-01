from datetime import date

import pytest

from domain.hr_connections.employee_protection import (
    EmployeeProtectionPortfolio,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
)
from domain.hr_connections.organizations import EffectivePeriod, OrganizationKind


def test_mutuelle_affiliation_keeps_payroll_ready_metadata():
    record = EmployeeProtectionRecord.create(
        record_id="mutuelle-2026",
        structure_ref="structure-1",
        employee_ref="employee-1",
        organization_code="unimutuelle",
        organization_kind=OrganizationKind.MUTUELLE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=EmployeeProtectionStatus.ACTIVE,
        effective_period=EffectivePeriod(starts_on=date(2026, 1, 1)),
        scheme_code="base",
        option_code="famille",
        contribution_profile_code="non_cadre",
        external_reference="adh-123",
        document_ref="doc-affiliation-1",
        source="fiche_salarie",
    )

    assert record.is_effective_on(as_of=date(2026, 9, 1))
    assert record.scheme_code == "base"
    assert record.option_code == "famille"
    assert record.contribution_profile_code == "non_cadre"
    assert record.external_reference == "adh-123"
    assert record.document_ref == "doc-affiliation-1"


def test_effective_record_requires_start_date():
    with pytest.raises(ValueError, match="date de début"):
        EmployeeProtectionRecord.create(
            record_id="prevoyance-1",
            structure_ref="structure-1",
            employee_ref="employee-1",
            organization_code="chorum",
            organization_kind=OrganizationKind.PREVOYANCE,
            relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
            status=EmployeeProtectionStatus.ACTIVE,
        )


def test_ended_record_requires_end_date():
    with pytest.raises(ValueError, match="date de fin"):
        EmployeeProtectionRecord.create(
            record_id="retraite-1",
            structure_ref="structure-1",
            employee_ref="employee-1",
            organization_code="agirc-arrco",
            organization_kind=OrganizationKind.RETRAITE_COMPLEMENTAIRE,
            relation_kind=EmployeeProtectionRelationKind.REGISTRATION,
            status=EmployeeProtectionStatus.ENDED,
            effective_period=EffectivePeriod(starts_on=date(2025, 1, 1)),
        )


def test_waiver_is_explicit_and_requires_a_coded_reason():
    with pytest.raises(ValueError, match="motif codifié"):
        EmployeeProtectionRecord.create(
            record_id="dispense-1",
            structure_ref="structure-1",
            employee_ref="employee-1",
            organization_code="unimutuelle",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.WAIVER,
        )

    record = EmployeeProtectionRecord.create(
        record_id="dispense-2",
        structure_ref="structure-1",
        employee_ref="employee-1",
        organization_code="unimutuelle",
        organization_kind=OrganizationKind.MUTUELLE,
        relation_kind=EmployeeProtectionRelationKind.WAIVER,
        status=EmployeeProtectionStatus.ACTIVE,
        effective_period=EffectivePeriod(starts_on=date(2026, 9, 1)),
        waiver_reason_code="couverture_collective_conjoint",
        document_ref="justificatif-dispense-2026",
    )

    assert record.waiver_reason_code == "couverture_collective_conjoint"
    assert record.is_effective_on(as_of=date(2026, 9, 1))


def test_waiver_is_not_allowed_for_prevoyance():
    with pytest.raises(ValueError, match="mutuelle"):
        EmployeeProtectionRecord.create(
            record_id="bad-waiver",
            structure_ref="structure-1",
            employee_ref="employee-1",
            organization_code="chorum",
            organization_kind=OrganizationKind.PREVOYANCE,
            relation_kind=EmployeeProtectionRelationKind.WAIVER,
            waiver_reason_code="test",
        )


def test_spst_monitoring_is_administrative_and_deadline_aware():
    record = EmployeeProtectionRecord.create(
        record_id="spst-2026",
        structure_ref="structure-1",
        employee_ref="employee-1",
        organization_code="pst35",
        organization_kind=OrganizationKind.SPST,
        relation_kind=EmployeeProtectionRelationKind.MONITORING,
        status=EmployeeProtectionStatus.PENDING,
        administrative_deadline=date(2026, 10, 15),
        document_ref="convocation-2026",
    )

    assert not record.is_due_on_or_before(as_of=date(2026, 10, 14))
    assert record.is_due_on_or_before(as_of=date(2026, 10, 15))


def test_monitoring_is_reserved_to_spst():
    with pytest.raises(ValueError, match="SPST"):
        EmployeeProtectionRecord.create(
            record_id="bad-monitoring",
            structure_ref="structure-1",
            employee_ref="employee-1",
            organization_code="unimutuelle",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.MONITORING,
        )


def test_transactional_organizations_stay_in_hr_cases_not_employee_protection():
    with pytest.raises(ValueError, match="réservé"):
        EmployeeProtectionRecord.create(
            record_id="urssaf-1",
            structure_ref="structure-1",
            employee_ref="employee-1",
            organization_code="urssaf",
            organization_kind=OrganizationKind.URSSAF,
            relation_kind=EmployeeProtectionRelationKind.REGISTRATION,
        )


def test_portfolio_isolates_structure_and_employee_and_rejects_duplicate_ids():
    first = EmployeeProtectionRecord.create(
        record_id="p1",
        structure_ref="structure-1",
        employee_ref="employee-1",
        organization_code="unimutuelle",
        organization_kind=OrganizationKind.MUTUELLE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=EmployeeProtectionStatus.ACTIVE,
        effective_period=EffectivePeriod(starts_on=date(2026, 1, 1)),
    )
    second = EmployeeProtectionRecord.create(
        record_id="p2",
        structure_ref="structure-1",
        employee_ref="employee-2",
        organization_code="chorum",
        organization_kind=OrganizationKind.PREVOYANCE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=EmployeeProtectionStatus.ACTIVE,
        effective_period=EffectivePeriod(starts_on=date(2026, 1, 1)),
    )
    portfolio = EmployeeProtectionPortfolio([first, second])

    assert portfolio.for_employee(
        structure_ref="structure-1", employee_ref="employee-1"
    ) == (first,)
    assert portfolio.effective_for_employee(
        structure_ref="structure-1",
        employee_ref="employee-1",
        as_of=date(2026, 9, 1),
    ) == (first,)

    with pytest.raises(ValueError, match="existe déjà"):
        portfolio.add(first)
