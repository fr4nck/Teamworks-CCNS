from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from uuid import UUID, uuid4

import pytest

from domain.missions import Mission, MissionOccurrence, MissionOccurrenceAssignment, MissionOccurrenceAssignmentStatus
from domain.people import Civility, Employee
from domain.planning import Planning, PlanningStatus


def employee(name="Ada"):
    return Employee(civility=Civility.MADAME, first_name=name, last_name="Lovelace")


def occurrence(start=datetime(2026, 7, 20, 9), end=datetime(2026, 7, 20, 17), code="ALSH"):
    return MissionOccurrence(mission=Mission(code=code, name="Animation"), starts_at=start, ends_at=end)


def assignment(emp=None, occ=None, *, id=None):
    kwargs = {"employee": emp or employee(), "occurrence": occ or occurrence(), "status": MissionOccurrenceAssignmentStatus.PLANNED}
    if id is not None:
        kwargs["id"] = id
    return MissionOccurrenceAssignment(**kwargs)


def planning(**kwargs):
    data = {"code": " ete-2026 ", "name": " Planning été ", "starts_on": date(2026, 7, 1), "ends_on": date(2026, 7, 31)}
    data.update(kwargs)
    return Planning(**data)


def test_creation_minimale_valide_uuid_genere_et_normalisation():
    p = planning()
    assert isinstance(p.id, UUID)
    assert p.code == "ETE-2026"
    assert p.name == "Planning été"
    assert p.assignments == ()
    assert p.status is PlanningStatus.DRAFT
    assert p.observations is None
    assert p.active is True


def test_creation_complete_valide_uuid_explicite_observations_et_statut():
    planning_id = uuid4(); a = assignment()
    p = planning(id=planning_id, assignments=(a,), status=PlanningStatus.PUBLISHED, observations="  OK  ", active=False)
    assert p.id == planning_id
    assert p.assignments == (a,)
    assert p.status is PlanningStatus.PUBLISHED
    assert p.observations == "OK"
    assert p.active is False


@pytest.mark.parametrize("kwargs, message", [
    ({"id": "bad"}, "UUID"),
    ({"code": "  "}, "code"),
    ({"name": "  "}, "nom"),
    ({"starts_on": "2026-07-01"}, "date stricte"),
    ({"ends_on": "2026-07-31"}, "date stricte"),
    ({"starts_on": datetime(2026, 7, 1), "ends_on": date(2026, 7, 31)}, "date stricte"),
    ({"starts_on": date(2026, 8, 1), "ends_on": date(2026, 7, 31)}, "supérieure ou égale"),
    ({"assignments": [assignment()]}, "tuple"),
    ({"assignments": (x for x in ())}, "tuple"),
    ({"assignments": (object(),)}, "MissionOccurrenceAssignment"),
    ({"status": "draft"}, "PlanningStatus"),
    ({"active": 1}, "booléen"),
    ({"observations": "  "}, "observations"),
])
def test_creation_refuse_les_valeurs_invalides(kwargs, message):
    with pytest.raises(ValueError, match=message):
        planning(**kwargs)


def test_meme_date_de_debut_et_de_fin_et_tuple_vide_acceptes():
    p = planning(starts_on=date(2026, 7, 20), ends_on=date(2026, 7, 20), assignments=())
    assert p.contains_day(date(2026, 7, 20)) is True


def test_doublon_uuid_affectation_refuse_sans_confondre_salarie_ou_occurrence():
    emp = employee(); occ = occurrence(); same_id = uuid4()
    a1 = assignment(emp, occ, id=same_id); a2 = assignment(emp, occ)
    assert planning(assignments=(a1, a2)).assignment_count() == 2
    with pytest.raises(ValueError, match="même identifiant"):
        planning(assignments=(a1, replace(a2, id=same_id)))


@pytest.mark.parametrize("occ", [
    occurrence(datetime(2026, 7, 1), datetime(2026, 7, 1, 1)),
    occurrence(datetime(2026, 7, 31, 22), datetime(2026, 7, 31, 23)),
    occurrence(datetime(2026, 7, 20), datetime(2026, 7, 22)),
])
def test_affectation_dans_periode_acceptee(occ):
    assert planning(assignments=(assignment(occ=occ),)).assignment_count() == 1


