"""Adaptateur SQL du contrat de lecture Planning."""

from __future__ import annotations

from datetime import date, datetime

from application.services.planning_read import (
    PlanningPerson,
    PlanningPresence,
    PlanningReadDataError,
    PlanningReadMappingError,
    PresenceCategory,
    PresenceQuery,
    VacationPeriod,
)
from domain.common.duration import parse_clock_time


class GestionDbPlanningReadAdapter:
    """Lecture Planning paramétrée, compatible SQLite/MySQL via GestionDB."""

    def __init__(self, db):
        if db is None:
            raise RuntimeError("Connexion GestionDB absente.")
        if getattr(db, "echec", 0):
            raise RuntimeError("Connexion GestionDB indisponible.")
        if getattr(db, "cursor", None) is None:
            raise RuntimeError("Curseur GestionDB absent.")
        self.db = db

    @property
    def _placeholder(self) -> str:
        return "%s" if getattr(self.db, "isNetwork", False) else "?"

    @staticmethod
    def _as_date(value, *, field: str) -> date:
        try:
            if isinstance(value, datetime):
                return value.date()
            if type(value) is date:
                return value
            return date.fromisoformat(str(value)[:10])
        except Exception as exc:
            raise PlanningReadDataError(
                "%s invalide : %r" % (field, value)
            ) from exc

    @staticmethod
    def _as_time_text(value, *, field: str) -> str:
        parsed = parse_clock_time(value, field)
        if not parsed.ok:
            message = parsed.error.message if parsed.error else "horaire invalide"
            raise PlanningReadDataError(message)
        total = int(parsed.value_minutes)
        return "%02d:%02d" % (total // 60, total % 60)

    @staticmethod
    def _duration_minutes(start_time: str, end_time: str) -> int:
        start = parse_clock_time(start_time, "start_time")
        end = parse_clock_time(end_time, "end_time")
        if not start.ok or not end.ok:
            raise PlanningReadDataError("Horaire de présence invalide.")
        duration = int(end.value_minutes) - int(start.value_minutes)
        if duration < 0:
            raise PlanningReadDataError(
                "Une présence possède une heure de fin antérieure au début."
            )
        return duration

    def _in_clause(self, values: tuple[int, ...]) -> tuple[str, tuple[object, ...]]:
        if not values:
            return "", ()
        placeholders = ", ".join(self._placeholder for _ in values)
        return "(%s)" % placeholders, tuple(values)

    def read_presences(
        self,
        query: PresenceQuery,
    ) -> tuple[PlanningPresence, ...]:
        p = self._placeholder
        sql = (
            "SELECT IDpresence, IDpersonne, date, heure_debut, heure_fin, "
            "IDcategorie, intitule FROM presences "
            "WHERE date>=%s AND date<=%s" % (p, p)
        )
        params: list[object] = [
            query.start_date.isoformat(),
            query.end_date.isoformat(),
        ]

        persons_clause, persons_params = self._in_clause(query.person_ids)
        if persons_clause:
            sql += " AND IDpersonne IN %s" % persons_clause
            params.extend(persons_params)

        categories_clause, categories_params = self._in_clause(query.category_ids)
        if categories_clause:
            sql += " AND IDcategorie IN %s" % categories_clause
            params.extend(categories_params)

        sql += " ORDER BY date, IDpersonne, heure_debut, IDpresence"
        self.db.cursor.execute(sql, tuple(params))
        rows = self.db.cursor.fetchall()

        result: list[PlanningPresence] = []
        for row in rows:
            try:
                presence_id = int(row[0])
                person_id = int(row[1])
                presence_date = self._as_date(row[2], field="date")
                start_time = self._as_time_text(row[3], field="heure_debut")
                end_time = self._as_time_text(row[4], field="heure_fin")
                category_id = int(row[5])
                title = str(row[6] or "").strip()
            except PlanningReadDataError:
                raise
            except Exception as exc:
                raise PlanningReadMappingError(
                    "Projection présence impossible : %r" % (row,)
                ) from exc

            result.append(
                PlanningPresence(
                    presence_id=presence_id,
                    person_id=person_id,
                    presence_date=presence_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=self._duration_minutes(
                        start_time,
                        end_time,
                    ),
                    category_id=category_id,
                    title=title,
                )
            )

        return tuple(result)

    def read_people(
        self,
        query: PresenceQuery,
    ) -> tuple[PlanningPerson, ...]:
        sql = "SELECT IDpersonne, nom, prenom FROM personnes"
        params: tuple[object, ...] = ()

        persons_clause, persons_params = self._in_clause(query.person_ids)
        if persons_clause:
            sql += " WHERE IDpersonne IN %s" % persons_clause
            params = persons_params

        sql += " ORDER BY nom, prenom, IDpersonne"
        self.db.cursor.execute(sql, params)
        rows = self.db.cursor.fetchall()

        result: list[PlanningPerson] = []
        for row in rows:
            try:
                person_id = int(row[0])
                name = " ".join(
                    part
                    for part in (
                        str(row[1] or "").strip(),
                        str(row[2] or "").strip(),
                    )
                    if part
                )
                if not name:
                    name = "Personne %d" % person_id
            except Exception as exc:
                raise PlanningReadMappingError(
                    "Projection personne impossible : %r" % (row,)
                ) from exc

            result.append(
                PlanningPerson(
                    person_id=person_id,
                    display_name=name,
                )
            )

        return tuple(result)

    def read_categories(
        self,
        query: PresenceQuery,
    ) -> tuple[PresenceCategory, ...]:
        sql = "SELECT IDcategorie, nom_categorie, couleur FROM cat_presences"
        params: tuple[object, ...] = ()

        categories_clause, categories_params = self._in_clause(query.category_ids)
        if categories_clause:
            sql += " WHERE IDcategorie IN %s" % categories_clause
            params = categories_params

        sql += " ORDER BY nom_categorie, IDcategorie"
        self.db.cursor.execute(sql, params)
        rows = self.db.cursor.fetchall()

        result: list[PresenceCategory] = []
        for row in rows:
            try:
                result.append(
                    PresenceCategory(
                        category_id=int(row[0]),
                        name=str(row[1] or "").strip(),
                        color=str(row[2] or "").strip(),
                    )
                )
            except Exception as exc:
                raise PlanningReadMappingError(
                    "Projection catégorie impossible : %r" % (row,)
                ) from exc

        return tuple(result)

    def read_vacations(
        self,
        query: PresenceQuery,
    ) -> tuple[VacationPeriod, ...]:
        p = self._placeholder
        sql = (
            "SELECT IDperiode, nom, date_debut, date_fin "
            "FROM periodes_vacances "
            "WHERE date_fin>=%s AND date_debut<=%s "
            "ORDER BY date_debut, IDperiode"
            % (p, p)
        )
        self.db.cursor.execute(
            sql,
            (
                query.start_date.isoformat(),
                query.end_date.isoformat(),
            ),
        )
        rows = self.db.cursor.fetchall()

        result: list[VacationPeriod] = []
        for row in rows:
            try:
                start_date = self._as_date(row[2], field="date_debut")
                end_date = self._as_date(row[3], field="date_fin")
                if end_date < start_date:
                    raise PlanningReadDataError(
                        "Une période de vacances possède une fin antérieure au début."
                    )
                result.append(
                    VacationPeriod(
                        vacation_id=int(row[0]),
                        name=str(row[1] or "").strip(),
                        start_date=start_date,
                        end_date=end_date,
                    )
                )
            except PlanningReadDataError:
                raise
            except Exception as exc:
                raise PlanningReadMappingError(
                    "Projection vacances impossible : %r" % (row,)
                ) from exc

        return tuple(result)
