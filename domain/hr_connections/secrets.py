from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, Iterable, Protocol, Tuple


class SecretKind(str, Enum):
    """Nature d'un secret nécessaire à un connecteur externe."""

    PASSWORD = "password"
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    API_KEY = "api_key"
    CLIENT_SECRET = "client_secret"
    PRIVATE_KEY = "private_key"
    CERTIFICATE = "certificate"
    OTHER = "other"


@dataclass(frozen=True)
class SecretHandle:
    """Référence opaque vers un secret stocké hors des données métier.

    Le handle identifie un emplacement dans un coffre ou un backend système. Il ne
    contient jamais la valeur du secret et doit pouvoir être journalisé sans révéler
    le credential lui-même.
    """

    store_key: str
    kind: SecretKind

    def __post_init__(self) -> None:
        if not self.store_key.strip():
            raise ValueError("La clé du secret est obligatoire.")
        if not isinstance(self.kind, SecretKind):
            raise TypeError("La nature du secret est invalide.")
        if any(character.isspace() for character in self.store_key):
            raise ValueError("La clé du secret ne doit pas contenir d'espace.")

    @classmethod
    def create(cls, *, store_key: str, kind: SecretKind) -> "SecretHandle":
        return cls(store_key=store_key.strip(), kind=kind)


@dataclass(frozen=True)
class CredentialRequirement:
    """Credential requis par un connecteur, sans valeur secrète."""

    code: str
    label: str
    kind: SecretKind
    required: bool = True

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Le code du credential requis est obligatoire.")
        if not self.label.strip():
            raise ValueError("Le libellé du credential requis est obligatoire.")
        if not isinstance(self.kind, SecretKind):
            raise TypeError("La nature du credential requis est invalide.")
        if not isinstance(self.required, bool):
            raise TypeError("Le caractère obligatoire du credential doit être booléen.")

    @classmethod
    def create(
        cls,
        *,
        code: str,
        label: str,
        kind: SecretKind,
        required: bool = True,
    ) -> "CredentialRequirement":
        return cls(
            code=code.strip(),
            label=label.strip(),
            kind=kind,
            required=required,
        )


@dataclass(frozen=True)
class CredentialBinding:
    """Association entre un besoin de credential et un handle opaque."""

    requirement_code: str
    secret_handle: SecretHandle

    def __post_init__(self) -> None:
        if not self.requirement_code.strip():
            raise ValueError("Le code du credential associé est obligatoire.")
        if not isinstance(self.secret_handle, SecretHandle):
            raise TypeError("La référence du secret associé est invalide.")

    @classmethod
    def create(
        cls,
        *,
        requirement_code: str,
        secret_handle: SecretHandle,
    ) -> "CredentialBinding":
        return cls(
            requirement_code=requirement_code.strip(),
            secret_handle=secret_handle,
        )


@dataclass(frozen=True)
class ConnectorCredentialProfile:
    """Configuration de credentials d'un connecteur, composée uniquement de handles."""

    connector_id: str
    requirements: Tuple[CredentialRequirement, ...] = field(default_factory=tuple)
    bindings: Tuple[CredentialBinding, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.connector_id.strip():
            raise ValueError("L'identifiant du connecteur est obligatoire.")
        if any(not isinstance(item, CredentialRequirement) for item in self.requirements):
            raise TypeError("La liste des credentials requis est invalide.")
        if any(not isinstance(item, CredentialBinding) for item in self.bindings):
            raise TypeError("La liste des associations de secrets est invalide.")

        requirement_codes = tuple(item.code for item in self.requirements)
        if len(requirement_codes) != len(set(requirement_codes)):
            raise ValueError("Deux credentials requis ne peuvent pas partager le même code.")

        binding_codes = tuple(item.requirement_code for item in self.bindings)
        if len(binding_codes) != len(set(binding_codes)):
            raise ValueError("Un credential ne peut pas être associé à plusieurs secrets.")

        requirements_by_code = {item.code: item for item in self.requirements}
        for binding in self.bindings:
            requirement = requirements_by_code.get(binding.requirement_code)
            if requirement is None:
                raise ValueError(
                    f"Le credential '{binding.requirement_code}' n'est pas déclaré par le connecteur."
                )
            if requirement.kind is not binding.secret_handle.kind:
                raise ValueError(
                    f"Le secret associé à '{binding.requirement_code}' n'a pas la nature attendue."
                )

    @classmethod
    def create(
        cls,
        *,
        connector_id: str,
        requirements: Iterable[CredentialRequirement] = (),
        bindings: Iterable[CredentialBinding] = (),
    ) -> "ConnectorCredentialProfile":
        return cls(
            connector_id=connector_id.strip(),
            requirements=tuple(requirements),
            bindings=tuple(bindings),
        )

    @property
    def bound_requirement_codes(self) -> FrozenSet[str]:
        return frozenset(binding.requirement_code for binding in self.bindings)

    @property
    def missing_required_codes(self) -> FrozenSet[str]:
        bound = self.bound_requirement_codes
        return frozenset(
            requirement.code
            for requirement in self.requirements
            if requirement.required and requirement.code not in bound
        )

    @property
    def is_bound(self) -> bool:
        """Indique seulement si tous les handles obligatoires sont configurés.

        Cette propriété ne garantit pas que les secrets existent réellement dans le
        coffre ni qu'ils sont valides auprès du service externe.
        """

        return not self.missing_required_codes


class SecretStore(Protocol):
    """Contrat minimal d'un coffre à secrets sans exposition de valeur en clair.

    À ce stade, le domaine ne demande qu'une vérification de disponibilité. La
    lecture, l'écriture et le renouvellement des valeurs secrètes seront définis au
    niveau infrastructure lorsqu'un connecteur officiel en aura réellement besoin.
    """

    def is_available(self, handle: SecretHandle) -> bool:
        ...


def unavailable_secret_handles(
    profile: ConnectorCredentialProfile,
    secret_store: SecretStore,
) -> Tuple[SecretHandle, ...]:
    """Retourne les handles configurés mais absents du coffre, sans lire leur valeur."""

    if not isinstance(profile, ConnectorCredentialProfile):
        raise TypeError("Le profil de credentials est invalide.")

    missing = []
    for binding in profile.bindings:
        if not secret_store.is_available(binding.secret_handle):
            missing.append(binding.secret_handle)
    return tuple(missing)
