from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

_FIELD_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class FieldValueType(str, Enum):
    TEXT = "text"
    DATE = "date"
    NUMBER = "number"
    BOOLEAN = "boolean"


class FieldStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class MergeField:
    key: str
    label: str
    owner_domain: str
    source_of_truth: str
    category: str
    value_type: FieldValueType = FieldValueType.TEXT
    description: str = ""
    contexts: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    legacy_tokens: tuple[str, ...] = ()
    resolver_id: str = ""
    status: FieldStatus = FieldStatus.ACTIVE

    def __post_init__(self) -> None:
        normalized = self.key.strip().upper()
        if not _FIELD_KEY_RE.match(normalized):
            raise ValueError(f"Invalid canonical merge-field key: {self.key!r}")
        object.__setattr__(self, "key", normalized)
        if not self.owner_domain.strip():
            raise ValueError(f"Merge field {normalized} has no owner_domain")
        if not self.source_of_truth.strip():
            raise ValueError(f"Merge field {normalized} has no source_of_truth")

    def all_identifiers(self) -> tuple[str, ...]:
        return (self.key,) + tuple(alias.strip().upper() for alias in self.aliases)

    def all_legacy_tokens(self) -> tuple[str, ...]:
        return tuple(self.legacy_tokens or ("{%s}" % self.key,))


class MergeFieldRegistry:
    def __init__(self, fields: Iterable[MergeField] = ()) -> None:
        self._by_key: dict[str, MergeField] = {}
        self._by_identifier: dict[str, MergeField] = {}
        self._by_legacy_token: dict[str, MergeField] = {}
        for merge_field in fields:
            self.register(merge_field)

    def register(self, merge_field: MergeField) -> None:
        if merge_field.key in self._by_key:
            raise ValueError(f"Duplicate canonical merge-field key: {merge_field.key}")
        for identifier in merge_field.all_identifiers():
            existing = self._by_identifier.get(identifier)
            if existing is not None:
                raise ValueError(f"Duplicate merge-field identifier {identifier}: {existing.key} vs {merge_field.key}")
        for token in merge_field.all_legacy_tokens():
            existing = self._by_legacy_token.get(token)
            if existing is not None:
                raise ValueError(f"Duplicate legacy merge token {token}: {existing.key} vs {merge_field.key}")
        self._by_key[merge_field.key] = merge_field
        for identifier in merge_field.all_identifiers():
            self._by_identifier[identifier] = merge_field
        for token in merge_field.all_legacy_tokens():
            self._by_legacy_token[token] = merge_field

    def get(self, key_or_alias: str) -> MergeField | None:
        return self._by_identifier.get(str(key_or_alias).strip().upper())

    def get_by_legacy_token(self, token: str) -> MergeField | None:
        return self._by_legacy_token.get(token)

    def canonical_key(self, key_or_alias: str) -> str | None:
        field = self.get(key_or_alias)
        return field.key if field else None

    def list_fields(self, *, context: str | None = None) -> tuple[MergeField, ...]:
        fields = tuple(self._by_key.values())
        return fields if context is None else tuple(field for field in fields if context in field.contexts)

    def __contains__(self, key_or_alias: object) -> bool:
        return isinstance(key_or_alias, str) and self.get(key_or_alias) is not None


def _rh_field(key: str, label: str, category: str, resolver: str, *, aliases: tuple[str, ...], contexts: tuple[str, ...], value_type: FieldValueType = FieldValueType.TEXT, extra_tokens: tuple[str, ...] = ()) -> MergeField:
    legacy_tokens = tuple("{%s}" % alias for alias in aliases) + extra_tokens + ("{%s}" % key,)
    return MergeField(key=key, label=label, owner_domain="rh", source_of_truth="Teamworks-CCNS", category=category, value_type=value_type, aliases=aliases, legacy_tokens=legacy_tokens, resolver_id=resolver, contexts=contexts)


_EMPLOYEE = ("employee", "contract")
_CONTRACT = ("contract",)
DEFAULT_DOCUMENT_FIELD_REGISTRY = MergeFieldRegistry((
    _rh_field("SALARIE_NOM", "Nom du salarié", "salarie", "rh.employee.last_name", aliases=("NOM",), contexts=_EMPLOYEE),
    _rh_field("SALARIE_PRENOM", "Prénom du salarié", "salarie", "rh.employee.first_name", aliases=("PRENOM",), contexts=_EMPLOYEE),
    _rh_field("SALARIE_CIVILITE", "Civilité du salarié", "salarie", "rh.employee.civility", aliases=("CIVILITE",), contexts=_EMPLOYEE),
    _rh_field("SALARIE_DATE_NAISSANCE", "Date de naissance", "salarie", "rh.employee.birth_date", aliases=("DATENAISS",), contexts=_EMPLOYEE, value_type=FieldValueType.DATE),
    _rh_field("SALARIE_ADRESSE", "Adresse du salarié", "salarie", "rh.employee.address", aliases=("ADRESSERESID",), contexts=_EMPLOYEE),
    _rh_field("SALARIE_CODE_POSTAL", "Code postal du salarié", "salarie", "rh.employee.postal_code", aliases=("CPRESID",), contexts=_EMPLOYEE),
    _rh_field("SALARIE_VILLE", "Ville du salarié", "salarie", "rh.employee.city", aliases=("VILLERESID",), contexts=_EMPLOYEE),
    _rh_field("SALARIE_TELEPHONES", "Téléphones du salarié", "salarie", "rh.employee.phones", aliases=("TELEPHONES",), contexts=_EMPLOYEE),
    _rh_field("SALARIE_EMAILS", "Emails du salarié", "salarie", "rh.employee.emails", aliases=("EMAILS",), contexts=_EMPLOYEE),
    _rh_field("CONTRAT_DATE_DEBUT", "Date de début du contrat", "contrat", "rh.contract.start_date", aliases=("DATEDEBUT", "DATE_DEBUT"), contexts=_CONTRACT, value_type=FieldValueType.DATE),
    _rh_field("CONTRAT_DATE_FIN", "Date de fin du contrat", "contrat", "rh.contract.end_date", aliases=("DATEFIN",), contexts=_CONTRACT, value_type=FieldValueType.DATE),
    _rh_field("CONTRAT_TYPE", "Type de contrat", "contrat", "rh.contract.type", aliases=("TYPECONTRAT",), contexts=_CONTRACT),
    _rh_field("CONTRAT_CLASSIFICATION", "Classification", "contrat", "rh.contract.classification", aliases=("CLASSIFICATION",), contexts=_CONTRACT),
    _rh_field("CONTRAT_CONVENTION", "Convention collective", "contrat", "rh.contract.convention", aliases=("CONVENTION",), contexts=_CONTRACT),
    _rh_field("CONTRAT_GROUPE_CCNS", "Groupe CCNS", "contrat", "rh.contract.ccns_group", aliases=("GROUPECCNS",), contexts=_CONTRACT),
    _rh_field("CONTRAT_DUREE_HEBDO", "Durée hebdomadaire", "contrat", "rh.contract.weekly_duration", aliases=("DUREEHEBDO",), contexts=_CONTRACT),
    _rh_field("CONTRAT_SALAIRE_BRUT_MENSUEL", "Salaire brut mensuel", "contrat", "rh.contract.monthly_gross_salary", aliases=("SALAIREBRUTMENSUEL",), contexts=_CONTRACT, value_type=FieldValueType.NUMBER),
))
