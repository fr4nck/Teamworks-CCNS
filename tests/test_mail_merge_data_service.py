from application.services.mail_merge_data import (
    build_legacy_mail_merge_batch,
    compose_mail_merge_record,
)


def test_compose_record_preserves_order_hides_private_keys_and_uses_rightmost_value() -> None:
    record = compose_mail_merge_record(
        (
            ("NOM", "_IDPERSONNE", "EMAILS"),
            {"NOM": "Martin", "_IDPERSONNE": 12, "EMAILS": "a@example.test"},
        ),
        (
            ("DATEDEBUT", "NOM"),
            {"DATEDEBUT": "01/09/2026", "NOM": "Martin contrat", "_SECRET": "x"},
        ),
    )

    assert record.keywords == ("NOM", "EMAILS", "DATEDEBUT", "NOM")
    assert record.values == {
        "NOM": "Martin contrat",
        "EMAILS": "a@example.test",
        "DATEDEBUT": "01/09/2026",
    }


def test_build_batch_keeps_the_historical_output_contract() -> None:
    calls = []

    def loader(category, record_id):
        calls.append((category, record_id))
        if record_id == 1:
            return ("NOM",), {"NOM": "A"}
        return ("NOM", "DATEDEBUT"), {"NOM": "B", "DATEDEBUT": "02/09/2026"}

    result = build_legacy_mail_merge_batch(
        category="contrat",
        record_ids=(1, 2),
        edition_name="NOM_PRENOM*1_DATEDEBUT_DATEFIN",
        loader=loader,
    )

    assert calls == [("contrat", 1), ("contrat", 2)]
    assert result["CATEGORIE"] == "contrat"
    assert result["NBREDOCUMENTS"] == 2
    assert result["NOMEDITION"] == "NOM_PRENOM*1_DATEDEBUT_DATEFIN"
    assert result[1] == {"NOM": "A"}
    assert result[2] == {"NOM": "B", "DATEDEBUT": "02/09/2026"}
    assert result["MOTSCLES"] == [("NOM", "base"), ("DATEDEBUT", "base")]


def test_build_empty_batch_has_no_keywords_and_does_not_call_loader() -> None:
    def loader(category, record_id):
        raise AssertionError("le loader ne doit pas être appelé")

    result = build_legacy_mail_merge_batch(
        category="contrat",
        record_ids=None,
        edition_name="NOM",
        loader=loader,
    )

    assert result == {
        "CATEGORIE": "contrat",
        "NBREDOCUMENTS": 0,
        "NOMEDITION": "NOM",
        "MOTSCLES": [],
    }
