import pytest

from domain.common.recuperation import (
    JOURNEE_EXTRASCOLAIRE_MINUTES_ACTUELLE,
    credit_recuperation_minicamp,
    format_minutes_recuperation,
)


def test_ccns_une_nuitee_credite_une_journee_extrascolaire_actuelle_de_9h36():
    credit = credit_recuperation_minicamp(1, "CCNS")
    assert credit.unite == "minutes"
    assert credit.valeur == JOURNEE_EXTRASCOLAIRE_MINUTES_ACTUELLE == 576
    assert format_minutes_recuperation(credit.valeur) == "9:36"


def test_ccns_trois_nuitees_cumulent_28h48_avec_la_reference_actuelle():
    credit = credit_recuperation_minicamp(3, "CCNS")
    assert credit.valeur == 3 * JOURNEE_EXTRASCOLAIRE_MINUTES_ACTUELLE
    assert format_minutes_recuperation(credit.valeur) == "28:48"


def test_ccns_la_nuitee_suit_la_duree_de_journee_extrascolaire_fournie():
    credit = credit_recuperation_minicamp(
        2,
        "CCNS",
        journee_extrascolaire_minutes=8 * 60,
    )
    assert credit.valeur == 16 * 60
    assert format_minutes_recuperation(credit.valeur) == "16:00"


def test_cee_une_nuitee_credite_un_jour_sans_conversion_horaire():
    credit = credit_recuperation_minicamp(1, "CEE")
    assert credit.unite == "jours"
    assert credit.valeur == 1


def test_cee_trois_nuitees_cumulent_trois_jours():
    credit = credit_recuperation_minicamp(3, "CEE")
    assert credit.unite == "jours"
    assert credit.valeur == 3


def test_zero_nuitee_ne_credite_rien():
    assert credit_recuperation_minicamp(0, "CCNS").valeur == 0
    assert credit_recuperation_minicamp(0, "CEE").valeur == 0


@pytest.mark.parametrize("nuitees", [-1, -3])
def test_nombre_de_nuitees_negatif_est_refuse(nuitees):
    with pytest.raises(ValueError):
        credit_recuperation_minicamp(nuitees, "CCNS")


@pytest.mark.parametrize("nuitees", [1.0, "1", None, True])
def test_nombre_de_nuitees_non_entier_est_refuse(nuitees):
    with pytest.raises(TypeError):
        credit_recuperation_minicamp(nuitees, "CCNS")


@pytest.mark.parametrize("duree", [0, -1])
def test_duree_de_journee_extrascolaire_non_positive_est_refusee(duree):
    with pytest.raises(ValueError):
        credit_recuperation_minicamp(1, "CCNS", journee_extrascolaire_minutes=duree)


@pytest.mark.parametrize("duree", [9.6, "576", None, True])
def test_duree_de_journee_extrascolaire_non_entiere_est_refusee(duree):
    with pytest.raises(TypeError):
        credit_recuperation_minicamp(1, "CCNS", journee_extrascolaire_minutes=duree)


def test_regime_inconnu_est_refuse():
    with pytest.raises(ValueError):
        credit_recuperation_minicamp(1, "ECLAT")
