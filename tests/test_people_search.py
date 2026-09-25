import pytest

from domain.people.person import Person
from domain.people.search import normalize_search_text, search_people


def person(code, last_name, first_name):
    return Person(code_internal=code, last_name=last_name, first_name=first_name)


PEOPLE = [
    person("P01", "DUPONT", "Marie"),
    person("P02", "DUPONT", "Marie"),
    person("P03", "DUPONT", "Marianne"),
    person("P04", "DUPOND", "Marie"),
    person("P05", "DUPONT", "Marc"),
    person("P06", "LE GOFF", "Hélène"),
    person("P07", "LE-GOFF", "Hélène"),
    person("P08", "LE GOF", "Hélène"),
    person("P09", "LE GALL", "Élodie"),
    person("P10", "LEGALL", "Elodie"),
    person("P11", "DE LA TOUR", "Anne"),
    person("P12", "DELATOUR", "Anne"),
    person("P13", "D'ARVOR", "Maël"),
    person("P14", "DARVOR", "Mael"),
    person("P15", "KERJEAN-LE GALL", "Anaïs"),
    person("P16", "MARTIN", "Martin"),
    person("P17", "MARTINEAU", "Martine"),
    person("P18", "LE MARTIN", "Marie"),
    person("P19", "TOUR", "Anne"),
    person("P20", "DE MARTIN", "Anne"),
    person("P21", "LE GALL-LE GOFF", "Yann"),
]


def codes(results, kind=None):
    return {
        result.person.code_internal
        for result in results
        if kind is None or result.kind == kind
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Hélène", "helene"),
        ("ÉLODIE", "elodie"),
        ("  Marie   DUPONT  ", "marie dupont"),
        ("LE-GOFF", "le goff"),
        ("D'ARVOR", "d arvor"),
        ("d’arvor", "d arvor"),
        ("KERJEAN-LE GALL", "kerjean le gall"),
        ("Maël", "mael"),
    ],
)
def test_normalization(raw, expected):
    assert normalize_search_text(raw) == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("DUPONT MARIE", {"P01", "P02"}),
        ("helene le goff", {"P06", "P07"}),
        ("le goff helene", {"P06", "P07"}),
        ("   helene    le   goff   ", {"P06", "P07"}),
        ("le-goff helene", {"P06", "P07"}),
        ("dupo mar", {"P01", "P02", "P03", "P05"}),
        ("de la tour anne", {"P11"}),
        ("kerjean le gall anais", {"P15"}),
        ("martin martin", {"P16"}),
    ],
)
def test_certain_matching(query, expected):
    assert codes(search_people(query, PEOPLE), "certain") == expected


def test_exact_homonyms_are_kept_with_same_score():
    results = search_people("dupont marie", PEOPLE)
    homonyms = [r for r in results if r.person.code_internal in {"P01", "P02"}]
    assert {r.person.code_internal for r in homonyms} == {"P01", "P02"}
    assert len({r.score for r in homonyms}) == 1


@pytest.mark.parametrize(
    ("query", "forbidden"),
    [
        ("martin", {"P17"}),
        ("le goff helene", {"P08"}),
        ("dupont marie", {"P04"}),
        ("delatour anne", {"P11"}),
        ("legall elodie", {"P09"}),
        ("darvor mael", {"P13"}),
    ],
)
def test_false_positives_are_not_certain(query, forbidden):
    assert codes(search_people(query, PEOPLE), "certain").isdisjoint(forbidden)


def test_typo_is_suggestion_not_certainty():
    results = search_people("dpuont marie", PEOPLE)
    assert codes(results, "certain").isdisjoint({"P01", "P02"})
    assert {"P01", "P02"}.issubset(codes(results, "suggestion"))


@pytest.mark.parametrize("query", ["d", "du", "ma", "le"])
def test_short_queries_do_not_trigger_fuzzy(query):
    assert not codes(search_people(query, PEOPLE), "suggestion")


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("Hélène LE GOFF", "helene le goff"),
        ("LE GOFF Hélène", "Hélène LE GOFF"),
        ("  helene   le goff ", "helene le goff"),
        ("LE-GOFF Hélène", "le goff helene"),
        ("ÉLODIE LE GALL", "elodie le gall"),
    ],
)
def test_equivalent_queries_have_same_certain_results(left, right):
    assert codes(search_people(left, PEOPLE), "certain") == codes(
        search_people(right, PEOPLE), "certain"
    )


def test_unknown_query_has_no_results():
    assert search_people("xyzabc", PEOPLE) == []



@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("De La Tour Anne", {"P11"}),
        ("de   la   tour anne", {"P11"}),
        ("anne de la tour", {"P11"}),
        ("de la tou anne", {"P11"}),
        ("tour anne", {"P11", "P19"}),
        ("d'arvor mael", {"P13"}),
        ("d’arvor mael", {"P13"}),
        ("d arvor mael", {"P13"}),
        ("le-goff helene", {"P06", "P07"}),
        ("le gall le goff yann", {"P21"}),
    ],
)
def test_particle_matching_contract(query, expected):
    assert codes(search_people(query, PEOPLE), "certain") == expected


@pytest.mark.parametrize(
    ("query", "forbidden"),
    [
        ("delatour anne", {"P11"}),
        ("darvor mael", {"P13"}),
        ("legall elodie", {"P09"}),
        ("le gall elodie", {"P10"}),
        ("legoff helene", {"P06", "P07"}),
    ],
)
def test_fused_particle_variants_are_not_silent_equivalences(query, forbidden):
    assert codes(search_people(query, PEOPLE), "certain").isdisjoint(forbidden)


@pytest.mark.parametrize("query", ["d", "de", "la", "le", "du", "des"])
def test_particle_only_short_queries_never_trigger_fuzzy(query):
    assert not codes(search_people(query, PEOPLE), "suggestion")


def test_exact_simple_surname_ranks_before_same_token_in_compound_surname():
    results = search_people("martin", PEOPLE)
    result_codes = [r.person.code_internal for r in results]
    assert result_codes.index("P16") < result_codes.index("P18")
    assert result_codes.index("P16") < result_codes.index("P20")


def test_exact_simple_tour_ranks_before_de_la_tour():
    results = search_people("tour", PEOPLE)
    result_codes = [r.person.code_internal for r in results]
    assert result_codes.index("P19") < result_codes.index("P11")


def test_full_surname_is_not_treated_as_prefix_of_longer_surname():
    results = search_people("martin", PEOPLE)
    assert "P17" not in codes(results, "certain")


def test_short_prefix_still_supports_abbreviated_entry():
    assert codes(search_people("dupo mar", PEOPLE), "certain") == {
        "P01",
        "P02",
        "P03",
        "P05",
    }


def test_ambiguous_short_prefix_keeps_all_literal_prefix_matches():
    assert codes(search_people("dup mar", PEOPLE), "certain") == {
        "P01",
        "P02",
        "P03",
        "P04",
        "P05",
    }


def test_repeated_token_requires_distinct_occurrences():
    assert codes(search_people("martin martin", PEOPLE), "certain") == {"P16"}


def test_exact_simple_surname_gets_higher_score_than_compound_surnames():
    results = search_people("martin", PEOPLE)
    by_code = {result.person.code_internal: result for result in results}
    assert by_code["P16"].score > by_code["P18"].score
    assert by_code["P16"].score > by_code["P20"].score
