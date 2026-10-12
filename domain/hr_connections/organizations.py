from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from urllib.parse import urlparse


class OrganizationKind(str, Enum):
    """Familles d'organismes ou portails RH externes."""

    URSSAF = "urssaf"
    NET_ENTREPRISES = "net_entreprises"
    MUTUELLE = "mutuelle"
    PREVOYANCE = "prevoyance"
    RETRAITE_COMPLEMENTAIRE = "retraite_complementaire"
    OPCO = "opco"
    SPST = "spst"
    FRANCE_TRAVAIL = "france_travail"
    OTHER = "other"


@dataclass(frozen=True)
class EffectivePeriod:
    """Période d'effet optionnelle d'une donnée RH."""

    starts_on: date | None = None
    ends_on: date | None = None

    def __post_init__(self) -> None:
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValueError("La date de fin ne peut pas précéder la date d'effet.")

    def includes(self, value: date) -> bool:
        if self.starts_on and value < self.starts_on:
            return False
        if self.ends_on and value > self.ends_on:
            return False
        return True


@dataclass(frozen=True)
class PortalLink:
    """Lien non secret vers un portail officiel ou métier."""

    url: str
    label: str

    def __post_init__(self) -> None:
        if not self.url.strip():
            raise ValueError("L'URL du portail est obligatoire.")
        if not self.label.strip():
            raise ValueError("Le libellé du portail est obligatoire.")

        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Le portail doit utiliser une URL HTTP ou HTTPS valide.")
        if parsed.username or parsed.password:
            raise ValueError("Les identifiants ne doivent pas être intégrés dans l'URL du portail.")

    @classmethod
    def create(cls, *, url: str, label: str) -> "PortalLink":
        return cls(url=url.strip(), label=label.strip())


_SENSITIVE_REFERENCE_TYPES = {
    "password",
    "mot_de_passe",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "cookie",
    "session",
    "api_key",
    "private_key",
}


def _normalize_reference_type(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


@dataclass(frozen=True)
class OrganizationReference:
    """Référence administrative non secrète liée à un organisme."""

    reference_type: str
    value: str
    label: str | None = None

    def __post_init__(self) -> None:
        reference_type = _normalize_reference_type(self.reference_type)
        if not reference_type:
            raise ValueError("Le type de référence est obligatoire.")
        if not self.value.strip():
            raise ValueError("La valeur de la référence est obligatoire.")
        if reference_type in _SENSITIVE_REFERENCE_TYPES:
            raise ValueError("Un secret ne peut pas être stocké comme référence d'organisme.")

    @classmethod
    def create(
        cls,
        *,
        reference_type: str,
        value: str,
        label: str | None = None,
    ) -> "OrganizationReference":
        normalized_label = label.strip() if label is not None else None
        return cls(
            reference_type=_normalize_reference_type(reference_type),
            value=value.strip(),
            label=normalized_label or None,
        )


@dataclass(frozen=True)
class HrOrganization:
    """Organisme RH externe identifié par un code stable."""

    code: str
    label: str
    kind: OrganizationKind

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Le code de l'organisme est obligatoire.")
        if not self.label.strip():
            raise ValueError("Le libellé de l'organisme est obligatoire.")
        if not isinstance(self.kind, OrganizationKind):
            raise TypeError("Le type d'organisme est invalide.")

    @classmethod
    def create(
        cls,
        *,
        code: str,
        label: str,
        kind: OrganizationKind,
    ) -> "HrOrganization":
        return cls(code=code.strip(), label=label.strip(), kind=kind)
