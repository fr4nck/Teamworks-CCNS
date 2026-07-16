from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, Iterable


class ScopeKind(str, Enum):
    """Nature générique d'un périmètre métier."""

    GLOBAL = "global"
    PERSONAL = "personal"
    SERVICE = "service"
    SITE = "site"
    ACTIVITY = "activity"
    PERSON = "person"


@dataclass(frozen=True)
class ScopeAtom:
    """Brique élémentaire d'un périmètre métier.

    Un atome décrit une nature de périmètre et, lorsque cette nature cible des
    objets métier, les identifiants fonctionnels concernés. Les identifiants
    restent de simples chaînes pour éviter toute dépendance à la persistance ou
    à une interface.
    """

    kind: ScopeKind
    identifiers: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ScopeKind):
            raise ValueError("La nature du périmètre doit être un ScopeKind.")
        normalized = frozenset(_normalize_identifier(identifier) for identifier in self.identifiers)
        if self.kind in {ScopeKind.GLOBAL, ScopeKind.PERSONAL}:
            if normalized:
                raise ValueError("Un périmètre global ou personnel ne porte pas d'identifiant.")
        elif not normalized:
            raise ValueError("Un périmètre ciblé doit contenir au moins un identifiant.")
        object.__setattr__(self, "identifiers", normalized)

    @classmethod
    def global_scope(cls) -> "ScopeAtom":
        return cls(kind=ScopeKind.GLOBAL)

    @classmethod
    def personal(cls) -> "ScopeAtom":
        return cls(kind=ScopeKind.PERSONAL)

    @classmethod
    def targeted(cls, kind: ScopeKind, identifiers: Iterable[str]) -> "ScopeAtom":
        if kind in {ScopeKind.GLOBAL, ScopeKind.PERSONAL}:
            raise ValueError(
                "Les périmètres global et personnel doivent utiliser leurs constructeurs dédiés."
            )
        return cls(kind=kind, identifiers=frozenset(identifiers))

    def contains(self, other: "ScopeAtom") -> bool:
        if not isinstance(other, ScopeAtom):
            raise ValueError("La comparaison de périmètre attend un ScopeAtom.")
        if self.kind == ScopeKind.GLOBAL:
            return True
        if self.kind != other.kind:
            return False
        if self.kind == ScopeKind.PERSONAL:
            return True
        return other.identifiers.issubset(self.identifiers)

    def intersects(self, other: "ScopeAtom") -> bool:
        if not isinstance(other, ScopeAtom):
            raise ValueError("La comparaison de périmètre attend un ScopeAtom.")
        if self.kind == ScopeKind.GLOBAL or other.kind == ScopeKind.GLOBAL:
            return True
        if self.kind != other.kind:
            return False
        if self.kind == ScopeKind.PERSONAL:
            return True
        return bool(self.identifiers & other.identifiers)

    def merge(self, other: "ScopeAtom") -> "ScopeAtom":
        if not isinstance(other, ScopeAtom):
            raise ValueError("La fusion de périmètre attend un ScopeAtom.")
        if self.kind != other.kind:
            raise ValueError("Seuls deux atomes de même nature peuvent être fusionnés directement.")
        if self.kind in {ScopeKind.GLOBAL, ScopeKind.PERSONAL}:
            return self
        return ScopeAtom(kind=self.kind, identifiers=self.identifiers | other.identifiers)


@dataclass(frozen=True)
class Scope:
    """Périmètre métier sur lequel un compte exerce ses responsabilités."""

    atoms: tuple[ScopeAtom, ...]

    def __post_init__(self) -> None:
        atoms = tuple(self.atoms)
        if not atoms:
            raise ValueError("Un périmètre métier doit contenir au moins un atome.")
        if any(not isinstance(atom, ScopeAtom) for atom in atoms):
            raise ValueError("Un périmètre métier doit contenir uniquement des ScopeAtom.")
        object.__setattr__(self, "atoms", _merge_atoms_by_kind(atoms))

    @classmethod
    def global_scope(cls) -> "Scope":
        return cls((ScopeAtom.global_scope(),))

    @classmethod
    def personal(cls) -> "Scope":
        return cls((ScopeAtom.personal(),))

    @classmethod
    def for_targets(cls, kind: ScopeKind, identifiers: Iterable[str]) -> "Scope":
        return cls((ScopeAtom.targeted(kind, identifiers),))

    @classmethod
    def combine(cls, scopes: Iterable["Scope"]) -> "Scope":
        scopes_tuple = tuple(scopes)
        if not scopes_tuple:
            raise ValueError("La combinaison attend au moins un périmètre.")
        if any(not isinstance(scope, Scope) for scope in scopes_tuple):
            raise ValueError("La combinaison attend uniquement des Scope.")
        return cls(tuple(atom for scope in scopes_tuple for atom in scope.atoms))

    def contains(self, other: "Scope") -> bool:
        if not isinstance(other, Scope):
            raise ValueError("La comparaison de périmètre attend un Scope.")
        return all(any(atom.contains(searched) for atom in self.atoms) for searched in other.atoms)

    def intersects(self, other: "Scope") -> bool:
        if not isinstance(other, Scope):
            raise ValueError("La comparaison de périmètre attend un Scope.")
        return any(atom.intersects(candidate) for atom in self.atoms for candidate in other.atoms)

    def merge(self, other: "Scope") -> "Scope":
        if not isinstance(other, Scope):
            raise ValueError("La fusion de périmètre attend un Scope.")
        return Scope(self.atoms + other.atoms)

    def is_global(self) -> bool:
        return any(atom.kind == ScopeKind.GLOBAL for atom in self.atoms)

    def is_personal(self) -> bool:
        return len(self.atoms) == 1 and self.atoms[0].kind == ScopeKind.PERSONAL


def _merge_atoms_by_kind(atoms: tuple[ScopeAtom, ...]) -> tuple[ScopeAtom, ...]:
    merged: dict[ScopeKind, ScopeAtom] = {}
    for atom in atoms:
        existing = merged.get(atom.kind)
        merged[atom.kind] = atom if existing is None else existing.merge(atom)
    return tuple(merged.values())


def _normalize_identifier(identifier: str) -> str:
    if not isinstance(identifier, str):
        raise ValueError("Les identifiants de périmètre doivent être des chaînes.")
    normalized = identifier.strip()
    if not normalized:
        raise ValueError("Les identifiants de périmètre ne doivent pas être vides.")
    return normalized
