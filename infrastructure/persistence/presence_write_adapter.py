"""Adaptateur GestionDB pour les écritures de Présences."""

from __future__ import annotations

from datetime import date, datetime

from application.services.presence_write import PresenceSnapshot
from domain.common.presence_revision import build_presence_revision


class GestionDbPresenceWriteAdapter:
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

    @staticmethod
    def _as_time_text(value) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        return text[:5]

    def person_exists(self, person_id: int) -> bool:
        self.db.cursor.execute(
            "SELECT IDpersonne FROM personnes WHERE IDpersonne=%s" % self._placeholder,
            (person_id,),
        )
        return self.db.cursor.fetchone() is not None

    def presence_exists(self, presence_id: int) -> bool:
        self.db.cursor.execute(
            "SELECT IDpresence FROM presences WHERE IDpresence=%s" % self._placeholder,
            (presence_id,),
        )
        return self.db.cursor.fetchone() is not None

    def read_presence(self, presence_id: int) -> PresenceSnapshot | None:
        self.db.cursor.execute(
            "SELECT IDpersonne, date, heure_debut, heure_fin, IDcategorie, intitule "
            "FROM presences WHERE IDpresence=%s" % self._placeholder,
            (presence_id,),
        )
        row = self.db.cursor.fetchone()
        if row is None:
            return None
        person_id = int(row[0])
        presence_date = self._as_date(row[1])
        start_time = self._as_time_text(row[2])
        end_time = self._as_time_text(row[3])
        category_id = int(row[4])
        title = str(row[5] or "")
        return PresenceSnapshot(
            presence_id=presence_id,
            person_id=person_id,
            presence_date=presence_date,
            start_time=start_time,
            end_time=end_time,
            category_id=category_id,
            title=title,
            revision=build_presence_revision(
                presence_id=presence_id,
                presence_date=presence_date,
                start_time=start_time,
                end_time=end_time,
                category_id=category_id,
                title=title,
            ),
        )

    def find_overlap(
        self,
        *,
        person_id: int,
        presence_date: date,
        start_time: str,
        end_time: str,
        exclude_presence_id: int | None = None,
    ) -> int | None:
        p = self._placeholder
        sql = (
            "SELECT IDpresence FROM presences "
            "WHERE date=%s AND IDpersonne=%s "
            "AND heure_debut<%s AND heure_fin>%s"
            % (p, p, p, p)
        )
        params: list[object] = [
            presence_date.isoformat(),
            person_id,
            end_time,
            start_time,
        ]
        if exclude_presence_id is not None:
            sql += " AND IDpresence<>%s" % p
            params.append(exclude_presence_id)
        sql += " ORDER BY IDpresence LIMIT 1"
        self.db.cursor.execute(sql, tuple(params))
        row = self.db.cursor.fetchone()
        return int(row[0]) if row is not None else None

    def insert_presence(
        self,
        *,
        person_id: int,
        presence_date: date,
        start_time: str,
        end_time: str,
        category_id: int,
        title: str,
    ) -> int:
        p = self._placeholder
        self.db.cursor.execute(
            "INSERT INTO presences "
            "(IDpersonne, date, heure_debut, heure_fin, IDcategorie, intitule) "
            "VALUES (%s, %s, %s, %s, %s, %s)" % (p, p, p, p, p, p),
            (
                person_id,
                presence_date.isoformat(),
                start_time,
                end_time,
                category_id,
                title,
            ),
        )
        return int(self.db.cursor.lastrowid or 0)

    def update_presence(
        self,
        *,
        presence_id: int,
        start_time: str,
        end_time: str,
        category_id: int,
        title: str,
        expected: PresenceSnapshot | None = None,
    ) -> int:
        p = self._placeholder
        sql = (
            "UPDATE presences SET heure_debut=%s, heure_fin=%s, "
            "IDcategorie=%s, intitule=%s WHERE IDpresence=%s"
            % (p, p, p, p, p)
        )
        params: list[object] = [
            start_time,
            end_time,
            category_id,
            title,
            presence_id,
        ]
        if expected is not None:
            sql += (
                " AND IDpersonne=%s AND date=%s "
                "AND heure_debut=%s AND heure_fin=%s "
                "AND IDcategorie=%s AND COALESCE(intitule, '')=%s"
                % (p, p, p, p, p, p)
            )
            params.extend(
                (
                    expected.person_id,
                    expected.presence_date.isoformat(),
                    expected.start_time,
                    expected.end_time,
                    expected.category_id,
                    expected.title,
                )
            )
        self.db.cursor.execute(sql, tuple(params))
        return int(self.db.cursor.rowcount)

    def delete_presence(
        self,
        presence_id: int,
        *,
        expected: PresenceSnapshot | None = None,
    ) -> int:
        p = self._placeholder
        sql = "DELETE FROM presences WHERE IDpresence=%s" % p
        params: list[object] = [presence_id]
        if expected is not None:
            sql += (
                " AND IDpersonne=%s AND date=%s "
                "AND heure_debut=%s AND heure_fin=%s "
                "AND IDcategorie=%s AND COALESCE(intitule, '')=%s"
                % (p, p, p, p, p, p)
            )
            params.extend(
                (
                    expected.person_id,
                    expected.presence_date.isoformat(),
                    expected.start_time,
                    expected.end_time,
                    expected.category_id,
                    expected.title,
                )
            )
        self.db.cursor.execute(sql, tuple(params))
        return int(self.db.cursor.rowcount)

    def commit(self) -> None:
        self.db.Commit()

    def rollback(self) -> None:
        self.db.connexion.rollback()
