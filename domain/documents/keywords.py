from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable, Mapping


class KeywordContext(str, Enum):
    PERSON = "person"
    CANDIDATE = "candidate"
    APPLICATION = "application"
    CONTRACT = "contract"
    HR_DOCUMENT = "hr_document"


@dataclass(frozen=True)
class KeywordDefinition:
    name: str
    source: str
    contexts: frozenset[KeywordContext]


@dataclass(frozen=True)
class TemplateKeywordValidation:
    keywords: tuple[str, ...]
    unknown_keywords: tuple[str, ...]
    empty_known_keywords: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.unknown_keywords


_TOKEN_RE = re.compile(r"\{([A-Za-z0-9_]+)\}")


_PERSON_KEYWORDS = (
    "CIVILITE",
    "NOM",
    "NOMJFILLE",
    "PRENOM",
    "DATENAISS",
    "AGE",
    "CPNAISS",
    "VILLENAISS",
    "PAYSNAISS",
    "NATIONALITE",
    "NUMSECU",
    "ADRESSERESID",
    "CPRESID",
    "VILLERESID",
    "SITUATION",
    "TELEPHONES",
    "EMAILS",
    "FAX",
)

_CANDIDATE_KEYWORDS = (
    "CIVILITE",
    "NOM",
    "PRENOM",
    "DATENAISS",
    "AGE",
    "ADRESSERESID",
    "CPRESID",
    "VILLERESID",
    "TELEPHONES",
    "FAX",
    "EMAILS",
    "QUALIFICATIONS",
    "MEMO",
)

_APPLICATION_KEYWORDS = (
    "DATEDEPOT",
    "TYPEDEPOT",
    "OFFREDEMPLOI",
    "DISPONIBILITES",
    "FONCTIONS",
    "AFFECTATIONS",
    "DECISION",
    "DATEREPONSE",
    "TYPEREPONSE",
)

_CONTRACT_KEYWORDS = (
    "DATEDEBUT",
    "DATEFIN",
    "CLASSIFICATION",
    "TYPECONTRAT",
    "VALEURPOINT",
    "ESSAI",
    "CONVENTION",
    "GROUPECCNS",
    "QUALIFICATIONCEE",
    "DUREEHEBDO",
    "SALAIREBRUTMENSUEL",
    "MINIMUMCCNS",
    "MINIMUMSMIC",
    "MINIMUMRETENU",
    "CONFORMITEREMUNERATION",
    "BAREMECEE",
    "MINIMUMCEE",
    "BRUTJOUR",
)

_STRUCTURE_FIELDS = (
    "RAISON_SOCIALE",
    "NOM_USAGE",
    "ADRESSE",
    "CODE_POSTAL",
    "VILLE",
    "TELEPHONE",
    "EMAIL",
    "EMAIL_RH",
    "SITE_WEB",
    "RNA",
    "SIREN",
    "SIRET",
    "APE_NAF",
    "AGREMENT_JS",
    "AGREMENT_JS_DATE",
    "ASSUREUR",
    "POLICE_ASSURANCE",
    "ASSURANCE_ECHEANCE",
    "REPRESENTANT_LEGAL",
    "REPRESENTANT_FONCTION",
    "DECLARATION_PREFECTURE",
    "REFERENCE_JOAFE",
    "LOGO",
)

_EMPLOYEE_FIELDS = (
    "NOM",
    "PRENOM",
    "CIVILITE",
    "DATE_NAISSANCE",
    "ADRESSE",
    "CODE_POSTAL",
    "VILLE",
    "TELEPHONES",
    "EMAILS",
)

_CONTRACT_FIELDS = (
    "DATE_DEBUT",
    "DATE_FIN",
    "TYPE",
    "CLASSIFICATION",
    "CONVENTION",
    "GROUPE_CCNS",
    "DUREE_HEBDO",
    "SALAIRE_BRUT_MENSUEL",
)


