# -*- coding: utf-8 -*-

import pytest

from teamworks.Utils.UTILS_Identifiants import (
    normaliser_adresse,
    normaliser_bic,
    normaliser_iban,
    normaliser_identifiant_libre,
    normaliser_nir,
    normaliser_pays,
    normaliser_texte_identite,
)


def test_identity_address_and_country_preserve_unicode():
    assert normaliser_texte_identite("  E\u0301lise D’Œuvre ") == "Élise D’Œuvre"
    assert normaliser_adresse("  12 rue de l’Église – Bâtiment Œ  ") == "12 rue de l’Église – Bâtiment Œ"
    assert normaliser_pays("  Côte d’Ivoire  ") == "Côte d’Ivoire"


def test_free_identifier_keeps_leading_zeroes_and_letters():
    assert normaliser_identifiant_libre("  00A-0123  ") == "00A-0123"


def test_nir_standard_round_trip_and_key_validation():
    corps = "1800675123456"
    cle = 97 - (int(corps) % 97)
    nir = corps + "%02d" % cle
    assert normaliser_nir(" ".join([nir[:1], nir[1:3], nir[3:5], nir[5:7], nir[7:10], nir[10:13], nir[13:]])) == nir


def test_nir_corsica_2a_is_supported():
    corps_affiche = "180062A123456"
    corps_calcul = "1800619123456"
    cle = 97 - (int(corps_calcul) % 97)
    nir = corps_affiche + "%02d" % cle
    assert normaliser_nir(nir) == nir


@pytest.mark.parametrize("nir", ["123", "180067512345600", "1800675123456AA"])
def test_invalid_nir_is_rejected(nir):
    with pytest.raises(ValueError):
        normaliser_nir(nir)


def test_iban_and_bic_are_normalized():
    assert normaliser_iban("FR76 3000 6000 0112 3456 7890 189") == "FR7630006000011234567890189"
    assert normaliser_bic("agrifrpp") == "AGRIFRPP"


@pytest.mark.parametrize("iban", ["FR00 0000", "ABC", "FR7630006000011234567890188"])
def test_invalid_iban_is_rejected(iban):
    with pytest.raises(ValueError):
        normaliser_iban(iban)


@pytest.mark.parametrize("bic", ["ABC", "AGRIFR", "AGRIFRPPXXXX"])
def test_invalid_bic_is_rejected(bic):
    with pytest.raises(ValueError):
        normaliser_bic(bic)
