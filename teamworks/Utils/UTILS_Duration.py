"""Adaptateurs wx/historique vers le métier commun des horaires et durées.

Aucune règle de calcul n'est définie ici : ce module adapte seulement les formats
historiques attendus par Teamworks wx.
"""

from __future__ import annotations

from domain.common.duration import calculate_time_difference, operate_signed_durations


def _format_wx_signed_minutes(value_minutes):
    """Retourne le format historique wx avec signe '+' explicite."""
    sign = "+" if value_minutes >= 0 else "-"
    hours, minutes = divmod(abs(value_minutes), 60)
    return "%s%d:%02d" % (sign, hours, minutes)


def operation_heures_wx(heureA=None, heureB=None, operation="addition"):
    """Compatibilité stricte avec DLG_Scenario.OperationHeures.

    Entrées historiques : ``+H:MM``, ``-H:MM`` ou ``None``.
    Sortie historique : ``+H:MM`` ou ``-H:MM``.
    En cas d'entrée invalide, aucune exception UI n'est produite ici : le résultat
    métier structuré est retourné au second élément du tuple.
    """
    result = operate_signed_durations(heureA, heureB, operation)
    if not result.ok:
        return None, result
    return _format_wx_signed_minutes(result.value_minutes), result


def duree_presence_wx(heure_debut, heure_fin, *, allow_overnight=False):
    """Adapte deux horaires de journée vers une durée signée historique wx."""
    result = calculate_time_difference(
        heure_debut,
        heure_fin,
        allow_overnight=allow_overnight,
    )
    if not result.ok:
        return None, result
    return _format_wx_signed_minutes(result.value_minutes), result