def _build_default_catalog() -> tuple[KeywordDefinition, ...]:
    definitions: dict[str, KeywordDefinition] = {}

    def add(name: str, source: str, contexts: Iterable[KeywordContext]) -> None:
        current = definitions.get(name)
        context_set = frozenset(contexts)
        if current is None:
            definitions[name] = KeywordDefinition(name=name, source=source, contexts=context_set)
            return
        definitions[name] = KeywordDefinition(
            name=name,
            source=current.source,
            contexts=current.contexts | context_set,
        )

    for name in _PERSON_KEYWORDS:
        add(name, "legacy_person", (KeywordContext.PERSON, KeywordContext.CONTRACT))
    for name in _CANDIDATE_KEYWORDS:
        add(name, "legacy_candidate", (KeywordContext.CANDIDATE,))
    for name in _PERSON_KEYWORDS:
        add(name, "legacy_person", (KeywordContext.APPLICATION,))
    for name in _CANDIDATE_KEYWORDS:
        add(name, "legacy_candidate", (KeywordContext.APPLICATION,))
    for name in _APPLICATION_KEYWORDS:
        add(name, "legacy_application", (KeywordContext.APPLICATION,))
    for name in _CONTRACT_KEYWORDS:
        add(name, "legacy_contract", (KeywordContext.CONTRACT,))

    for field in _STRUCTURE_FIELDS:
        add(f"STRUCTURE_{field}", "structure", (KeywordContext.HR_DOCUMENT, KeywordContext.CONTRACT))
    for field in _EMPLOYEE_FIELDS:
        add(f"SALARIE_{field}", "employee", (KeywordContext.HR_DOCUMENT, KeywordContext.CONTRACT))
    for field in _CONTRACT_FIELDS:
        add(f"CONTRAT_{field}", "contract", (KeywordContext.HR_DOCUMENT, KeywordContext.CONTRACT))

    return tuple(definitions[name] for name in sorted(definitions))


DEFAULT_KEYWORD_CATALOG = _build_default_catalog()


def normalize_keyword(value: object) -> str:
    return str(value).strip().upper()


def known_keywords(
    *,
    context: KeywordContext | None = None,
    extra_keywords: Iterable[str] = (),
    catalog: Iterable[KeywordDefinition] = DEFAULT_KEYWORD_CATALOG,
) -> frozenset[str]:
    names = {
        item.name
        for item in catalog
        if context is None or context in item.contexts
    }
    names.update(
        normalized
        for normalized in (normalize_keyword(item) for item in extra_keywords)
        if normalized
    )
    return frozenset(names)


def extract_template_keywords(template_text: str) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for match in _TOKEN_RE.finditer(template_text or ""):
        name = normalize_keyword(match.group(1))
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return tuple(result)


def validate_template_keywords(
    template_text: str,
    values: Mapping[str, object] | None = None,
    *,
    context: KeywordContext | None = KeywordContext.HR_DOCUMENT,
    extra_keywords: Iterable[str] = (),
    catalog: Iterable[KeywordDefinition] = DEFAULT_KEYWORD_CATALOG,
) -> TemplateKeywordValidation:
    normalized_values = {
        normalize_keyword(key): value
        for key, value in (values or {}).items()
        if normalize_keyword(key)
    }
    known = known_keywords(
        context=context,
        extra_keywords=tuple(extra_keywords) + tuple(normalized_values),
        catalog=catalog,
    )
    keywords = extract_template_keywords(template_text)
    unknown = tuple(name for name in keywords if name not in known)
    empty_known = tuple(
        name
        for name in keywords
        if name in known and normalized_values.get(name, "") in (None, "")
    )
    return TemplateKeywordValidation(
        keywords=keywords,
        unknown_keywords=unknown,
        empty_known_keywords=empty_known,
    )


def render_text_template(
    template_text: str,
    values: Mapping[str, object] | None = None,
    *,
    context: KeywordContext | None = KeywordContext.HR_DOCUMENT,
    extra_keywords: Iterable[str] = (),
    catalog: Iterable[KeywordDefinition] = DEFAULT_KEYWORD_CATALOG,
) -> str:
    """Rend un gabarit texte selon le contrat de publipostage.

    Une clé connue mais absente devient vide. Une clé inconnue reste visible afin
    que la faute de modèle ne soit pas masquée. Ce rendu pur sert à la
    prévisualisation et aux tests ; il ne remplace pas l'intégration Office.
    """

    normalized_values = {
        normalize_keyword(key): value
        for key, value in (values or {}).items()
        if normalize_keyword(key)
    }
    known = known_keywords(
        context=context,
        extra_keywords=tuple(extra_keywords) + tuple(normalized_values),
        catalog=catalog,
    )

    def replace(match: re.Match[str]) -> str:
        name = normalize_keyword(match.group(1))
        if name not in known:
            return match.group(0)
        value = normalized_values.get(name, "")
        return "" if value is None else str(value)

    return _TOKEN_RE.sub(replace, template_text or "")
