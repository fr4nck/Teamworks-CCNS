from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable

from .responsibility import Responsibility
from .workspace import Workspace


@dataclass(frozen=True)
class Role:
    """Fonction métier et responsabilités associées.

    Le rôle décrit ce qu'une personne peut accomplir dans Teamworks. Les contrôles
    d'accès aux données restent à appliquer dans la couche applicative selon le
    périmètre concerné (salarié, ALSH, sport ou association entière).
    """

    code: str
    label: str
    workspace: Workspace
    responsibilities: FrozenSet[Responsibility] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Le code du rôle est obligatoire.")
        if not self.label.strip():
            raise ValueError("Le libellé du rôle est obligatoire.")

    @classmethod
    def create(
        cls,
        *,
        code: str,
        label: str,
        workspace: Workspace,
        responsibilities: Iterable[Responsibility] = (),
    ) -> "Role":
        return cls(
            code=code.strip(),
            label=label.strip(),
            workspace=workspace,
            responsibilities=frozenset(responsibilities),
        )

    def can(self, responsibility: Responsibility) -> bool:
        return responsibility in self.responsibilities