@pytest.mark.parametrize("occ", [
    occurrence(datetime(2026, 6, 30, 22), datetime(2026, 6, 30, 23)),
    occurrence(datetime(2026, 8, 1), datetime(2026, 8, 1, 1)),
    occurrence(datetime(2026, 6, 30, 23), datetime(2026, 7, 1, 1)),
    occurrence(datetime(2026, 7, 31, 23), datetime(2026, 8, 1, 1)),
])
def test_affectation_hors_periode_refusee(occ):
    with pytest.raises(ValueError, match="période"):
        planning(assignments=(assignment(occ=occ),))


def test_methodes_de_consultation_et_ordre_conserve():
    emp1 = employee("Ada"); emp2 = employee("Grace"); occ1 = occurrence(code="A"); occ2 = occurrence(datetime(2026, 7, 21, 9), datetime(2026, 7, 21, 17), code="B")
    a1 = assignment(emp1, occ1); a2 = assignment(emp2, occ1); a3 = assignment(emp1, occ2)
    p = planning(assignments=(a1, a2, a3), observations="note", status=PlanningStatus.VALIDATED)
    assert p.is_active() and p.is_validated() and not p.is_draft() and not p.is_published() and not p.is_archived()
    assert p.has_observations() and p.has_assignments() and p.assignment_count() == 3
    assert p.contains_day(date(2026, 7, 1)) and p.contains_day(date(2026, 7, 31)) and not p.contains_day(date(2026, 8, 1))
    with pytest.raises(ValueError, match="date stricte"):
        p.contains_day(datetime(2026, 7, 1))
    assert p.contains_assignment(replace(a1, employee=emp2)) is True
    assert p.assignment_by_id(a2.id) == a2
    with pytest.raises(ValueError, match="Aucune"):
        p.assignment_by_id(uuid4())
    with pytest.raises(ValueError, match="UUID"):
        p.assignment_by_id("bad")
    assert p.assignments_for_employee(emp1) == (a1, a3)
    assert p.assignments_for_occurrence(occ1) == (a1, a2)
    with pytest.raises(ValueError, match="Employee"):
        p.assignments_for_employee(object())
    with pytest.raises(ValueError, match="MissionOccurrence"):
        p.assignments_for_occurrence(object())


def test_transformations_immutables_ajout_retrait_remplacement_et_statut():
    a1 = assignment(); a2 = assignment(occ=occurrence(datetime(2026, 7, 21, 9), datetime(2026, 7, 21, 17), "B")); a3 = assignment(occ=occurrence(datetime(2026, 7, 22, 9), datetime(2026, 7, 22, 17), "C"))
    original = planning(assignments=(a1, a2))
    added = original.with_assignment(a3)
    assert added is not original and added.assignments == (a1, a2, a3) and original.assignments == (a1, a2)
    with pytest.raises(ValueError, match="déjà"):
        original.with_assignment(replace(a1, employee=employee("Grace")))
    with pytest.raises(ValueError, match="période"):
        original.with_assignment(assignment(occ=occurrence(datetime(2026, 8, 1), datetime(2026, 8, 1, 1))))
    removed = added.without_assignment(a2)
    assert removed is not added and removed.assignments == (a1, a3)
    with pytest.raises(ValueError, match="pas présente"):
        original.without_assignment(a3)
    replacement = replace(a2, occurrence=occurrence(datetime(2026, 7, 23, 9), datetime(2026, 7, 23, 17), "D"))
    replaced = original.replace_assignment(replacement)
    assert replaced.assignments == (a1, replacement) and replaced.assignments[1].id == a2.id
    with pytest.raises(ValueError, match="pas présente"):
        original.replace_assignment(a3)
    with pytest.raises(ValueError, match="période"):
        original.replace_assignment(replace(a1, occurrence=occurrence(datetime(2026, 8, 1), datetime(2026, 8, 1, 1))))
    published = original.with_status(PlanningStatus.PUBLISHED)
    assert published is not original and published.status is PlanningStatus.PUBLISHED and original.status is PlanningStatus.DRAFT
    with pytest.raises(ValueError, match="PlanningStatus"):
        original.with_status("published")


def test_immutabilite_planning_status_strict_et_assignments_tuple():
    p = planning()
    with pytest.raises(FrozenInstanceError):
        p.code = "AUTRE"
    assert isinstance(PlanningStatus.DRAFT, PlanningStatus)
    assert PlanningStatus.DRAFT.value == "draft"
    assert isinstance(p.assignments, tuple)
