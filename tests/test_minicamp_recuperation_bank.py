import pytest

from domain.common.recuperation import (
    CCNS_MINUTES_PAR_NUITEE,
    credit_recuperation_minicamp,
    format_minutes_recuperation,
)


def test_ccns_une_nuitee_credite_9h36():
    credit = credit_recuperation_minicamp(1, "CCNS")
    assert credit.unite == "minutes"
    assert credit.valeur == 576
    assert format_minutes_recuperation(credit.valeur) == "9:36"


def test_ccns_trois_nuitees_cumulent_28h48():
    credit = credit_recuperation_minicamp(3, "CCNS")
    assert credit.valeur == 3 * CCNS_MINUTES_PAR_NUITEE
    assert format_minutes_recuperation(credit.valeur) == "28:48"


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


def test_regime_inconnu_est_refuse():
    with pytest.raises(ValueError):
        credit_recuperation_minicamp(1, "ECLAT")
