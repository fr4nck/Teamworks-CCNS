"""Toolkit-independent validation and transactional update for employee details.

The first usable Qt write path covers identity, address and memo only.
It deliberately excludes social-security numbers, linked reference tables,
birth dates and related employee records.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PersonDetails:
    last_name: str
    first_name: str
    address: str | None
    postcode: int | str | None
    city: str | None
    memo: str | None


@dataclass(frozen=True)
class PersonDetailsSnapshot:
    person_id: int
    details: PersonDetails


@dataclass(frozen=True)
class PersonDetailsResult:
    ok: bool
    code: str
    message: str
    committed: bool = False
    verified: bool = False
    value: PersonDetailsSnapshot | None = None


class PersonDetailsPort(Protocol):
    def load(self, person_id: int) -> PersonDetailsSnapshot | None: ...
    def update_if_unchanged(
        self, previous: PersonDetailsSnapshot, next_details: PersonDetails
    ) -> int: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


def _optional_text(value: str | None, maximum: int, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(label + " invalide.")
    value = value.strip()
    if len(value) > maximum or "\x00" in value:
        raise ValueError(label + " invalide ou trop long.")
    return value or None


def validate_person_details(
    *, last_name: str, first_name: str, address: str | None,
    postcode: str | int | None, city: str | None, memo: str | None,
) -> PersonDetails:
    """Validate before any SQL, preserving the historical integer postcode."""
    last_name = _optional_text(last_name, 100, "Nom")
    first_name = _optional_text(first_name, 100, "Prénom")
    if not last_name or not first_name:
        raise ValueError("Le nom et le prénom sont obligatoires.")
    if any("\n" in value or "\r" in value for value in (last_name, first_name)):
        raise ValueError("Nom ou prénom invalide.")
    address = _optional_text(address, 200, "Adresse")
    city = _optional_text(city, 100, "Ville")
    memo = _optional_text(memo, 800, "Mémo")
    if postcode is None or str(postcode).strip() == "":
        normalized_postcode = None
    else:
        postcode_text = str(postcode).strip()
        if not postcode_text.isascii() or not postcode_text.isdigit() or len(postcode_text) != 5:
            raise ValueError("Le code postal doit contenir cinq chiffres.")
        normalized_postcode = int(postcode_text)
    return PersonDetails(
        last_name=last_name, first_name=first_name,
        address=address, postcode=normalized_postcode,
        city=city, memo=memo,
    )


def save_person_details(
    port: PersonDetailsPort, previous: PersonDetailsSnapshot,
    updated: PersonDetails,
) -> PersonDetailsResult:
    """Commit exactly one optimistic update, then independently re-read it.

    A changed record is refused instead of overwriting somebody else's edits.
    A failed read after commit is explicitly reported as committed-but-unverified.
    """
    person_id = previous.person_id
    if type(person_id) is not int or person_id <= 0:
        return PersonDetailsResult(False, "INVALID_ID", "Identifiant salarié invalide.")
    try:
        current = port.load(person_id)
    except Exception:
        return PersonDetailsResult(False, "READ_ERROR", "Lecture de la fiche impossible.")
    if current is None:
        return PersonDetailsResult(False, "NOT_FOUND", "La fiche n'existe plus.")
    if current != previous:
        return PersonDetailsResult(False, "CONFLICT", "La fiche a été modifiée ailleurs. Rechargez-la.")
    if current.details == updated:
        return PersonDetailsResult(True, "UNCHANGED", "Aucune modification à enregistrer.", value=current, verified=True)

    try:
        affected = port.update_if_unchanged(previous, updated)
        if affected != 1:
            port.rollback()
            return PersonDetailsResult(False, "CONFLICT", "La fiche a changé pendant l'enregistrement.")
        port.commit()
    except Exception:
        try:
            port.rollback()
        except Exception:
            pass
        return PersonDetailsResult(False, "WRITE_ERROR", "Enregistrement impossible. Vérifiez la connexion.")

    try:
        refreshed = port.load(person_id)
    except Exception:
        return PersonDetailsResult(
            False, "READBACK_ERROR",
            "Enregistrement validé, mais relecture impossible.",
            committed=True,
        )
    if refreshed is None or refreshed.details != updated:
        return PersonDetailsResult(
            False, "READBACK_MISMATCH",
            "Enregistrement validé, mais confirmation des données impossible.",
            committed=True,
            value=refreshed,
        )
    return PersonDetailsResult(
        True, "OK", "Fiche enregistrée et relue.",
        committed=True, verified=True, value=refreshed,
    )
