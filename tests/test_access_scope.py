import pytest

from domain.access.scope import Scope, ScopeAtom, ScopeKind


def test_scope_requires_at_least_one_valid_atom():
    with pytest.raises(ValueError, match="au moins"):
        Scope(())
    with pytest.raises(ValueError, match="ScopeAtom"):
        Scope(("site-a",))


def test_targeted_scope_requires_identifiers_and_normalizes_them():
    with pytest.raises(ValueError, match="identifiant"):
        Scope.for_targets(ScopeKind.SITE, [])
    with pytest.raises(ValueError, match="vides"):
        Scope.for_targets(ScopeKind.SITE, [" "])

    scope = Scope.for_targets(ScopeKind.SITE, [" Bais ", "Bais", "Evron"])

    assert scope.atoms == (ScopeAtom.targeted(ScopeKind.SITE, ["Bais", "Evron"]),)


def test_global_and_personal_scopes_do_not_accept_identifiers():
    with pytest.raises(ValueError, match="pas d'identifiant"):
        ScopeAtom(kind=ScopeKind.GLOBAL, identifiers=frozenset({"association"}))
    with pytest.raises(ValueError, match="pas d'identifiant"):
        ScopeAtom(kind=ScopeKind.PERSONAL, identifiers=frozenset({"me"}))

    assert Scope.global_scope().is_global()
    assert Scope.personal().is_personal()
    assert not Scope.combine([Scope.personal(), Scope.for_targets(ScopeKind.ACTIVITY, ["EMS"])]).is_personal()


def test_contains_checks_scope_coverage_without_managing_rights():
    association = Scope.global_scope()
    bais_and_evron = Scope.for_targets(ScopeKind.SITE, ["Bais", "Evron"])
    bais = Scope.for_targets(ScopeKind.SITE, ["Bais"])
    sport = Scope.for_targets(ScopeKind.SERVICE, ["Sport"])

    assert association.contains(bais_and_evron)
    assert bais_and_evron.contains(bais)
    assert not bais.contains(bais_and_evron)
    assert not sport.contains(bais)


def test_intersects_detects_common_scope_parts():
    bais_and_evron = Scope.for_targets(ScopeKind.SITE, ["Bais", "Evron"])
    evron = Scope.for_targets(ScopeKind.SITE, ["Evron"])
    mayenne = Scope.for_targets(ScopeKind.SITE, ["Mayenne"])
    sport = Scope.for_targets(ScopeKind.SERVICE, ["Sport"])

    assert bais_and_evron.intersects(evron)
    assert Scope.global_scope().intersects(sport)
    assert not bais_and_evron.intersects(mayenne)
    assert not bais_and_evron.intersects(sport)


def test_merge_combines_multiple_generic_scope_kinds():
    scope = (
        Scope.global_scope()
        .merge(Scope.for_targets(ScopeKind.SERVICE, ["Sport"]))
        .merge(Scope.for_targets(ScopeKind.SITE, ["Bais"]))
        .merge(Scope.for_targets(ScopeKind.SITE, ["Evron"]))
    )

    assert scope.is_global()
    assert scope.contains(Scope.for_targets(ScopeKind.SERVICE, ["Sport"]))
    assert scope.contains(Scope.for_targets(ScopeKind.SITE, ["Bais", "Evron"]))


def test_combine_supports_personal_and_activity_scope():
    scope = Scope.combine([Scope.personal(), Scope.for_targets(ScopeKind.ACTIVITY, ["EMS"])])

    assert scope.contains(Scope.personal())
    assert scope.contains(Scope.for_targets(ScopeKind.ACTIVITY, ["EMS"]))
    assert scope.intersects(Scope.for_targets(ScopeKind.ACTIVITY, ["EMS", "Yoga"]))
    assert not scope.contains(Scope.for_targets(ScopeKind.ACTIVITY, ["Yoga"]))
