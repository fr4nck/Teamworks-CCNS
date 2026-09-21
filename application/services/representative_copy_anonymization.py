from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


ANONYMIZED_TEXT = "[ANONYMISE]"

_FIRST_NAMES = (
    "Élodie",
    "Maëlys",
    "Joël",
    "Anne-Sophie",
    "François",
    "Noémie",
    "Léna",
    "Yann",
)
_LAST_NAMES = (
    "Le Test",
    "D'Exemple",
    "Ker-Recette",
    "de La Démo",
    "L'Échantillon",
    "Martin-Test",
    "Durand-Recette",
    "Le Guen-Test",
)
_CITIES = (
    "Ville-Recette",
    "Saint-Test",
    "Ker-Démo",
    "Cité-Échantillon",
)


@dataclass(frozen=True)
class SyntheticIdentity:
    first_name: str
    last_name: str
    birth_name: str
    address: str
    postcode: int
    city: str
    email: str
    phone: str
    date_shift_days: int


def assert_safe_recipe_database_name(database: str, confirmation: str) -> None:
    database = str(database or "").strip()
    confirmation = str(confirmation or "").strip()
    if not database.endswith("_qt_vanilla_recette"):
        raise ValueError(
            "La base cible doit se terminer par '_qt_vanilla_recette'."
        )
    if database != confirmation:
        raise ValueError(
            "La confirmation du nom de base ne correspond pas exactement à la cible."
        )


def synthetic_identity(sequence: int) -> SyntheticIdentity:
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= 0:
        raise ValueError("La séquence synthétique doit être un entier positif.")

    first_name = _FIRST_NAMES[(sequence - 1) % len(_FIRST_NAMES)]
    last_name = _LAST_NAMES[(sequence - 1) % len(_LAST_NAMES)]
    city = _CITIES[(sequence - 1) % len(_CITIES)]

    # Décalage en semaines : les jours de la semaine restent identiques.
    week_shift = ((sequence * 17) % 89) - 44
    if week_shift == 0:
        week_shift = 1
    shift_days = week_shift * 7

    postcode = 90000 + (sequence % 999)
    return SyntheticIdentity(
        first_name=first_name,
        last_name=last_name,
        birth_name=f"{last_name}-NAISSANCE",
        address=f"{sequence} rue de la Recette",
        postcode=postcode,
        city=city,
        email=f"personne_{sequence:05d}@example.test",
        phone=f"00000{sequence % 100000:05d}",
        date_shift_days=shift_days,
    )


def shift_date(value: date | None, days: int) -> date | None:
    if value is None:
        return None
    return value + timedelta(days=days)


def anonymized_if_present(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return value
    return ANONYMIZED_TEXT


def synthetic_birth_date(
    value: date | None,
    sequence: int,
    *,
    reference_date: date | None = None,
) -> date | None:
    """Remplace une naissance par une date synthétique gardant le groupe d'âge.

    Les mineurs restent mineurs. Pour les adultes, l'âge est ramené au milieu
    d'une tranche de cinq ans. Le mois et le jour sont synthétiques.
    """

    if value is None:
        return None
    reference_date = reference_date or date.today()
    age = reference_date.year - value.year - (
        (reference_date.month, reference_date.day) < (value.month, value.day)
    )
    if age < 18:
        synthetic_age = max(0, age)
    else:
        synthetic_age = (age // 5) * 5 + 2

    year = reference_date.year - synthetic_age
    month = (sequence % 12) + 1
    day = ((sequence * 7) % 27) + 1
    candidate = date(year, month, day)
    if candidate > reference_date:
        candidate = date(year - 1, month, day)
    return candidate


def build_sequential_mapping(
    identifiers: list[int] | tuple[int, ...],
    *,
    start: int,
) -> dict[int, int]:
    """Crée un remappage dense sans conserver le lien original dans la sortie."""

    clean = sorted(
        {
            int(value)
            for value in identifiers
            if isinstance(value, int)
            and not isinstance(value, bool)
            and int(value) > 0
        }
    )
    return {old: start + index for index, old in enumerate(clean)}
