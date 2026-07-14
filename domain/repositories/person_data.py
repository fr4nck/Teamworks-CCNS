#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PersonIdentityRecord:
    """Identité minimale utilisée par les listes de sélection historiques."""

    IDpersonne: int
    nom: str
    prenom: str

    def __iter__(self):
        # Compatibilité avec les écrans historiques qui dépaquettent les tuples SQL.
        yield self.IDpersonne
        yield self.nom
        yield self.prenom


class PersonReaderProtocol(Protocol):
    def lire_identites(self) -> list[PersonIdentityRecord]:
        ...
