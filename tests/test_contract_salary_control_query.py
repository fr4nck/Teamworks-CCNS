from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.contracts import (
    ContractSalaryControlPage,
    ContractSalaryControlProjection,
    ContractSalaryControlQuery,
    ContractSalaryControlQueryService,
    ContractSalaryControlRow,
    ContractSalaryControlSortField,
    ContractSalaryControlStatus,
    ContractSalaryEvaluationFailureReason,
    SortDirection,
)
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory

D = date(2026, 7, 1)
C1 = UUID('00000000-0000-0000-0000-000000000001')
C2 = UUID('00000000-0000-0000-0000-000000000002')
C3 = UUID('00000000-0000-0000-0000-000000000003')
E1 = UUID('10000000-0000-0000-0000-000000000001')
E2 = UUID('10000000-0000-0000-0000-000000000002')
E3 = UUID('10000000-0000-0000-0000-000000000003')


def row(status, cid, eid, cls, rem, mini, short, source, terr, reason=None, failure=None, issue_code=None, issue=None):
    return ContractSalaryControlRow(cid, eid, D, status, cls, rem, mini, short, source, terr, reason, failure, issue_code, issue)


def projection():
    return ContractSalaryControlProjection(D, (
        row(ContractSalaryControlStatus.COMPLIANT, C2, E2, 'BETA', Decimal('2100.00'), Decimal('2000.00'), Decimal('0.00'), ApplicableSalaryMinimumSource.CCNS, SmicTerritory.METROPOLITAN_FRANCE),
        row(ContractSalaryControlStatus.NON_COMPLIANT, C1, E1, 'ALPHA', Decimal('1800.00'), Decimal('2000.00'), Decimal('200.00'), ApplicableSalaryMinimumSource.SMIC, SmicTerritory.MAYOTTE, issue_code='SALARY_SHORTFALL', issue='Manque salarial exact .*'),
        row(ContractSalaryControlStatus.NOT_EVALUATED, C3, E3, 'GAMMA', None, None, Decimal('0.00'), None, SmicTerritory.METROPOLITAN_FRANCE, ContractSalaryEvaluationFailureReason.MISSING_TERRITORY, 'Territoire absent'),
    ))


def execute(query=ContractSalaryControlQuery(), proj=None):
    return ContractSalaryControlQueryService().execute(proj or projection(), query)


def ids(page):
    return [r.contract_id for r in page.rows]


def test_projection_vide_et_requete_par_defaut_conserve_ordre_source():
    empty = execute(proj=ContractSalaryControlProjection(D, ()))
    assert empty.rows == () and empty.filtered_rows == () and empty.valid is True
    page = execute()
    assert ids(page) == [C2, C1, C3]
    assert page.total_source_count == page.total_filtered_count == 3
    assert page.limit is None and page.offset == 0


@pytest.mark.parametrize('status, expected', [
    (ContractSalaryControlStatus.COMPLIANT, [C2]),
    (ContractSalaryControlStatus.NON_COMPLIANT, [C1]),
    (ContractSalaryControlStatus.NOT_EVALUATED, [C3]),
])
def test_filtre_par_statut(status, expected):
    assert ids(execute(ContractSalaryControlQuery(statuses=(status,)))) == expected


def test_plusieurs_statuts_et_filtres_identifiants_classification_sources_territoires_motifs():
    assert ids(execute(ContractSalaryControlQuery(statuses=(ContractSalaryControlStatus.NON_COMPLIANT, ContractSalaryControlStatus.NOT_EVALUATED)))) == [C1, C3]
    assert ids(execute(ContractSalaryControlQuery(employee_ids=(E1,)))) == [C1]
    assert ids(execute(ContractSalaryControlQuery(contract_ids=(C3,)))) == [C3]
    assert ids(execute(ContractSalaryControlQuery(classification_codes=(' ALPHA ',)))) == [C1]
    assert ids(execute(ContractSalaryControlQuery(minimum_sources=(ApplicableSalaryMinimumSource.SMIC,)))) == [C1]
    assert ids(execute(ContractSalaryControlQuery(territories=(SmicTerritory.MAYOTTE,)))) == [C1]
    assert ids(execute(ContractSalaryControlQuery(failure_reasons=(ContractSalaryEvaluationFailureReason.MISSING_TERRITORY,)))) == [C3]


def test_filtres_manque_salarial_et_combinaison():
    assert ids(execute(ContractSalaryControlQuery(has_shortfall=True))) == [C1]
    assert ids(execute(ContractSalaryControlQuery(has_shortfall=False))) == [C2, C3]
    assert ids(execute(ContractSalaryControlQuery(minimum_shortfall_amount=Decimal('100.00')))) == [C1]
    assert ids(execute(ContractSalaryControlQuery(maximum_shortfall_amount=Decimal('100.00')))) == [C2, C3]
    assert ids(execute(ContractSalaryControlQuery(minimum_shortfall_amount=Decimal('100.00'), maximum_shortfall_amount=Decimal('250.00'), territories=(SmicTerritory.MAYOTTE,)))) == [C1]


@pytest.mark.parametrize('text, expected', [('alp', [C1]), ('territoire', [C3]), ('salary_shortfall', [C1]), ('MANQUE', [C1]), ('.*', [C1])])
def test_recherche_textuelle(text, expected):
    assert ids(execute(ContractSalaryControlQuery(search_text=text))) == expected


