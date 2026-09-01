from __future__ import annotations

from datetime import timedelta

from domain.hr_connections import (
    EmployeeProtectionRecord,
    EmployeeProtectionStatus,
)

from .teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
    _EMPLOYEE_PROTECTION_COLUMNS,
    _close,
    _commit,
    _employee_record_from_row,
    _employee_record_values,
    _execute,
    _fetchone,
    _rollback,
)


class TeamworksEmployeeProtectionSuccessionRepository(TeamworksHrConnectionsRepository):
    """Extension transactionnelle de la persistance Teamworks CRH-16.

    La succession d'une période est volontairement une seule unité de travail :
    l'ancienne ligne passe à ``ENDED`` et la nouvelle ligne est insérée avant le
    commit. Toute erreur sur l'insertion de la période successeure annule aussi la
    clôture de la période précédente.
    """

    def supersede_employee_protection(
        self,
        *,
        ended_record: EmployeeProtectionRecord,
        successor_record: EmployeeProtectionRecord,
    ) -> tuple[EmployeeProtectionRecord, EmployeeProtectionRecord]:
        _validate_succession_records(
            ended_record=ended_record,
            successor_record=successor_record,
        )

        db = self._db_factory()
        try:
            current_row = _fetchone(
                db,
                "SELECT " + ", ".join(_EMPLOYEE_PROTECTION_COLUMNS)
                + " FROM tw_hr_employee_protection "
                "WHERE structure_ref = ? AND record_id = ?",
                (ended_record.structure_ref, ended_record.record_id),
            )
            if current_row is None:
                raise LookupError("La période de protection sociale à remplacer est introuvable.")

            current_record = _employee_record_from_row(current_row)
            _validate_current_record(
                current_record=current_record,
                ended_record=ended_record,
            )

            ended_values = _employee_record_values(ended_record)
            update_columns = _EMPLOYEE_PROTECTION_COLUMNS[2:]
            assignments = ", ".join(f"{column} = ?" for column in update_columns)
            cursor = _execute(
                db,
                f"UPDATE tw_hr_employee_protection SET {assignments} "
                "WHERE structure_ref = ? AND record_id = ? AND status = ?",
                ended_values[2:]
                + (
                    ended_record.structure_ref,
                    ended_record.record_id,
                    EmployeeProtectionStatus.ACTIVE.value,
                ),
            )
            rowcount = getattr(cursor, "rowcount", 1)
            if rowcount not in (-1, 1):
                raise RuntimeError(
                    "La période active a changé pendant la préparation de sa succession."
                )

            successor_values = _employee_record_values(successor_record)
            placeholders = ", ".join("?" for _ in _EMPLOYEE_PROTECTION_COLUMNS)
            _execute(
                db,
                "INSERT INTO tw_hr_employee_protection("
                + ", ".join(_EMPLOYEE_PROTECTION_COLUMNS)
                + f") VALUES ({placeholders})",
                successor_values,
            )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)

        return ended_record, successor_record


def _validate_succession_records(
    *,
    ended_record: EmployeeProtectionRecord,
    successor_record: EmployeeProtectionRecord,
) -> None:
    if not isinstance(ended_record, EmployeeProtectionRecord):
        raise TypeError("La période à clôturer est invalide.")
    if not isinstance(successor_record, EmployeeProtectionRecord):
        raise TypeError("La période successeure est invalide.")
    if ended_record.status is not EmployeeProtectionStatus.ENDED:
        raise ValueError("La période précédente doit être terminée avant persistance.")
    if successor_record.status is not EmployeeProtectionStatus.ACTIVE:
        raise ValueError("La période successeure doit être active.")
    if ended_record.structure_ref != successor_record.structure_ref:
        raise ValueError("Les périodes doivent appartenir à la même structure.")
    if ended_record.employee_ref != successor_record.employee_ref:
        raise ValueError("Les périodes doivent appartenir au même salarié.")
    if ended_record.record_id == successor_record.record_id:
        raise ValueError("La période successeure doit avoir un nouvel identifiant.")

    ended_on = ended_record.effective_period.ends_on
    successor_starts_on = successor_record.effective_period.starts_on
    if ended_on is None or successor_starts_on is None:
        raise ValueError("La succession exige des dates explicites.")
    if ended_on + timedelta(days=1) != successor_starts_on:
        raise ValueError("Les périodes successives doivent être contiguës.")


def _validate_current_record(
    *,
    current_record: EmployeeProtectionRecord,
    ended_record: EmployeeProtectionRecord,
) -> None:
    if current_record.status is not EmployeeProtectionStatus.ACTIVE:
        raise RuntimeError("La période à remplacer n'est plus active.")
    if current_record.structure_ref != ended_record.structure_ref:
        raise RuntimeError("La structure de la période active a changé.")
    if current_record.employee_ref != ended_record.employee_ref:
        raise RuntimeError("Le salarié de la période active a changé.")
    if current_record.effective_period.starts_on != ended_record.effective_period.starts_on:
        raise RuntimeError("La date d'effet de la période active a changé.")

    stable_fields = (
        "record_id",
        "organization_code",
        "organization_kind",
        "relation_kind",
        "scheme_code",
        "option_code",
        "contribution_profile_code",
        "waiver_reason_code",
        "external_reference",
        "document_ref",
        "administrative_deadline",
        "source",
    )
    for field_name in stable_fields:
        if getattr(current_record, field_name) != getattr(ended_record, field_name):
            raise RuntimeError(
                "La période active a changé pendant la préparation de sa succession."
            )

    current_end = current_record.effective_period.ends_on
    ended_on = ended_record.effective_period.ends_on
    if current_end is not None and ended_on is not None and ended_on > current_end:
        raise ValueError(
            "La succession ne peut pas prolonger une date de fin déjà enregistrée."
        )
