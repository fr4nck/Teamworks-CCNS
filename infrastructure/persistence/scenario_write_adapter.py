"""Adaptateur GestionDB pour les écritures Scénarios."""

from __future__ import annotations

from datetime import date, datetime

from application.services.scenario_write import (
    ScenarioCategorySnapshot,
    ScenarioSnapshot,
)


class GestionDbScenarioWriteAdapter:
    def __init__(self, db):
        if db is None:
            raise RuntimeError("Connexion GestionDB absente.")
        if getattr(db, "echec", 0):
            raise RuntimeError("Connexion GestionDB indisponible.")
        if getattr(db, "cursor", None) is None or getattr(db, "connexion", None) is None:
            raise RuntimeError("Connexion GestionDB incomplète.")
        self.db = db

    @property
    def _placeholder(self) -> str:
        return "%s" if getattr(self.db, "isNetwork", False) else "?"

    @staticmethod
    def _as_date(value) -> date:
        if isinstance(value, datetime):
            return value.date()
        if type(value) is date:
            return value
        return date.fromisoformat(str(value)[:10])

    @classmethod
    def _as_optional_date(cls, value) -> date | None:
        if value in (None, ""):
            return None
        return cls._as_date(value)

    @staticmethod
    def _as_optional_text(value) -> str | None:
        if value is None:
            return None
        return str(value)

    def person_exists(self, person_id: int) -> bool:
        self.db.cursor.execute(
            "SELECT IDpersonne FROM personnes WHERE IDpersonne=%s" % self._placeholder,
            (person_id,),
        )
        return self.db.cursor.fetchone() is not None

    def scenario_exists(self, scenario_id: int) -> bool:
        self.db.cursor.execute(
            "SELECT IDscenario FROM scenarios WHERE IDscenario=%s" % self._placeholder,
            (scenario_id,),
        )
        return self.db.cursor.fetchone() is not None

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
        placeholders = ", ".join([self._placeholder] * 8)
        self.db.cursor.execute(
            "INSERT INTO scenarios "
            "(IDpersonne, nom, description, mode_heure, detail_mois, date_debut, date_fin, toutes_categories) "
            "VALUES (%s)" % placeholders,
            (
                person_id,
                name,
                description,
                hour_mode,
                month_detail,
                start_date.isoformat(),
                end_date.isoformat(),
                int(all_categories),
            ),
        )
        return int(self.db.cursor.lastrowid or 0)

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
        p = self._placeholder
        self.db.cursor.execute(
            "UPDATE scenarios SET "
            "IDpersonne=%s, nom=%s, description=%s, mode_heure=%s, detail_mois=%s, "
            "date_debut=%s, date_fin=%s, toutes_categories=%s WHERE IDscenario=%s"
            % (p, p, p, p, p, p, p, p, p),
            (
                person_id,
                name,
                description,
                hour_mode,
                month_detail,
                start_date.isoformat(),
                end_date.isoformat(),
                int(all_categories),
                scenario_id,
            ),
        )
        return int(self.db.cursor.rowcount)

    def list_scenario_category_ids(self, scenario_id: int) -> tuple[int, ...]:
        self.db.cursor.execute(
            "SELECT IDscenario_cat FROM scenarios_cat WHERE IDscenario=%s "
            "ORDER BY IDscenario_cat" % self._placeholder,
            (scenario_id,),
        )
        return tuple(int(row[0]) for row in self.db.cursor.fetchall())

    def insert_scenario_category(
        self,
        scenario_id: int,
        category_id: int,
        forecast: str | None,
        report: str | None,
        realized_start: date | None,
        realized_end: date | None,
    ) -> int:
        placeholders = ", ".join([self._placeholder] * 6)
        self.db.cursor.execute(
            "INSERT INTO scenarios_cat "
            "(IDscenario, IDcategorie, prevision, report, date_debut_realise, date_fin_realise) "
            "VALUES (%s)" % placeholders,
            (
                scenario_id,
                category_id,
                forecast,
                report,
                realized_start.isoformat() if realized_start else None,
                realized_end.isoformat() if realized_end else None,
            ),
        )
        return int(self.db.cursor.lastrowid or 0)

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
        p = self._placeholder
        self.db.cursor.execute(
            "UPDATE scenarios_cat SET IDcategorie=%s, prevision=%s, report=%s, "
            "date_debut_realise=%s, date_fin_realise=%s "
            "WHERE IDscenario_cat=%s AND IDscenario=%s"
            % (p, p, p, p, p, p, p),
            (
                category_id,
                forecast,
                report,
                realized_start.isoformat() if realized_start else None,
                realized_end.isoformat() if realized_end else None,
                scenario_category_id,
                scenario_id,
            ),
        )
        return int(self.db.cursor.rowcount)

    def delete_scenario_category(
        self, scenario_id: int, scenario_category_id: int
    ) -> int:
        p = self._placeholder
        self.db.cursor.execute(
            "DELETE FROM scenarios_cat WHERE IDscenario_cat=%s AND IDscenario=%s"
            % (p, p),
            (scenario_category_id, scenario_id),
        )
        return int(self.db.cursor.rowcount)

    def count_reports_to_scenario(self, scenario_id: int) -> int:
        pattern = "A%d;%%" % scenario_id
        self.db.cursor.execute(
            "SELECT COUNT(*) FROM scenarios_cat WHERE report LIKE %s"
            % self._placeholder,
            (pattern,),
        )
        row = self.db.cursor.fetchone()
        return int(row[0]) if row else 0

    def delete_all_scenario_categories(self, scenario_id: int) -> int:
        self.db.cursor.execute(
            "DELETE FROM scenarios_cat WHERE IDscenario=%s" % self._placeholder,
            (scenario_id,),
        )
        return int(self.db.cursor.rowcount)

    def delete_scenario(self, scenario_id: int) -> int:
        self.db.cursor.execute(
            "DELETE FROM scenarios WHERE IDscenario=%s" % self._placeholder,
            (scenario_id,),
        )
        return int(self.db.cursor.rowcount)

    def read_scenario(self, scenario_id: int) -> ScenarioSnapshot | None:
        self.db.cursor.execute(
            "SELECT IDpersonne, nom, description, mode_heure, detail_mois, "
            "date_debut, date_fin, toutes_categories "
            "FROM scenarios WHERE IDscenario=%s" % self._placeholder,
            (scenario_id,),
        )
        row = self.db.cursor.fetchone()
        if row is None:
            return None

        self.db.cursor.execute(
            "SELECT IDscenario_cat, IDcategorie, prevision, report, "
            "date_debut_realise, date_fin_realise "
            "FROM scenarios_cat WHERE IDscenario=%s ORDER BY IDscenario_cat"
            % self._placeholder,
            (scenario_id,),
        )
        categories = tuple(
            ScenarioCategorySnapshot(
                scenario_category_id=int(category_row[0]),
                category_id=int(category_row[1]),
                forecast=self._as_optional_text(category_row[2]),
                report=self._as_optional_text(category_row[3]),
                realized_start=self._as_optional_date(category_row[4]),
                realized_end=self._as_optional_date(category_row[5]),
            )
            for category_row in self.db.cursor.fetchall()
        )

        return ScenarioSnapshot(
            scenario_id=scenario_id,
            person_id=int(row[0]),
            name=str(row[1] or ""),
            description=str(row[2] or ""),
            hour_mode=int(row[3]),
            month_detail=int(row[4]),
            start_date=self._as_date(row[5]),
            end_date=self._as_date(row[6]),
            all_categories=bool(row[7]),
            categories=categories,
        )

    def commit(self) -> None:
        self.db.Commit()

    def rollback(self) -> None:
        self.db.connexion.rollback()
