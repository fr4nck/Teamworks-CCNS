import datetime
from pathlib import Path
import sys


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
