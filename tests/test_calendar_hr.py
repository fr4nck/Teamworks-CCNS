import datetime

from teamworks.CcnsCore.calendar_hr import build_birthdays_index, format_birthday_names


def test_build_birthdays_index_projects_registry_birthdays_on_displayed_year():
    rows = [
        (12, "DUPONT", "Alice", "1990-09-02"),
        (27, "MARTIN", "Benoit", datetime.date(1985, 9, 2)),
        (31, "SANS DATE", "Camille", None),
    ]

    result = build_birthdays_index(rows, 2026)

    assert list(result) == [datetime.date(2026, 9, 2)]
    assert [person["IDpersonne"] for person in result[datetime.date(2026, 9, 2)]] == [12, 27]
    assert format_birthday_names(result[datetime.date(2026, 9, 2)]) == "Alice DUPONT, Benoit MARTIN"


def test_build_birthdays_index_ignores_invalid_dates():
    rows = [
        (1, "INVALIDE", "Date", "pas-une-date"),
        (2, "VIDE", "Date", ""),
    ]

    assert build_birthdays_index(rows, 2026) == {}


def test_february_29_birthdays_are_visible_on_february_28_in_non_leap_years():
    rows = [(9, "BISSEXTILE", "Lina", "2000-02-29")]

    normal_year = build_birthdays_index(rows, 2026)
    leap_year = build_birthdays_index(rows, 2028)

    assert datetime.date(2026, 2, 28) in normal_year
    assert datetime.date(2028, 2, 29) in leap_year


def test_people_sharing_a_birthday_are_sorted_by_first_name_then_last_name():
    rows = [
        (3, "Zulu", "Chloe", "1991-04-10"),
        (2, "Beta", "Alice", "1988-04-10"),
        (1, "Alpha", "Alice", "1992-04-10"),
    ]

    people = build_birthdays_index(rows, 2026)[datetime.date(2026, 4, 10)]

    assert [(person["prenom"], person["nom"]) for person in people] == [
        ("Alice", "Alpha"),
        ("Alice", "Beta"),
        ("Chloe", "Zulu"),
    ]
