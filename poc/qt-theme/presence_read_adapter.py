from __future__ import annotations

from presence_projection import project_presences


class PresenceReadAdapter:
    """Projection lecture seule des présences historiques, sans dépendance UI Qt.

    L'adaptateur reste volontairement composable : il reçoit un activity reader
    déjà géré par l'appelant et ne prend donc pas en charge son cycle de vie.
    """

    def __init__(self, activity_reader):
        self._activity_reader = activity_reader

    def list_presences(self, person_id: str | int):
        historical_id = _require_historical_id(person_id)
        presences = self._activity_reader.lire_presences_personne(historical_id)
        categories = self._activity_reader.lire_categories_presences()
        vacations = self._activity_reader.lire_periodes_vacances()
        return project_presences(presences, categories, vacations)


def _require_historical_id(value) -> int:
    if value is None or isinstance(value, bool):
        raise ValueError("IDpersonne historique obligatoire pour la lecture des présences")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("IDpersonne historique invalide") from exc
    if result <= 0:
        raise ValueError("IDpersonne historique invalide")
    return result
