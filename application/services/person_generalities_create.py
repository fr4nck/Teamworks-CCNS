"""Create the first minimal Teamworks person record without a GUI dependency.

This operation creates only identity, postal address and memo. It does not
silently create a social-security number, nationality, contract or linked data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from application.services.person_generalities_write import (
    PersonDetails,
    PersonDetailsSnapshot,
    validate_person_details,
)


class PersonCreationPort(Protocol):
    def insert(self, details: PersonDetails) -> int: ...
    def load(self, person_id: int) -> PersonDetailsSnapshot | None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


@dataclass(frozen=True)
class PersonCreationResult:
    ok: bool
    code: str
    message: str
    committed: bool = False
    verified: bool = False
    value: PersonDetailsSnapshot | None = None


def create_person_details(
    port: PersonCreationPort, details: PersonDetails
) -> PersonCreationResult:
    """Validate, insert once, commit once, then read back the inserted row.

    No SQL or commit on invalid input. If confirmation after commit fails,
    return the assigned identifier without suggesting a second creation.
    """
    try:
        if not isinstance(details, PersonDetails):
            raise ValueError("Fiche invalide.")
        postal = details.postcode
        if type(postal) is int and 0 <= postal <= 99999:
            postal = str(postal).zfill(5)
        normalized = validate_person_details(
            last_name=details.last_name,
            first_name=details.first_name,
            address=details.address,
            postcode=postal,
            city=details.city,
            memo=details.memo,
        )
    except ValueError:
        return PersonCreationResult(
            False, "INVALID_FIELDS",
            "Vérifiez le nom, le prénom et les coordonnées avant l'enregistrement.",
        )

    try:
        person_id = port.insert(normalized)
        if type(person_id) is not int or person_id <= 0:
            raise RuntimeError("Identifiant attribué invalide")
        port.commit()
    except Exception:
        try:
            port.rollback()
        except Exception:
            pass
        return PersonCreationResult(
            False, "WRITE_UNCONFIRMED",
            "Création non confirmée. Vérifiez la liste avant de réessayer.",
        )

    try:
        refreshed = port.load(person_id)
    except Exception:
        return PersonCreationResult(
            False, "READBACK_ERROR",
            "Fiche créée (n°%d), mais relecture impossible. Ne la recréez pas." % person_id,
            committed=True,
        )

    if refreshed is None or refreshed.details != normalized:
        return PersonCreationResult(
            False, "READBACK_MISMATCH",
            "Fiche créée (n°%d), mais données non confirmées. Ne la recréez pas." % person_id,
            committed=True,
            value=refreshed,
        )

    return PersonCreationResult(
        True, "OK", "Fiche n°%d créée et vérifiée." % person_id,
        committed=True, verified=True, value=refreshed,
    )
