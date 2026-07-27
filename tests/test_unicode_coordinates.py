# -*- coding: utf-8 -*-

import csv
import io
import sqlite3

import pytest

from teamworks.Utils.UTILS_Coordonnees import (
    normaliser_email,
    normaliser_telephone,
    normaliser_texte,
)


def test_unicode_text_is_normalized_without_data_loss():
    decomposed = "E\u0301lodie D’Œuvre – 12 €"
    assert normaliser_texte("  %s  " % decomposed) == "Élodie D’Œuvre – 12 €"


@pytest.mark.parametrize(
    "source, expected",
    [
        ("06 12 34 56 78", "06.12.34.56.78"),
        ("06.12.34.56.78", "06.12.34.56.78"),
        ("06-12-34-56-78", "06.12.34.56.78"),
        ("+33 6 12 34 56 78", "06.12.34.56.78"),
        ("0033 6 12 34 56 78", "06.12.34.56.78"),
        ("+32 470 12 34 56", "+32470123456"),
        ("06\u00a012\u202f34 56 78", "06.12.34.56.78"),
    ],
)
def test_phone_formats_are_accepted(source, expected):
    assert normaliser_telephone(source) == expected


@pytest.mark.parametrize("source", ["", "abc", "+33 téléphone", "123"])
def test_invalid_phone_is_rejected(source):
    if source == "":
        assert normaliser_telephone(source) == ""
    else:
        with pytest.raises(ValueError):
            normaliser_telephone(source)


def test_email_preserves_unicode_local_part_and_normalizes_domain():
    assert normaliser_email("  élodie@example.ORG ") == "élodie@example.org"


def test_sqlite_round_trip_preserves_user_inputs():
    values = (
        "Élodie D’Œuvre",
        "12 rue de l’Église – Bâtiment Œ",
        "06.12.34.56.78",
        "élodie@example.org",
    )
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE coordonnees (nom TEXT, adresse TEXT, telephone TEXT, email TEXT)"
    )
    connection.execute("INSERT INTO coordonnees VALUES (?, ?, ?, ?)", values)
    loaded = connection.execute("SELECT nom, adresse, telephone, email FROM coordonnees").fetchone()
    assert loaded == values


def test_csv_utf8_round_trip_preserves_user_inputs():
    values = [
        "Élodie D’Œuvre",
        "12 rue de l’Église – Bâtiment Œ",
        "+33 6 12 34 56 78",
        "élodie@example.org",
    ]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";")
    writer.writerow(values)
    raw = stream.getvalue().encode("utf-8-sig")

    decoded = io.StringIO(raw.decode("utf-8-sig"), newline="")
    loaded = next(csv.reader(decoded, delimiter=";"))
    assert loaded == values
