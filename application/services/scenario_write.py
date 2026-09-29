"""Écritures métier des scénarios, indépendantes de wx et Qt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional, Protocol

from application.services.transactional_write import WriteCode, WriteResult, is_valid_target_id


@dataclass(frozen=True)
class ScenarioCategorySnapshot:
    scenario_category_id: int
    category_id: int
    forecast: str | None
    report: str | None
    realized_start: date | None
    realized_end: date | None


@dataclass(frozen=True)
class ScenarioSnapshot:
    scenario_id: int
    person_id: int
    name: str
    description: str
    hour_mode: int
    month_detail: int
    start_date: date
    end_date: date
    all_categories: bool
    categories: tuple[ScenarioCategorySnapshot, ...]


@dataclass(frozen=True)
class ScenarioCategoryCommand:
    category_id: int
    forecast: str | None = None
    report: str | None = None
    realized_start: date | None = None
    realized_end: date | None = None
    scenario_category_id: Optional[int] = None


@dataclass(frozen=True)
class ScenarioSaveCommand:
    person_id: int
    name: str
    description: str
    hour_mode: int
    month_detail: int
    start_date: date
    end_date: date
    all_categories: bool
    categories: tuple[ScenarioCategoryCommand, ...] = ()
    scenario_id: Optional[int] = None


class ScenarioWritePort(Protocol):
    def person_exists(self, person_id: int) -> bool:
        ...

    def scenario_exists(self, scenario_id: int) -> bool:
        ...

    def insert_scenario(
        self,
        person_id: int,
        name: str,
        description: str,
        hour_mode: int,
        month_detail: int,
        start_date: date,
        end_date: date,
        all_categories: bool,
    ) -> int:
        ...

    def update_scenario(
        self,
        scenario_id: int,
        person_id: int,
        name: str,
        description: str,
        hour_mode: int,
        month_detail: int,
        start_date: date,
        end_date: date,
        all_categories: bool,
    ) -> int:
        ...

    def list_scenario_category_ids(self, scenario_id: int) -> tuple[int, ...]:
        ...

    def insert_scenario_category(
        self,
        scenario_id: int,
        category_id: int,
        forecast: str | None,
        report: str | None,
        realized_start: date | None,
        realized_end: date | None,
    ) -> int:
        ...

    def update_scenario_category(
        self,
        scenario_id: int,
        scenario_category_id: int,
        category_id: int,
        forecast: str | None,
        report: str | None,
        realized_start: date | None,
        realized_end: date | None,
    ) -> int:
        ...

    def delete_scenario_category(
        self, scenario_id: int, scenario_category_id: int
    ) -> int:
        ...

    def count_reports_to_scenario(self, scenario_id: int) -> int:
        ...

    def delete_all_scenario_categories(self, scenario_id: int) -> int:
        ...

    def delete_scenario(self, scenario_id: int) -> int:
        ...

    def read_scenario(self, scenario_id: int) -> ScenarioSnapshot | None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


def validate_scenario_command(command: ScenarioSaveCommand) -> tuple[str, ...]:
    errors: list[str] = []

    if not is_valid_target_id(command.person_id):
        errors.append("Identifiant historique de la personne invalide.")
    if command.scenario_id is not None and not is_valid_target_id(command.scenario_id):
        errors.append("Identifiant historique du scénario invalide.")
    if not isinstance(command.name, str) or not command.name.strip():
        errors.append("Le nom du scénario est obligatoire.")
    if not isinstance(command.description, str):
        errors.append("La description du scénario doit être du texte.")
    if (
        not isinstance(command.hour_mode, int)
        or isinstance(command.hour_mode, bool)
        or command.hour_mode < 0
    ):
        errors.append("Le mode d'heure du scénario est invalide.")
    if (
        not isinstance(command.month_detail, int)
        or isinstance(command.month_detail, bool)
        or command.month_detail < 0
    ):
        errors.append("Le niveau de détail mensuel du scénario est invalide.")
    if type(command.start_date) is not date or type(command.end_date) is not date:
        errors.append("La période du scénario est invalide.")
    elif command.end_date < command.start_date:
        errors.append("La date de fin du scénario précède sa date de début.")
    if type(command.all_categories) is not bool:
        errors.append("L'indicateur toutes catégories est invalide.")

    category_ids: list[int] = []
    scenario_category_ids: list[int] = []
    for category in command.categories:
        if not is_valid_target_id(category.category_id):
            errors.append("Une catégorie du scénario possède un identifiant invalide.")
        else:
            category_ids.append(category.category_id)
        if category.scenario_category_id is not None:
            if not is_valid_target_id(category.scenario_category_id):
                errors.append("Une ligne scénario/catégorie possède un identifiant invalide.")
            else:
                scenario_category_ids.append(category.scenario_category_id)
        if category.realized_start is not None and type(category.realized_start) is not date:
            errors.append("Une date de début réalisée est invalide.")
        if category.realized_end is not None and type(category.realized_end) is not date:
            errors.append("Une date de fin réalisée est invalide.")
        if (
            type(category.realized_start) is date
            and type(category.realized_end) is date
            and category.realized_end < category.realized_start
        ):
            errors.append("Une période réalisée de catégorie est inversée.")

    if len(category_ids) != len(set(category_ids)):
        errors.append("Une catégorie est présente plusieurs fois dans le scénario.")
    if len(scenario_category_ids) != len(set(scenario_category_ids)):
        errors.append("Une ligne scénario/catégorie est utilisée plusieurs fois.")

    return tuple(errors)


def _safe_rollback(port: ScenarioWritePort) -> None:
    try:
        port.rollback()
    except Exception:
        pass


def _result_database_error(
    message: str,
    exc: Exception,
    *,
    target_id: int | None,
) -> WriteResult[ScenarioSnapshot]:
    return WriteResult(
        ok=False,
        code=WriteCode.DATABASE_ERROR,
        message="%s : %s" % (message, exc),
        target_id=target_id,
    )


def save_scenario(
    port: ScenarioWritePort,
    *,
    command: ScenarioSaveCommand,
) -> WriteResult[ScenarioSnapshot]:
    """Crée ou modifie un scénario et synchronise ses catégories atomiquement."""

    errors = validate_scenario_command(command)
    if errors:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=" ".join(errors),
            target_id=command.scenario_id,
        )

    scenario_id = command.scenario_id
    try:
        if not port.person_exists(command.person_id):
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="La personne sélectionnée n'existe plus.",
                target_id=scenario_id,
            )

        if scenario_id is None:
            scenario_id = port.insert_scenario(
                command.person_id,
                command.name.strip(),
                command.description,
                command.hour_mode,
                command.month_detail,
                command.start_date,
                command.end_date,
                command.all_categories,
            )
            if not is_valid_target_id(scenario_id):
                _safe_rollback(port)
                return WriteResult(
                    ok=False,
                    code=WriteCode.INVALID_TARGET_ID,
                    message="La création du scénario n'a pas retourné d'identifiant valide.",
                )
        else:
            if not port.scenario_exists(scenario_id):
                return WriteResult(
                    ok=False,
                    code=WriteCode.TARGET_NOT_FOUND,
                    message="Le scénario sélectionné n'existe plus.",
                    target_id=scenario_id,
                )
            affected = int(
                port.update_scenario(
                    scenario_id,
                    command.person_id,
                    command.name.strip(),
                    command.description,
                    command.hour_mode,
                    command.month_detail,
                    command.start_date,
                    command.end_date,
                    command.all_categories,
                )
            )
            if affected not in (0, 1):
                raise RuntimeError(
                    "La mise à jour du scénario a affecté %d ligne(s)." % affected
                )

        existing_ids = set(port.list_scenario_category_ids(scenario_id))
        treated_ids: set[int] = set()

        for category in command.categories:
            scenario_category_id = category.scenario_category_id
            if scenario_category_id is None:
                scenario_category_id = port.insert_scenario_category(
                    scenario_id,
                    category.category_id,
                    category.forecast,
                    category.report,
                    category.realized_start,
                    category.realized_end,
                )
                if not is_valid_target_id(scenario_category_id):
                    raise RuntimeError(
                        "La création d'une catégorie scénario n'a pas retourné d'identifiant valide."
                    )
            else:
                if scenario_category_id not in existing_ids:
                    raise RuntimeError(
                        "La catégorie scénario n°%d n'appartient pas au scénario n°%d."
                        % (scenario_category_id, scenario_id)
                    )
                affected = int(
                    port.update_scenario_category(
                        scenario_id,
                        scenario_category_id,
                        category.category_id,
                        category.forecast,
                        category.report,
                        category.realized_start,
                        category.realized_end,
                    )
                )
                if affected not in (0, 1):
                    raise RuntimeError(
                        "La mise à jour de la catégorie scénario n°%d a affecté %d ligne(s)."
                        % (scenario_category_id, affected)
                    )
            if scenario_category_id in treated_ids:
                raise RuntimeError(
                    "La catégorie scénario n°%d est utilisée plusieurs fois."
                    % scenario_category_id
                )
            treated_ids.add(scenario_category_id)

        for scenario_category_id in existing_ids - treated_ids:
            affected = int(
                port.delete_scenario_category(scenario_id, scenario_category_id)
            )
            if affected not in (0, 1):
                raise RuntimeError(
                    "La suppression de la catégorie scénario n°%d a affecté %d ligne(s)."
                    % (scenario_category_id, affected)
                )

        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return _result_database_error(
            "Enregistrement du scénario impossible",
            exc,
            target_id=scenario_id if is_valid_target_id(scenario_id) else None,
        )

    try:
        snapshot = port.read_scenario(scenario_id)
        if snapshot is None:
            raise LookupError("Scénario introuvable après commit.")
        actual_ids = {item.scenario_category_id for item in snapshot.categories}
        if actual_ids != treated_ids:
            raise LookupError(
                "La relecture ne confirme pas les catégories rattachées au scénario."
            )
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Scénario validé, mais relecture impossible : %s" % exc,
            target_id=scenario_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Scénario enregistré et relu.",
        target_id=scenario_id,
        value=snapshot,
        committed=True,
    )


def duplicate_scenario(
    port: ScenarioWritePort,
    *,
    scenario_id: int,
    name_prefix: str = "Copie de ",
) -> WriteResult[ScenarioSnapshot]:
    """Duplique le scénario et ses catégories dans une transaction unique."""

    if not is_valid_target_id(scenario_id):
        return WriteResult(
            ok=False,
            code=WriteCode.INVALID_TARGET_ID,
            message="Identifiant historique du scénario invalide.",
        )
    if not isinstance(name_prefix, str):
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Le préfixe du nom de copie est invalide.",
            target_id=scenario_id,
        )

    new_scenario_id: int | None = None
    try:
        source = port.read_scenario(scenario_id)
        if source is None:
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="Le scénario source n'existe plus.",
                target_id=scenario_id,
            )

        new_scenario_id = port.insert_scenario(
            source.person_id,
            name_prefix + source.name,
            source.description,
            source.hour_mode,
            source.month_detail,
            source.start_date,
            source.end_date,
            source.all_categories,
        )
        if not is_valid_target_id(new_scenario_id):
            raise RuntimeError(
                "La duplication du scénario n'a pas retourné d'identifiant valide."
            )

        for category in source.categories:
            inserted_id = port.insert_scenario_category(
                new_scenario_id,
                category.category_id,
                category.forecast,
                category.report,
                category.realized_start,
                category.realized_end,
            )
            if not is_valid_target_id(inserted_id):
                raise RuntimeError(
                    "La duplication d'une catégorie scénario n'a pas retourné d'identifiant valide."
                )

        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return _result_database_error(
            "Duplication du scénario impossible",
            exc,
            target_id=new_scenario_id if is_valid_target_id(new_scenario_id) else scenario_id,
        )

    try:
        snapshot = port.read_scenario(new_scenario_id)
        if snapshot is None:
            raise LookupError("Copie du scénario introuvable après commit.")
        if len(snapshot.categories) != len(source.categories):
            raise LookupError(
                "La relecture ne confirme pas toutes les catégories de la copie."
            )
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Scénario dupliqué, mais relecture impossible : %s" % exc,
            target_id=new_scenario_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Scénario dupliqué et relu.",
        target_id=new_scenario_id,
        value=snapshot,
        committed=True,
    )


def delete_scenario(
    port: ScenarioWritePort,
    *,
    scenario_id: int,
    confirmed: bool,
) -> WriteResult[bool]:
    """Supprime catégories puis scénario, en refusant les reports entrants."""

    if not is_valid_target_id(scenario_id):
        return WriteResult(
            ok=False,
            code=WriteCode.INVALID_TARGET_ID,
            message="Identifiant historique du scénario invalide.",
        )
    if confirmed is not True:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="La suppression du scénario doit être confirmée explicitement.",
            target_id=scenario_id,
        )

    try:
        if not port.scenario_exists(scenario_id):
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="Le scénario sélectionné n'existe plus.",
                target_id=scenario_id,
            )

        report_count = int(port.count_reports_to_scenario(scenario_id))
        if report_count:
            return WriteResult(
                ok=False,
                code=WriteCode.VALIDATION_ERROR,
                message="%d report(s) utilisent encore ce scénario." % report_count,
                target_id=scenario_id,
            )

        port.delete_all_scenario_categories(scenario_id)
        affected = int(port.delete_scenario(scenario_id))
        if affected == 0:
            _safe_rollback(port)
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="Le scénario a disparu avant la suppression.",
                target_id=scenario_id,
            )
        if affected != 1:
            raise RuntimeError(
                "La suppression du scénario a affecté %d ligne(s)." % affected
            )
        port.commit()
    except Exception as exc:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Suppression du scénario impossible : %s" % exc,
            target_id=scenario_id,
        )

    try:
        still_exists = port.read_scenario(scenario_id) is not None
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Scénario supprimé, mais contrôle d'absence impossible : %s" % exc,
            target_id=scenario_id,
            committed=True,
        )

    if still_exists:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Scénario supprimé, mais encore relu après commit.",
            target_id=scenario_id,
            value=False,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Scénario supprimé et absence confirmée.",
        target_id=scenario_id,
        value=True,
        committed=True,
    )
