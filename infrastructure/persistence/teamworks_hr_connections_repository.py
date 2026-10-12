from __future__ import annotations

from datetime import date
from typing import Callable

from domain.hr_connections import (
    ConnectionProfile,
    ConnectorCapability,
    EffectivePeriod,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)


TEAMWORKS_HR_SCHEMA_VERSION = 1
_SCHEMA_COMPONENT = "hr_connections_runtime"

_PROFILE_COLUMNS = (
    "structure_ref",
    "organization_code",
    "organization_label",
    "organization_kind",
    "effective_start",
    "effective_end",
)

_EMPLOYEE_PROTECTION_COLUMNS = (
    "structure_ref",
    "record_id",
    "employee_ref",
    "organization_code",
    "organization_kind",
    "relation_kind",
    "status",
    "effective_start",
    "effective_end",
    "scheme_code",
    "option_code",
    "contribution_profile_code",
    "waiver_reason_code",
    "external_reference",
    "document_ref",
    "administrative_deadline",
    "source",
)

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS tw_hr_schema_versions (
        component VARCHAR(50) NOT NULL PRIMARY KEY,
        schema_version INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_connection_profiles (
        structure_ref VARCHAR(80) NOT NULL,
        organization_code VARCHAR(80) NOT NULL,
        organization_label VARCHAR(200) NOT NULL,
        organization_kind VARCHAR(40) NOT NULL,
        effective_start VARCHAR(10),
        effective_end VARCHAR(10),
        PRIMARY KEY (structure_ref, organization_code)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_connection_capabilities (
        structure_ref VARCHAR(80) NOT NULL,
        organization_code VARCHAR(80) NOT NULL,
        capability VARCHAR(50) NOT NULL,
        PRIMARY KEY (structure_ref, organization_code, capability)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_organization_references (
        structure_ref VARCHAR(80) NOT NULL,
        organization_code VARCHAR(80) NOT NULL,
        position INTEGER NOT NULL,
        reference_type VARCHAR(80) NOT NULL,
        reference_value VARCHAR(240) NOT NULL,
        reference_label VARCHAR(200),
        PRIMARY KEY (structure_ref, organization_code, position)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_portal_links (
        structure_ref VARCHAR(80) NOT NULL,
        organization_code VARCHAR(80) NOT NULL,
        position INTEGER NOT NULL,
        url VARCHAR(500) NOT NULL,
        label VARCHAR(200) NOT NULL,
        PRIMARY KEY (structure_ref, organization_code, position)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tw_hr_employee_protection (
        structure_ref VARCHAR(80) NOT NULL,
        record_id VARCHAR(100) NOT NULL,
        employee_ref VARCHAR(80) NOT NULL,
        organization_code VARCHAR(80) NOT NULL,
        organization_kind VARCHAR(40) NOT NULL,
        relation_kind VARCHAR(40) NOT NULL,
        status VARCHAR(30) NOT NULL,
        effective_start VARCHAR(10),
        effective_end VARCHAR(10),
        scheme_code VARCHAR(100),
        option_code VARCHAR(100),
        contribution_profile_code VARCHAR(100),
        waiver_reason_code VARCHAR(100),
        external_reference VARCHAR(200),
        document_ref VARCHAR(200),
        administrative_deadline VARCHAR(10),
        source VARCHAR(120),
        PRIMARY KEY (structure_ref, record_id)
    )
    """,
)

_INDEXES = (
    (
        "tw_hr_connection_profiles",
        "idx_tw_hr_profiles_kind",
        "structure_ref, organization_kind",
    ),
    (
        "tw_hr_employee_protection",
        "idx_tw_hr_employee_protection_employee",
        "structure_ref, employee_ref, effective_start",
    ),
    (
        "tw_hr_employee_protection",
        "idx_tw_hr_employee_protection_organization",
        "structure_ref, organization_code",
    ),
    (
        "tw_hr_employee_protection",
        "idx_tw_hr_employee_protection_deadline",
        "structure_ref, employee_ref, administrative_deadline, status",
    ),
)


class TeamworksHrConnectionsRepository:
    """Persistance de production des profils RH et suivis salarié.

    L'adaptateur s'appuie sur ``GestionDB.DB`` afin de rester compatible avec les
    bases locales SQLite et réseau MySQL historiques de Teamworks. Le schéma est
    strictement additif : aucune table existante n'est modifiée et aucune clé
    étrangère n'est créée vers les tables personnes ou contrats.

    Le même objet implémente les deux ports nécessaires aux services CRH-10A et
    CRH-12 : configuration non secrète des organismes et suivi de protection
    sociale du salarié.
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
                """
                SELECT schema_version
                FROM tw_hr_schema_versions
                WHERE component = ?
                """,
                (_SCHEMA_COMPONENT,),
            )
            if row is None:
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_schema_versions(component, schema_version)
                    VALUES (?, ?)
                    """,
                    (_SCHEMA_COMPONENT, TEAMWORKS_HR_SCHEMA_VERSION),
                )
            elif int(row[0]) != TEAMWORKS_HR_SCHEMA_VERSION:
                raise RuntimeError(
                    "Version de schéma Connexions RH Teamworks non prise en charge : "
                    f"{row[0]}."
                )

            for table, index_name, columns in _INDEXES:
                if not _index_exists(db, table=table, index_name=index_name):
                    _execute(
                        db,
                        f"CREATE INDEX {index_name} ON {table}({columns})",
                    )
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
                """
                SELECT schema_version
                FROM tw_hr_schema_versions
                WHERE component = ?
                """,
                (_SCHEMA_COMPONENT,),
            )
        finally:
            _close(db)
        if row is None:
            raise RuntimeError("Le schéma Connexions RH Teamworks n'est pas initialisé.")
        return int(row[0])

    def save_profile(self, profile: ConnectionProfile) -> ConnectionProfile:
        if not isinstance(profile, ConnectionProfile):
            raise TypeError("Le profil de connexion à persister est invalide.")

        period = profile.effective_period
        key = (profile.structure_ref, profile.organization.code)
        values = (
            profile.organization.label,
            profile.organization.kind.value,
            period.starts_on.isoformat() if period and period.starts_on else None,
            period.ends_on.isoformat() if period and period.ends_on else None,
        )

        db = self._db_factory()
        try:
            exists = _fetchone(
                db,
                """
                SELECT 1
                FROM tw_hr_connection_profiles
                WHERE structure_ref = ? AND organization_code = ?
                """,
                key,
            )
            if exists is None:
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_connection_profiles(
                        structure_ref,
                        organization_code,
                        organization_label,
                        organization_kind,
                        effective_start,
                        effective_end
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    key + values,
                )
            else:
                _execute(
                    db,
                    """
                    UPDATE tw_hr_connection_profiles
                    SET organization_label = ?,
                        organization_kind = ?,
                        effective_start = ?,
                        effective_end = ?
                    WHERE structure_ref = ? AND organization_code = ?
                    """,
                    values + key,
                )

            for table in (
                "tw_hr_connection_capabilities",
                "tw_hr_organization_references",
                "tw_hr_portal_links",
            ):
                _execute(
                    db,
                    f"DELETE FROM {table} WHERE structure_ref = ? AND organization_code = ?",
                    key,
                )

            for capability in sorted(profile.capabilities, key=lambda item: item.value):
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_connection_capabilities(
                        structure_ref, organization_code, capability
                    ) VALUES (?, ?, ?)
                    """,
                    key + (capability.value,),
                )

            for position, reference in enumerate(profile.references):
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_organization_references(
                        structure_ref,
                        organization_code,
                        position,
                        reference_type,
                        reference_value,
                        reference_label
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    key
                    + (
                        position,
                        reference.reference_type,
                        reference.value,
                        reference.label,
                    ),
                )

            for position, link in enumerate(profile.portal_links):
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_portal_links(
                        structure_ref, organization_code, position, url, label
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    key + (position, link.url, link.label),
                )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)
        return profile

    def get_profile(self, *, structure_ref: str, organization_code: str) -> ConnectionProfile | None:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        organization_code = _required_text(organization_code, "Le code de l'organisme est obligatoire.")
        db = self._db_factory()
        try:
            header = _fetchone(
                db,
                """
                SELECT structure_ref, organization_code, organization_label,
                       organization_kind, effective_start, effective_end
                FROM tw_hr_connection_profiles
                WHERE structure_ref = ? AND organization_code = ?
                """,
                (structure_ref, organization_code),
            )
            if header is None:
                return None
            capabilities = _fetchall(
                db,
                """
                SELECT capability FROM tw_hr_connection_capabilities
                WHERE structure_ref = ? AND organization_code = ?
                ORDER BY capability
                """,
                (structure_ref, organization_code),
            )
            references = _fetchall(
                db,
                """
                SELECT reference_type, reference_value, reference_label
                FROM tw_hr_organization_references
                WHERE structure_ref = ? AND organization_code = ?
                ORDER BY position
                """,
                (structure_ref, organization_code),
            )
            links = _fetchall(
                db,
                """
                SELECT url, label FROM tw_hr_portal_links
                WHERE structure_ref = ? AND organization_code = ?
                ORDER BY position
                """,
                (structure_ref, organization_code),
            )
        finally:
            _close(db)
        return _profile_from_rows(header, capabilities, references, links)

    def list_profiles(self, *, structure_ref: str) -> tuple[ConnectionProfile, ...]:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        db = self._db_factory()
        try:
            headers = _fetchall(
                db,
                """
                SELECT structure_ref, organization_code, organization_label,
                       organization_kind, effective_start, effective_end
                FROM tw_hr_connection_profiles
                WHERE structure_ref = ?
                ORDER BY organization_code
                """,
                (structure_ref,),
            )
            if not headers:
                return ()
            capability_rows = _fetchall(
                db,
                """
                SELECT organization_code, capability
                FROM tw_hr_connection_capabilities
                WHERE structure_ref = ?
                ORDER BY organization_code, capability
                """,
                (structure_ref,),
            )
            reference_rows = _fetchall(
                db,
                """
                SELECT organization_code, position, reference_type,
                       reference_value, reference_label
                FROM tw_hr_organization_references
                WHERE structure_ref = ?
                ORDER BY organization_code, position
                """,
                (structure_ref,),
            )
            link_rows = _fetchall(
                db,
                """
                SELECT organization_code, position, url, label
                FROM tw_hr_portal_links
                WHERE structure_ref = ?
                ORDER BY organization_code, position
                """,
                (structure_ref,),
            )
        finally:
            _close(db)

        capabilities_by_code = {}
        for code, capability in capability_rows:
            capabilities_by_code.setdefault(code, []).append((capability,))
        references_by_code = {}
        for code, _position, reference_type, value, label in reference_rows:
            references_by_code.setdefault(code, []).append((reference_type, value, label))
        links_by_code = {}
        for code, _position, url, label in link_rows:
            links_by_code.setdefault(code, []).append((url, label))

        return tuple(
            _profile_from_rows(
                header,
                capabilities_by_code.get(header[1], ()),
                references_by_code.get(header[1], ()),
                links_by_code.get(header[1], ()),
            )
            for header in headers
        )

    def save_employee_protection(self, record: EmployeeProtectionRecord) -> EmployeeProtectionRecord:
        if not isinstance(record, EmployeeProtectionRecord):
            raise TypeError("Le suivi de protection sociale à persister est invalide.")

        key = (record.structure_ref, record.record_id)
        values = _employee_record_values(record)
        db = self._db_factory()
        try:
            exists = _fetchone(
                db,
                """
                SELECT 1 FROM tw_hr_employee_protection
                WHERE structure_ref = ? AND record_id = ?
                """,
                key,
            )
            if exists is None:
                placeholders = ", ".join("?" for _ in _EMPLOYEE_PROTECTION_COLUMNS)
                _execute(
                    db,
                    "INSERT INTO tw_hr_employee_protection("
                    + ", ".join(_EMPLOYEE_PROTECTION_COLUMNS)
                    + f") VALUES ({placeholders})",
                    values,
                )
            else:
                update_columns = _EMPLOYEE_PROTECTION_COLUMNS[2:]
                assignments = ", ".join(f"{column} = ?" for column in update_columns)
                _execute(
                    db,
                    f"UPDATE tw_hr_employee_protection SET {assignments} "
                    "WHERE structure_ref = ? AND record_id = ?",
                    values[2:] + key,
                )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)
        return record

    def get_employee_protection(self, *, structure_ref: str, record_id: str) -> EmployeeProtectionRecord | None:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        record_id = _required_text(record_id, "L'identifiant du suivi de protection sociale est obligatoire.")
        db = self._db_factory()
        try:
            row = _fetchone(
                db,
                "SELECT " + ", ".join(_EMPLOYEE_PROTECTION_COLUMNS)
                + " FROM tw_hr_employee_protection "
                "WHERE structure_ref = ? AND record_id = ?",
                (structure_ref, record_id),
            )
        finally:
            _close(db)
        return _employee_record_from_row(row) if row is not None else None

    def list_employee_protection(self, *, structure_ref: str, employee_ref: str) -> tuple[EmployeeProtectionRecord, ...]:
        structure_ref = _required_text(structure_ref, "La référence de structure est obligatoire.")
        employee_ref = _required_text(employee_ref, "La référence du salarié est obligatoire.")
        db = self._db_factory()
        try:
            rows = _fetchall(
                db,
                "SELECT " + ", ".join(_EMPLOYEE_PROTECTION_COLUMNS)
                + " FROM tw_hr_employee_protection "
                "WHERE structure_ref = ? AND employee_ref = ? "
                "ORDER BY CASE WHEN effective_start IS NULL THEN 1 ELSE 0 END, "
                "effective_start, record_id",
                (structure_ref, employee_ref),
            )
        finally:
            _close(db)
        return tuple(_employee_record_from_row(row) for row in rows)


def _adapt_placeholders(db, statement: str) -> str:
    if bool(getattr(db, "isNetwork", False)):
        return statement.replace("?", "%s")
    return statement.replace("%s", "?")


def _execute(db, statement: str, params: tuple = ()):
    sql = _adapt_placeholders(db, statement)
    db.cursor.execute(sql, tuple(params))
    return db.cursor


def _fetchone(db, statement: str, params: tuple = ()):
    return _execute(db, statement, params).fetchone()


def _fetchall(db, statement: str, params: tuple = ()):
    return _execute(db, statement, params).fetchall()


def _index_exists(db, *, table: str, index_name: str) -> bool:
    if bool(getattr(db, "isNetwork", False)):
        row = _fetchone(db, f"SHOW INDEX FROM {table} WHERE Key_name = ?", (index_name,))
    else:
        row = _fetchone(
            db,
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name = ?",
            (index_name,),
        )
    return row is not None


def _commit(db) -> None:
    commit = getattr(db, "Commit", None)
    if callable(commit):
        commit()
    else:
        db.connexion.commit()


def _rollback(db) -> None:
    try:
        db.connexion.rollback()
    except Exception:
        pass


def _close(db) -> None:
    close = getattr(db, "Close", None)
    if callable(close):
        close()
    else:
        try:
            db.connexion.close()
        except Exception:
            pass


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _profile_from_rows(header, capabilities, references, links) -> ConnectionProfile:
    start = _optional_date(header[4])
    end = _optional_date(header[5])
    period = EffectivePeriod(starts_on=start, ends_on=end) if start or end else None
    return ConnectionProfile.create(
        structure_ref=header[0],
        organization=HrOrganization.create(
            code=header[1], label=header[2], kind=OrganizationKind(header[3])
        ),
        capabilities=(ConnectorCapability(row[0]) for row in capabilities),
        references=(
            OrganizationReference.create(reference_type=row[0], value=row[1], label=row[2])
            for row in references
        ),
        portal_links=(PortalLink.create(url=row[0], label=row[1]) for row in links),
        effective_period=period,
    )


def _employee_record_values(record: EmployeeProtectionRecord) -> tuple:
    period = record.effective_period
    return (
        record.structure_ref,
        record.record_id,
        record.employee_ref,
        record.organization_code,
        record.organization_kind.value,
        record.relation_kind.value,
        record.status.value,
        period.starts_on.isoformat() if period.starts_on else None,
        period.ends_on.isoformat() if period.ends_on else None,
        record.scheme_code,
        record.option_code,
        record.contribution_profile_code,
        record.waiver_reason_code,
        record.external_reference,
        record.document_ref,
        record.administrative_deadline.isoformat() if record.administrative_deadline else None,
        record.source,
    )


def _employee_record_from_row(row) -> EmployeeProtectionRecord:
    return EmployeeProtectionRecord.create(
        record_id=row[1],
        structure_ref=row[0],
        employee_ref=row[2],
        organization_code=row[3],
        organization_kind=OrganizationKind(row[4]),
        relation_kind=EmployeeProtectionRelationKind(row[5]),
        status=EmployeeProtectionStatus(row[6]),
        effective_period=EffectivePeriod(
            starts_on=_optional_date(row[7]), ends_on=_optional_date(row[8])
        ),
        scheme_code=row[9],
        option_code=row[10],
        contribution_profile_code=row[11],
        waiver_reason_code=row[12],
        external_reference=row[13],
        document_ref=row[14],
        administrative_deadline=_optional_date(row[15]),
        source=row[16],
    )
