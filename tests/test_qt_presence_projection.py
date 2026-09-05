from __future__ import annotations

from types import SimpleNamespace

from presence_projection import project_presences


def _presence(key, date, start, end, category, title=""):
    return SimpleNamespace(
        IDpresence=key,
        date=date,
        heure_debut=start,
        heure_fin=end,
        IDcategorie=category,
        intitule=title,
    )


def _category(key, name, color):
    return SimpleNamespace(IDcategorie=key, nom_categorie=name, couleur=color)


def _vacation(key, name, year, start, end):
    return SimpleNamespace(
        IDperiode=key,
        nom=name,
        annee=year,
        date_debut=start,
        date_fin=end,
    )


def test_presence_projection_reproduces_historical_display_contract():
    views = project_presences(
        (
            _presence(1, "2009-07-01", "08:00", "18:00", 1),
            _presence(2, "2009-07-02", "07:30", "17:00", 1),
            _presence(3, "2009-07-02", "18:30", "19:30", 5, "Réunion de fonctionnement"),
        ),
        (
            _category(1, "Animation", "(213, 244, 138)"),
            _category(5, "Réunion", "(196, 225, 255)"),
        ),
        (_vacation(5, "Eté", "2009", "2009-07-02", "2009-09-01"),),
    )

    assert views[0].date == "Mercredi 1 juillet 2009"
    assert views[0].vacation == ""
    assert views[0].schedule == "8h00-18h00"
    assert views[0].duration == "10h00"
    assert views[0].label == "Animation"
    assert views[0].category_color == "(213, 244, 138)"

    assert views[1].date == "Jeudi 2 juillet 2009"
    assert views[1].vacation == "Eté 2009"
    assert views[1].schedule == "7h30-17h00"
    assert views[1].duration == "9h30"

    assert views[2].date == ""
    assert views[2].vacation == "Eté 2009"
    assert views[2].schedule == "18h30-19h30"
    assert views[2].duration == "1h00"
    assert views[2].label == "Réunion (Réunion de fonctionnement)"


def test_presence_projection_keeps_last_matching_vacation_like_wx_loop():
    views = project_presences(
        (_presence(10, "2009-07-04", "09:00", "10:00", 1),),
        (_category(1, "Animation", "(1, 2, 3)"),),
        (
            _vacation(1, "Première", "2009", "2009-07-01", "2009-07-10"),
            _vacation(2, "Seconde", "2009", "2009-07-04", "2009-07-12"),
        ),
    )

    assert views[0].vacation == "Seconde 2009"


def test_presence_projection_handles_historical_midnight_modulo_and_invalid_values():
    views = project_presences(
        (
            _presence(20, "2009-07-05", "23:30", "01:00", 1),
            _presence(21, "bad-date", "bad", "01:00", 1),
        ),
        (_category(1, "Animation", "(1, 2, 3)"),),
        (),
    )

    assert views[0].duration == "1h30"
    assert views[1].date == ""
    assert views[1].schedule == "—"
    assert views[1].duration == "—"
