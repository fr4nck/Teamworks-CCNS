import datetime
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
if str(TEAMWORKS) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS))

from Utils import UTILS_Mailing


def test_manual_addresses_accept_modern_domains_and_remove_duplicates():
    addresses = UTILS_Mailing.SplitEmailAddresses(
        "  direction@pmsl.association ; contact@example.technology\n"
        "DIRECTION@PMSL.ASSOCIATION, invalide@localhost ; sans-arobase"
    )

    assert addresses == [
        "direction@pmsl.association",
        "contact@example.technology",
    ]


def test_merge_fields_handles_dates_booleans_and_none():
    result = UTILS_Mailing.MergeFields(
        "Bonjour {PRENOM}, début {DATE}, actif={ACTIF}, note={NOTE}.",
        fields={
            "{PRENOM}": "Léa",
            "{DATE}": datetime.date(2026, 9, 1),
            "{ACTIF}": True,
            "{NOTE}": None,
        },
    )

    assert result == "Bonjour Léa, début 01/09/2026, actif=True, note=."
    assert UTILS_Mailing.FindUnresolvedKeywords(result) == []


def test_prepare_payload_does_not_mutate_or_duplicate_attachments():
    personal = ["contrat-lea.pdf"]
    common = ["reglement.pdf", "contrat-lea.pdf"]

    first = UTILS_Mailing.PreparePayload(
        " lea@example.fr ",
        "Rentrée",
        "Bonjour {PRENOM}",
        fields={"{PRENOM}": "Léa"},
        personal_attachments=personal,
        common_attachments=common,
    )
    second = UTILS_Mailing.PreparePayload(
        "lea@example.fr",
        "Rentrée",
        "Bonjour {PRENOM}",
        fields={"{PRENOM}": "Léa"},
        personal_attachments=personal,
        common_attachments=common,
    )

    assert personal == ["contrat-lea.pdf"]
    assert common == ["reglement.pdf", "contrat-lea.pdf"]
    assert first["fichiers"] == ["contrat-lea.pdf", "reglement.pdf"]
    assert second["fichiers"] == first["fichiers"]
    assert first["texte_html"] == "Bonjour Léa"
    assert first["motscles_non_resolus"] == []


def test_prepare_payload_reports_unresolved_keywords():
    payload = UTILS_Mailing.PreparePayload(
        "test@example.fr",
        "Objet",
        "Bonjour {PRENOM} {INCONNU} {INCONNU}",
        fields={"{PRENOM}": "Franck"},
    )

    assert payload["motscles_non_resolus"] == ["{INCONNU}"]


def test_backend_parameters_preserve_equal_signs_and_roundtrip():
    raw = "api_key==public==part##api_secret==secret=value"

    parsed = UTILS_Mailing.ParseBackendParameters(raw)

    assert parsed == {
        "api_key": "public==part",
        "api_secret": "secret=value",
    }
    assert UTILS_Mailing.SerializeBackendParameters(
        parsed,
        ordered_names=["api_key", "api_secret"],
    ) == raw


def test_backend_parameters_can_ignore_a_corrupt_fragment_for_recovery_ui():
    assert UTILS_Mailing.ParseBackendParameters(
        "api_key==abc##fragment-casse##api_secret==def",
        strict=False,
    ) == {"api_key": "abc", "api_secret": "def"}

    with pytest.raises(ValueError, match="Paramètre de messagerie invalide"):
        UTILS_Mailing.ParseBackendParameters(
            "api_key==abc##fragment-casse##api_secret==def",
            strict=True,
        )


def test_smtp_backend_configuration_is_normalized_before_network_access():
    config = UTILS_Mailing.ValidateBackendConfig(
        " SMTP ",
        " Direction@PMSL.Association ",
        host=" smtp.example.fr ",
        port="587",
        username="direction@example.fr",
        password="secret",
        use_tls=1,
    )

    assert config == {
        "backend": "smtp",
        "email_exp": "Direction@pmsl.association",
        "host": "smtp.example.fr",
        "port": 587,
        "username": "direction@example.fr",
        "password": "secret",
        "use_tls": True,
        "parameters": {},
    }


def test_smtp_backend_rejects_incoherent_credentials_and_port():
    with pytest.raises(ValueError, match="renseignés ensemble"):
        UTILS_Mailing.ValidateBackendConfig(
            "smtp",
            "direction@example.fr",
            host="smtp.example.fr",
            port=587,
            username="direction@example.fr",
            password=None,
        )

    with pytest.raises(ValueError, match="Port SMTP hors plage"):
        UTILS_Mailing.ValidateBackendConfig(
            "smtp",
            "direction@example.fr",
            host="smtp.example.fr",
            port=70000,
        )


def test_mailjet_backend_requires_complete_keys_before_network_access():
    config = UTILS_Mailing.ValidateBackendConfig(
        "mailjet",
        "direction@example.fr",
        parameters="api_key==public##api_secret==secret==suffix",
    )
    assert config["parameters"] == {
        "api_key": "public",
        "api_secret": "secret==suffix",
    }

    with pytest.raises(ValueError, match="clés API Mailjet"):
        UTILS_Mailing.ValidateBackendConfig(
            "mailjet",
            "direction@example.fr",
            parameters="api_key==public##api_secret==   ",
        )


def test_unknown_backend_and_invalid_sender_are_rejected_explicitly():
    with pytest.raises(ValueError, match="Backend de messagerie inconnu"):
        UTILS_Mailing.ValidateBackendConfig(
            "exchange",
            "direction@example.fr",
        )

    with pytest.raises(ValueError, match="Adresse d'expédition invalide"):
        UTILS_Mailing.ValidateBackendConfig(
            "smtp",
            "direction@localhost",
            host="smtp.example.fr",
        )
