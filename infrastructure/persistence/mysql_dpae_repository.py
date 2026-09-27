"""Adaptateur MySQL/MariaDB transactionnel pour le domaine DPAE.

Le connecteur est injecté afin de garder le domaine indépendant de mysql.connector.
Chaque opération métier ouvre sa propre connexion et borne explicitement sa
transaction. Les contraintes du schéma restent la dernière ligne de défense
contre les courses inter-processus.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator, Tuple

from domain.dpae.model import (
    CorrelationStatus,
    DpaeCorrelationDecision,
    DpaeDomainError,
    DpaeReturn,
    DpaeReturnEffect,
    DpaeReturnType,
)


class MysqlDpaeRepository:
    def __init__(self, connection_factory: Callable[[], object]) -> None:
        self._connection_factory = connection_factory

    @contextmanager
    def _transaction(self) -> Iterator[Tuple[object, object]]:
        conn = self._connection_factory()
        cur = conn.cursor()
        try:
            # mysql-connector démarre la transaction au premier statement avec
            # autocommit=False. start_transaction() la rend explicite lorsque
            # le connecteur le permet.
            starter = getattr(conn, "start_transaction", None)
            if callable(starter):
                starter()
            yield conn, cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                cur.close()
            finally:
                conn.close()

    @staticmethod
    def _row_to_return(row) -> DpaeReturn:
        return DpaeReturn(
            id=row[0], provider=row[1], return_type=DpaeReturnType(row[2]),
            raw_hash=row[3], received_at=row[4], external_return_id=row[5],
            external_flux_id=row[6], employer_siret=row[7], submission_id=row[8],
            case_id=row[9], correlation_status=CorrelationStatus(row[10]), version=row[11],
        )

    @staticmethod
    def _is_duplicate(exc: Exception) -> bool:
        return getattr(exc, "errno", None) == 1062 or "Duplicate entry" in str(exc)

    def _select_return(self, cur, return_id: str, *, for_update: bool = False):
        sql = (
            "SELECT id,provider,return_type,raw_hash,received_at,external_return_id,"
            "external_flux_id,employer_siret,submission_id,case_id,correlation_status,version "
            "FROM tw_dpae_return WHERE id=%s"
        )
        if for_update:
            sql += " FOR UPDATE"
        cur.execute(sql, (return_id,))
        return cur.fetchone()

    def ingest_return(self, item: DpaeReturn) -> Tuple[DpaeReturn, str]:
        """Insère un retour ou restitue le replay logique existant."""
        try:
            with self._transaction() as (_, cur):
                cur.execute(
                    "INSERT INTO tw_dpae_return "
                    "(id,provider,return_type,raw_hash,received_at,external_return_id,"
                    "external_flux_id,employer_siret,submission_id,case_id,correlation_status,version) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (item.id, item.provider, item.return_type.value, item.raw_hash,
                     item.received_at, item.external_return_id, item.external_flux_id,
                     item.employer_siret, item.submission_id, item.case_id,
                     item.correlation_status.value, item.version),
                )
            return item, "CREATED"
        except Exception as exc:
            if not self._is_duplicate(exc):
                raise

        # Après rollback de la tentative concurrente, relire par les trois
        # identités susceptibles d'avoir déclenché l'unicité.
        conn = self._connection_factory()
        cur = conn.cursor()
        try:
            row = None
            if item.external_return_id:
                cur.execute(
                    "SELECT id,provider,return_type,raw_hash,received_at,external_return_id,"
                    "external_flux_id,employer_siret,submission_id,case_id,correlation_status,version "
                    "FROM tw_dpae_return WHERE provider=%s AND external_return_id=%s",
                    (item.provider, item.external_return_id),
                )
                row = cur.fetchone()
            if row is None:
                row = self._select_return(cur, item.id)
            if row is None:
                cur.execute(
                    "SELECT id,provider,return_type,raw_hash,received_at,external_return_id,"
                    "external_flux_id,employer_siret,submission_id,case_id,correlation_status,version "
                    "FROM tw_dpae_return WHERE provider=%s AND return_type=%s AND raw_hash=%s",
                    (item.provider, item.return_type.value, item.raw_hash),
                )
                row = cur.fetchone()
            if row is None:
                raise DpaeDomainError("RETURN_INTEGRITY_CONFLICT", "Collision DPAE non résolue après contrainte SQL.")
            existing = self._row_to_return(row)
            if existing.raw_hash != item.raw_hash:
                raise DpaeDomainError(
                    "RETURN_INTEGRITY_CONFLICT",
                    "Même identifiant de retour externe avec un contenu différent.",
                )
            return existing, "REPLAY"
        finally:
            cur.close()
            conn.close()

    def get_return(self, return_id: str) -> DpaeReturn:
        conn = self._connection_factory()
        cur = conn.cursor()
        try:
            row = self._select_return(cur, return_id)
            if row is None:
                raise KeyError(return_id)
            return self._row_to_return(row)
        finally:
            cur.close()
            conn.close()

    def confirm_correlation(self, return_id: str, submission_id: str, case_id: str, expected_version: int) -> str:
        """CAS atomique sous verrou de ligne, cohérent avec InMemoryDpaeRepository."""
        with self._transaction() as (_, cur):
            row = self._select_return(cur, return_id, for_update=True)
            if row is None:
                raise KeyError(return_id)
            item = self._row_to_return(row)
            result = item.confirm_correlation(submission_id, case_id, expected_version)
            if result == "ALREADY_CONFIRMED":
                return result
            cur.execute(
                "UPDATE tw_dpae_return SET submission_id=%s,case_id=%s,"
                "correlation_status='CONFIRMED',version=version+1 "
                "WHERE id=%s AND version=%s",
                (submission_id, case_id, return_id, expected_version),
            )
            if cur.rowcount != 1:
                raise DpaeDomainError("DPAE_CORRELATION_STALE", "Le retour DPAE a été modifié depuis sa lecture.")
            return "CONFIRMED"

    def append_decision(self, decision: DpaeCorrelationDecision) -> None:
        try:
            with self._transaction() as (_, cur):
                cur.execute(
                    "INSERT INTO tw_dpae_correlation_decision "
                    "(id,return_id,action,actor_id,decided_at,candidate_submission_id,reason_code,supersedes_id) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (decision.id, decision.return_id, decision.action, decision.actor_id,
                     decision.decided_at, decision.candidate_submission_id,
                     decision.reason_code, decision.supersedes_id),
                )
                if decision.action == "CONFIRM_MATCH" and decision.candidate_submission_id:
                    cur.execute(
                        "INSERT INTO tw_dpae_current_correlation "
                        "(return_id,submission_id,decision_id,confirmed_at) VALUES (%s,%s,%s,%s)",
                        (decision.return_id, decision.candidate_submission_id,
                         decision.id, decision.decided_at),
                    )
        except Exception as exc:
            if self._is_duplicate(exc):
                # Replay de la même décision seulement ; une corrélation
                # concurrente différente doit rester visible comme conflit.
                conn = self._connection_factory()
                cur = conn.cursor()
                try:
                    cur.execute(
                        "SELECT return_id,action,actor_id,candidate_submission_id "
                        "FROM tw_dpae_correlation_decision WHERE id=%s",
                        (decision.id,),
                    )
                    row = cur.fetchone()
                    if row == (decision.return_id, decision.action, decision.actor_id,
                               decision.candidate_submission_id):
                        return
                finally:
                    cur.close()
                    conn.close()
                raise DpaeDomainError(
                    "CONCURRENT_CORRELATION_CONFLICT",
                    "Une autre corrélation courante existe déjà pour ce retour.",
                ) from exc
            raise

    def record_effect_once(self, effect: DpaeReturnEffect) -> bool:
        """Vérifie CONFIRMED et matérialise l'effet exactly-once atomiquement."""
        try:
            with self._transaction() as (_, cur):
                row = self._select_return(cur, effect.return_id, for_update=True)
                if row is None:
                    raise KeyError(effect.return_id)
                item = self._row_to_return(row)
                if not item.may_have_business_effect:
                    raise DpaeDomainError(
                        "DPAE_UNCONFIRMED_RETURN_EFFECT",
                        "Un retour non confirmé ne peut produire aucun effet métier.",
                    )
                cur.execute(
                    "INSERT INTO tw_dpae_return_effect (return_id,effect_type,created_at) VALUES (%s,%s,%s)",
                    (effect.return_id, effect.effect_type, effect.created_at),
                )
            return True
        except Exception as exc:
            if self._is_duplicate(exc):
                return False
            raise

    def effect_count(self, return_id: str, effect_type: str) -> int:
        conn = self._connection_factory()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT COUNT(*) FROM tw_dpae_return_effect WHERE return_id=%s AND effect_type=%s",
                (return_id, effect_type),
            )
            return int(cur.fetchone()[0])
        finally:
            cur.close()
            conn.close()

    def acquire_submission_lock(self, case_id: str, submission_id: str, acquired_at) -> bool:
        """Matérialise l'unique tentative incertaine d'un Case."""
        try:
            with self._transaction() as (_, cur):
                cur.execute(
                    "INSERT INTO tw_dpae_case_submission_lock (case_id,submission_id,acquired_at) VALUES (%s,%s,%s)",
                    (case_id, submission_id, acquired_at),
                )
            return True
        except Exception as exc:
            if self._is_duplicate(exc):
                return False
            raise

    def release_submission_lock(self, case_id: str, submission_id: str) -> bool:
        with self._transaction() as (_, cur):
            cur.execute(
                "DELETE FROM tw_dpae_case_submission_lock WHERE case_id=%s AND submission_id=%s",
                (case_id, submission_id),
            )
            return cur.rowcount == 1
