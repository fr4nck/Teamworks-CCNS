from collections import defaultdict
from pathlib import Path

from domain.documents import (
    KeywordContext,
    audit_template_file,
)


ROOT = Path(__file__).resolve().parents[1]
STATIC_DOCUMENTS = ROOT / "teamworks" / "Static" / "Documents"

_CONTEXT_BY_STEM = {
    "Autorisation parentale mineurs - Exemple": KeywordContext.PERSON,
    "Certificat de travail - Exemple": KeywordContext.CONTRACT,
    "Confirmation d'embauche - Exemple": KeywordContext.CONTRACT,
    "Contrat d'engagement éducatif - Exemple": KeywordContext.CONTRACT,
    "Contrat à durée déterminée - Exemple": KeywordContext.CONTRACT,
    "Fiche candidature animateur - Exemple": KeywordContext.CANDIDATE,
    "Fiche renseignements salarié - Exemple": KeywordContext.PERSON,
    "Invitation réunion - Exemple": KeywordContext.PERSON,
    "Lettre de refus - Exemple": KeywordContext.APPLICATION,
}

# Dette historique explicitement connue : ces champs ne sont pas préconfigurés
# par le moteur. La liste est volontairement étroite pour qu'une nouvelle balise
# inconnue casse le garde-fou.
_ALLOWED_UNKNOWN_BY_STEM = {
    "Contrat d'engagement éducatif - Exemple": {"NBREJOURS", "REPARTITION"},
    "Contrat à durée déterminée - Exemple": {"NBREJOURS", "REPARTITION"},
    # Le modèle porte un nom Salarié mais utilise une donnée disponible
    # uniquement dans le contexte Candidat du moteur historique.
    "Fiche renseignements salarié - Exemple": {"QUALIFICATIONS"},
}


def _template_files():
    return sorted(
        path
        for path in STATIC_DOCUMENTS.iterdir()
        if path.is_file() and path.suffix.lower() in {".twd", ".odt", ".doc"}
    )


def _audits():
    return [
        audit_template_file(
            path,
            context=_CONTEXT_BY_STEM[path.stem],
        )
        for path in _template_files()
    ]


def test_all_bundled_templates_have_a_declared_context() -> None:
    stems = {path.stem for path in _template_files()}
    assert stems == set(_CONTEXT_BY_STEM)


def test_all_bundled_templates_are_statically_readable() -> None:
    audits = _audits()

    assert audits
    unreadable = {
        audit.path.name: audit.error
        for audit in audits
        if not audit.readable
    }
    assert unreadable == {}


def test_bundled_templates_do_not_introduce_untracked_unknown_keywords() -> None:
    unexpected = {}
    for audit in _audits():
        allowed = _ALLOWED_UNKNOWN_BY_STEM.get(audit.path.stem, set())
        extra = set(audit.unknown_keywords) - allowed
        if extra:
            unexpected[audit.path.name] = sorted(extra)

    assert unexpected == {}


def test_employee_information_template_exposes_candidate_only_qualification_keyword() -> None:
    audits = {audit.path.name: audit for audit in _audits()}

    for filename in (
        "Fiche renseignements salarié - Exemple.doc",
        "Fiche renseignements salarié - Exemple.odt",
    ):
        assert "QUALIFICATIONS" in audits[filename].unknown_keywords


def test_known_legacy_unknown_keywords_are_still_detected_in_contract_examples() -> None:
    audits = {audit.path.name: audit for audit in _audits()}

    for filename in (
        "Contrat d'engagement éducatif - Exemple.twd",
        "Contrat à durée déterminée - Exemple.twd",
    ):
        assert set(audits[filename].unknown_keywords) == {"NBREJOURS", "REPARTITION"}


def test_brutjour_is_flagged_as_flow_restricted_when_present() -> None:
    flagged = {
        audit.path.name
        for audit in _audits()
        if "BRUTJOUR" in audit.restricted_keywords
    }

    assert "Contrat d'engagement éducatif - Exemple.twd" in flagged
    assert "Contrat à durée déterminée - Exemple.twd" in flagged


def test_twd_and_odt_variants_share_the_same_keyword_contract() -> None:
    """Les deux moteurs lisibles exactement ne doivent pas dériver silencieusement."""

    by_stem = defaultdict(dict)
    for audit in _audits():
        by_stem[audit.path.stem][audit.path.suffix.lower()] = set(audit.keywords)

    mismatches = {}
    for stem, variants in by_stem.items():
        if ".twd" not in variants or ".odt" not in variants:
            continue
        if variants[".twd"] != variants[".odt"]:
            mismatches[stem] = {
                "twd_only": sorted(variants[".twd"] - variants[".odt"]),
                "odt_only": sorted(variants[".odt"] - variants[".twd"]),
            }

    assert mismatches == {}
