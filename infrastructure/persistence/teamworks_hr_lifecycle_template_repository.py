from __future__ import annotations

from typing import Callable

from domain.hr_connections import (
    ExpectedDocument,
    HrCaseType,
    HrLifecycleEventKind,
    HrLifecycleTemplate,
)

from .teamworks_hr_connections_repository import (
    _close,
    _commit,
    _execute,
    _fetchall,
    _fetchone,
    _index_exists,
    _required_text,
    _rollback,
)


TEAMWORKS_HR_LIFECYCLE_SCHEMA_VERSION = 1
_SCHEMA_COMPONENT = "hr_lifecycle_templates"

_TEMPLATE_COLUMNS = (
    "structure_ref",
    "template_id",
    "event_kind",
    "organization_code",
    "case_type_code",
    "case_type_label",
    "due_offset_days",
    "enabled",
)

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS tw_hr_lifecycle_templates (
        structure_ref VARCHAR(80) NOT NULL,
        template_id VARCHAR(100) NOT NULL,
        event_kind VARCHAR(40) NOT NULL,
        organization_code VARCHAR(80) NOT NULL,
        case_type_code VARCHAR(100) NOT NULL,
        case_type_label VARCHAR(200) NOT NULL,
        due_offset_days INTEGER,
        enabled INTEGER NOT NULL,
        PRIMARY KEY (structure_ref, template_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_lifecycle_template_documents (
        structure_ref VARCHAR(80) NOT NULL,
        template_id VARCHAR(100) NOT NULL,
        position INTEGER NOT NULL,
        document_code VARCHAR(100) NOT NULL,
        document_label VARCHAR(200) NOT NULL,
        required INTEGER NOT NULL,
        PRIMARY KEY (structure_ref, template_id, position)
    )
    """,
)

_INDEXES = (
    (
        "tw_hr_lifecycle_templates",
        "idx_tw_hr_lifecycle_event",
        "structure_ref, event_kind, enabled",
    ),
    (
        "tw_hr_lifecycle_templates",
        "idx_tw_hr_lifecycle_org",
        "structure_ref, organization_code",
    ),
)


class TeamworksHrLifecycleTemplateRepository:
    """Persistance additive des règles locales de cycle de vie RH.

    Le repository stocke uniquement une configuration explicite de la structure.
    Il n'embarque aucun catalogue réglementaire et ne touche ni aux personnes ni
    aux contrats historiques. Désactiver un modèle se fait par ``enabled=False`` ;
    aucune API de suppression de modèle n'est exposée.
    """

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        ensure_schema: bool = True,
    ) -> None:
        self._db_factory = db_factory or self._default_db_factory
        if ensure_schema:
            self.ensure_schema()

    @staticmethod
    def _default_db_factory():
        import GestionDB

        return GestionDB.DB()

    def ensure_schema(self) -> None:
        db = self._db_factory()
        try:
            for statement in _SCHEMA_STATEMENTS:
                _execute(db, statement)
            row = _fetchone(
                db,
                "SELECT schema_version FROM tw_hr_schema_versions WHERE component = ?",
                (_SCHEMA_COMPONENT,),
            )
            if row is None:
                _execute(
                    db,
                    "INSERT INTO tw_hr_schema_versions(component, schema_version) VALUES (?, ?)",
                    (_SCHEMA_COMPONENT, TEAMWORKS_HR_LIFECYCLE_SCHEMA_VERSION),
                )
            elif int(row[0]) != TEAMWORKS_HR_LIFECYCLE_SCHEMA_VERSION:
                raise RuntimeError(
                    "Version de schéma des modèles de cycle de vie RH non prise en charge : "
                    f"{row[0]}."
                )
            for table, index_name, columns in _INDEXES:
                if not _index_exists(db, table=table, index_name=index_name):
                    _execute(db, f"CREATE INDEX {index_name} ON {table}({columns})")
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)

    def schema_version(self) -> int:
        db = self._db_factory()
        try:
            row = _fetchone(
                db,
                "SELECT schema_version FROM tw_hr_schema_versions WHERE component = ?",
                (_SCHEMA_COMPONENT,),
            )
        finally:
            _close(db)
        if row is None:
            raise RuntimeError("Le schéma des modèles de cycle de vie RH n'est pas initialisé.")
        return int(row[0])

    def save_template(
        self,
        *,
        structure_ref: str,
        template: HrLifecycleTemplate,
    ) -> HrLifecycleTemplate:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(template, HrLifecycleTemplate):
            raise TypeError("Le modèle de cycle de vie RH à persister est invalide.")

        key = (structure_ref, template.template_id)
        values = (
            template.event_kind.value,
            template.organization_code,
            template.case_type.code,
            template.case_type.label,
            template.due_offset_days,
            1 if template.enabled else 0,
        )
        db = self._db_factory()
        try:
            exists = _fetchone(
                db,
                "SELECT 1 FROM tw_hr_lifecycle_templates "
                "WHERE structure_ref = ? AND template_id = ?",
                key,
            )
            if exists is None:
                _execute(
                    db,
                    "INSERT INTO tw_hr_lifecycle_templates("
                    + ", ".join(_TEMPLATE_COLUMNS)
                    + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    key + values,
                )
            else:
                _execute(
                    db,
                    "UPDATE tw_hr_lifecycle_templates SET "
                    "event_kind = ?, organization_code = ?, case_type_code = ?, "
                    "case_type_label = ?, due_offset_days = ?, enabled = ? "
                    "WHERE structure_ref = ? AND template_id = ?",
                    values + key,
                )

            _execute(
                db,
                "DELETE FROM tw_hr_lifecycle_template_documents "
                "WHERE structure_ref = ? AND template_id = ?",
                key,
            )
            for position, document in enumerate(template.expected_documents):
                _execute(
                    db,
                    "INSERT INTO tw_hr_lifecycle_template_documents("
                    "structure_ref, template_id, position, document_code, "
                    "document_label, required) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        structure_ref,
                        template.template_id,
                        position,
                        document.code,
                        document.label,
                        1 if document.required else 0,
                    ),
                )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)
        return template

    def get_template(
        self,
        *,
        structure_ref: str,
        template_id: str,
    ) -> HrLifecycleTemplate | None:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        template_id = _required_text(
            template_id,
            "L'identifiant du modèle RH est obligatoire.",
        )
        db = self._db_factory()
        try:
            row = _fetchone(
                db,
                "SELECT "
                + ", ".join(_TEMPLATE_COLUMNS)
                + " FROM tw_hr_lifecycle_templates "
                "WHERE structure_ref = ? AND template_id = ?",
                (structure_ref, template_id),
            )
            if row is None:
                return None
            documents = self._load_documents(
                db,
                structure_ref=structure_ref,
                template_ids=(template_id,),
            )
        finally:
            _close(db)
        return _template_from_row(row, documents.get(template_id, ()))

    def list_templates(
        self,
        *,
        structure_ref: str,
        event_kind: HrLifecycleEventKind,
    ) -> tuple[HrLifecycleTemplate, ...]:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(event_kind, HrLifecycleEventKind):
            raise TypeError("La nature d'événement de cycle de vie RH est invalide.")

        db = self._db_factory()
        try:
            rows = _fetchall(
                db,
                "SELECT "
                + ", ".join(_TEMPLATE_COLUMNS)
                + " FROM tw_hr_lifecycle_templates "
                "WHERE structure_ref = ? AND event_kind = ? ORDER BY template_id",
                (structure_ref, event_kind.value),
            )
            documents = self._load_documents(
                db,
                structure_ref=structure_ref,
                template_ids=tuple(row[1] for row in rows),
            )
        finally:
            _close(db)
        return tuple(
            _template_from_row(row, documents.get(row[1], ()))
            for row in rows
        )

    @staticmethod
    def _load_documents(
        db,
        *,
        structure_ref: str,
        template_ids: tuple[str, ...],
    ) -> dict[str, tuple[ExpectedDocument, ...]]:
        if not template_ids:
            return {}
        placeholders = ", ".join("?" for _ in template_ids)
        rows = _fetchall(
            db,
            "SELECT template_id, document_code, document_label, required "
            "FROM tw_hr_lifecycle_template_documents "
            "WHERE structure_ref = ? AND template_id IN ("
            + placeholders
            + ") ORDER BY template_id, position",
            (structure_ref,) + template_ids,
        )
        grouped: dict[str, list[ExpectedDocument]] = {}
        for template_id, code, label, required in rows:
            grouped.setdefault(template_id, []).append(
                ExpectedDocument.create(
                    code=code,
                    label=label,
                    required=bool(int(required)),
                )
            )
        return {key: tuple(value) for key, value in grouped.items()}


def _template_from_row(
    row,
    documents: tuple[ExpectedDocument, ...],
) -> HrLifecycleTemplate:
    return HrLifecycleTemplate.create(
        template_id=row[1],
        event_kind=HrLifecycleEventKind(row[2]),
        organization_code=row[3],
        case_type=HrCaseType.create(code=row[4], label=row[5]),
        due_offset_days=int(row[6]) if row[6] is not None else None,
        expected_documents=documents,
        enabled=bool(int(row[7])),
    )
