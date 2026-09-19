from __future__ import annotations

from datetime import date

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter


def resolve_contract_classification(
    *,
    legacy_classification,
    convention_code,
    ccns_group,
    reference_date: date | None,
) -> str:
    """Résout la classification d'un contrat sans dépendance UI.

    Une classification historique enregistrée reste prioritaire. À défaut, un
    contrat CCNS moderne utilise ``ccns_group``. Lorsque la grille applicable ne
    permet pas de résoudre le libellé, le code réellement stocké est conservé.
    Les autres conventions, notamment CEE, ne sont jamais converties en groupe
    CCNS.
    """

    legacy = _text(legacy_classification)
    if legacy:
        return legacy

    convention = _text(convention_code).upper()
    group_code = _text(ccns_group).upper()
    if convention != "CCNS" or not group_code:
        return ""
    if type(reference_date) is not date:
        return group_code

    try:
        choice = next(
            (
                item
                for item in CCNSContractCompliancePresenter().group_choices(reference_date)
                if item.code == group_code
            ),
            None,
        )
    except (LookupError, TypeError, ValueError):
        choice = None
    return _text(choice.label if choice is not None else group_code)


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()
