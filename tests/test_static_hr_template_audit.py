from pathlib import Path

from domain.documents import (
    KeywordContext,
    audit_template_directory,
)


ROOT = Path(__file__).resolve().parents[1]
STATIC_DOCUMENTS = ROOT / "teamworks" / "Static" / "Documents"

# Les modèles historiques distribués contiennent déjà ces deux champs de contrat
# non préconfigurés. Ils restent tolérés pour compatibilité mais doivent rester
# visibles comme dette documentaire jusqu'à décision de migration du modèle.
_ALLOWED_UNKNOWN_BY_STEM = {
    "Contrat d'engagement éducatif - Exemple": {"NBREJOURS", "REPARTITION"},
    "Contrat à durée déterminée - Exemple": {"NBREJOURS", "REPARTITION"},
}


def test_all_bundled_templates_are_statically_readable() -> None:
    audits = audit_template_directory(
        STATIC_DOCUMENTS,
        context=KeywordContext.CONTRACT,
    )

    assert audits
    unreadable = {
        audit.path.name: audit.error
        for audit in audits
        if not audit.readable
    }
    assert unreadable == {}


def test_bundled_templates_do_not_introduce_untracked_unknown_keywords() -> None:
    audits = audit_template_directory(
        STATIC_DOCUMENTS,
        context=KeywordContext.CONTRACT,
    )

    unexpected = {}
    for audit in audits:
        allowed = _ALLOWED_UNKNOWN_BY_STEM.get(audit.path.stem, set())
        current = set(audit.unknown_keywords)
        extra = current - allowed
        if extra:
            unexpected[audit.path.name] = sorted(extra)

    assert unexpected == {}


def test_known_legacy_unknown_keywords_are_still_detected_in_twd_contract_examples() -> None:
    audits = {
        audit.path.name: audit
        for audit in audit_template_directory(
            STATIC_DOCUMENTS,
            context=KeywordContext.CONTRACT,
        )
    }

    for filename in (
        "Contrat d'engagement éducatif - Exemple.twd",
        "Contrat à durée déterminée - Exemple.twd",
    ):
        assert set(audits[filename].unknown_keywords) == {"NBREJOURS", "REPARTITION"}


def test_brutjour_is_flagged_as_flow_restricted_when_present() -> None:
    audits = audit_template_directory(
        STATIC_DOCUMENTS,
        context=KeywordContext.CONTRACT,
    )

    flagged = {
        audit.path.name
        for audit in audits
        if "BRUTJOUR" in audit.restricted_keywords
    }

    assert "Contrat d'engagement éducatif - Exemple.twd" in flagged
    assert "Contrat à durée déterminée - Exemple.twd" in flagged