def test_recherche_vide_refusee():
    with pytest.raises(ValueError, match='search_text'):
        ContractSalaryControlQuery(search_text='  ')


@pytest.mark.parametrize('field', [
    ContractSalaryControlSortField.STATUS, ContractSalaryControlSortField.CONTRACT_ID, ContractSalaryControlSortField.EMPLOYEE_ID,
    ContractSalaryControlSortField.CLASSIFICATION_CODE, ContractSalaryControlSortField.REMUNERATION_AMOUNT,
    ContractSalaryControlSortField.APPLICABLE_MINIMUM_AMOUNT, ContractSalaryControlSortField.SHORTFALL_AMOUNT,
    ContractSalaryControlSortField.MINIMUM_SOURCE, ContractSalaryControlSortField.TERRITORY, ContractSalaryControlSortField.FAILURE_REASON,
])
def test_tous_les_champs_de_tri(field):
    page = execute(ContractSalaryControlQuery(sort_field=field))
    assert len(page.rows) == 3


def test_tri_ascendant_descendant_stabilite_none_et_source_order():
    assert ids(execute(ContractSalaryControlQuery(sort_field=ContractSalaryControlSortField.CONTRACT_ID))) == [C1, C2, C3]
    assert ids(execute(ContractSalaryControlQuery(sort_direction=SortDirection.DESCENDING))) == [C3, C1, C2]
    assert execute(ContractSalaryControlQuery(sort_field=ContractSalaryControlSortField.REMUNERATION_AMOUNT)).rows[-1].remuneration_amount is None
    same = ContractSalaryControlProjection(D, (projection().rows[0], row(ContractSalaryControlStatus.COMPLIANT, uuid4(), E1, 'BETA', Decimal('2100.00'), Decimal('2000.00'), Decimal('0.00'), ApplicableSalaryMinimumSource.CCNS, SmicTerritory.METROPOLITAN_FRANCE)))
    assert execute(ContractSalaryControlQuery(sort_field=ContractSalaryControlSortField.CLASSIFICATION_CODE), same).rows == same.rows


def test_pagination_navigation_et_offset_au_dela():
    p = execute(ContractSalaryControlQuery(offset=1))
    assert ids(p) == [C1, C3] and p.has_previous_page and not p.has_next_page
    p = execute(ContractSalaryControlQuery(limit=1))
    assert ids(p) == [C2] and p.has_next_page and p.next_offset == 1 and p.previous_offset is None
    p = execute(ContractSalaryControlQuery(offset=1, limit=1))
    assert ids(p) == [C1] and p.has_previous_page and p.has_next_page and p.previous_offset == 0 and p.next_offset == 2
    p = execute(ContractSalaryControlQuery(offset=2, limit=1))
    assert ids(p) == [C3] and not p.has_next_page
    assert execute(ContractSalaryControlQuery(offset=99)).rows == ()


def test_compteurs_total_valid_et_recherches_portent_sur_filtered_rows():
    p = execute(ContractSalaryControlQuery(limit=1))
    assert p.compliant_count == 1 and p.non_compliant_count == 1 and p.not_evaluated_count == 1
    assert p.total_shortfall_amount == Decimal('200.00') and p.valid is False
    assert p.row_for_contract(C1) is projection().row_for_contract(C1) or p.row_for_contract(C1).contract_id == C1
    assert p.rows_for_employee(E1)[0].contract_id == C1
    assert p.rows_for_status(ContractSalaryControlStatus.NON_COMPLIANT)[0].contract_id == C1


def test_identite_lignes_et_projection_source_non_modifiee():
    proj = projection()
    p = execute(ContractSalaryControlQuery(sort_field=ContractSalaryControlSortField.CONTRACT_ID), proj)
    assert p.rows[0] is proj.rows[1]
    assert proj.rows == (proj.rows[0], proj.rows[1], proj.rows[2])


@pytest.mark.parametrize('kwargs', [
    {'statuses': (ContractSalaryControlStatus.COMPLIANT, ContractSalaryControlStatus.COMPLIANT)},
    {'employee_ids': (str(E1),)},
    {'offset': True}, {'limit': False}, {'offset': -1}, {'limit': 0}, {'limit': -1},
    {'minimum_shortfall_amount': Decimal('10.00'), 'maximum_shortfall_amount': Decimal('1.00')},
    {'minimum_shortfall_amount': Decimal('1.001')}, {'contract_ids': (str(C1),)},
])
def test_validations_strictes(kwargs):
    with pytest.raises((TypeError, ValueError)):
        ContractSalaryControlQuery(**kwargs)


def test_immutabilite_et_page_uuid_strict():
    q = ContractSalaryControlQuery()
    with pytest.raises(FrozenInstanceError):
        q.offset = 2
    with pytest.raises(TypeError):
        ContractSalaryControlPage(q, projection(), (), (), 0, 0, 0, None, id='bad')
    with pytest.raises(TypeError):
        ContractSalaryControlQueryService().execute('bad', q)
    with pytest.raises(TypeError):
        ContractSalaryControlQueryService().execute(projection(), 'bad')
