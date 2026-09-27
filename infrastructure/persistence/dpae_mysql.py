"""Adaptateur MariaDB/MySQL du service DPAE."""
import uuid


class IdempotencyPayloadConflict(Exception):
    pass


class InvalidDpaeTransition(Exception):
    pass


class DpaeMariaDbAdapter:
    def __init__(self, connection_factory):
        self._connect = connection_factory

    @staticmethod
    def _id():
        return uuid.uuid4().hex

    def prepare(self, cmd):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT command_hash,case_id,decision FROM tw_dpae_command_audit WHERE command_id=%s", (cmd.command_id,))
            previous = cur.fetchone()
            command_hash = cmd.case_key
            if previous:
                if previous[0] != command_hash:
                    raise IdempotencyPayloadConflict("IDEMPOTENCY_PAYLOAD_CONFLICT")
                conn.rollback()
                return {"case_id": previous[1], "status": "READY", "replayed": True}
            case_id = self._id()
            cur.execute("INSERT INTO tw_dpae_case (id,case_key,employee_id,contract_id,establishment_id,expected_hiring_at,status,origin,created_at,version) VALUES (%s,%s,%s,%s,%s,%s,'READY','TEAMWORKS',NOW(),0)", (case_id,cmd.case_key,cmd.employee_id,cmd.contract_id,cmd.establishment_id,cmd.expected_hiring_at))
            cur.execute("INSERT INTO tw_dpae_command_audit (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,requested_at,decided_at,decision,case_version_seen) VALUES (%s,%s,'PrepareDpae',%s,'USER',%s,%s,NOW(),NOW(),'APPLIED',0)", (self._id(),cmd.command_id,command_hash,cmd.actor_id,case_id))
            conn.commit()
            return {"case_id": case_id, "status": "READY", "replayed": False}
        except Exception:
            conn.rollback(); raise
        finally:
            conn.close()

    def submit(self, cmd):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT command_hash,case_id,submission_id,decision FROM tw_dpae_command_audit WHERE command_id=%s", (cmd.command_id,))
            previous = cur.fetchone()
            if previous:
                if previous[0] != cmd.payload_hash:
                    raise IdempotencyPayloadConflict("IDEMPOTENCY_PAYLOAD_CONFLICT")
                conn.rollback()
                return {"case_id": previous[1], "submission_id": previous[2], "decision": previous[3], "replayed": True}
            cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s FOR UPDATE", (cmd.case_id,))
            case = cur.fetchone()
            if case != ("READY", 0):
                raise InvalidDpaeTransition("DPAE_NOT_SUBMITTABLE")
            submission_id = self._id()
            cur.execute("UPDATE tw_dpae_case SET status='SUBMITTING',version=1 WHERE id=%s AND version=0", (cmd.case_id,))
            cur.execute("INSERT INTO tw_dpae_submission (id,case_id,attempt_no,idempotency_key,payload_hash,state,created_at,version) VALUES (%s,%s,1,%s,%s,'PREPARED',NOW(),0)", (submission_id,cmd.case_id,cmd.command_id,cmd.payload_hash))
            cur.execute("INSERT INTO tw_dpae_case_event (id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) VALUES (%s,%s,'SUBMISSION_REQUESTED','READY','SUBMITTING',0,1,'USER',%s,%s,%s,NOW(),NOW())", (self._id(),cmd.case_id,cmd.actor_id,cmd.command_id,cmd.payload_hash))
            cur.execute("INSERT INTO tw_dpae_command_audit (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,submission_id,requested_at,decided_at,decision,case_version_seen) VALUES (%s,%s,'SubmitDpae',%s,'USER',%s,%s,%s,NOW(),NOW(),'APPLIED',0)", (self._id(),cmd.command_id,cmd.payload_hash,cmd.actor_id,cmd.case_id,submission_id))
            conn.commit()
            return {"case_id": cmd.case_id, "submission_id": submission_id, "decision": "APPLIED", "replayed": False}
        except Exception:
            conn.rollback(); raise
        finally:
            conn.close()

    def mark_sent(self, submission_id, external_flux_id):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT state,version FROM tw_dpae_submission WHERE id=%s FOR UPDATE", (submission_id,))
            state = cur.fetchone()
            if state == ("SENT", 1):
                conn.rollback(); return
            if state != ("PREPARED", 0):
                raise InvalidDpaeTransition("SUBMISSION_NOT_SENDABLE")
            cur.execute("UPDATE tw_dpae_submission SET state='SENT',external_flux_id=%s,sent_at=NOW(),version=1 WHERE id=%s AND version=0", (external_flux_id,submission_id))
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally: conn.close()

    def ingest_return(self, cmd):
        conn = self._connect()
        try:
            cur = conn.cursor()
            if cmd.external_return_id:
                cur.execute("SELECT id,submission_id,case_id,correlation_status FROM tw_dpae_return WHERE provider=%s AND external_return_id=%s", (cmd.provider,cmd.external_return_id))
                previous = cur.fetchone()
                if previous:
                    conn.rollback(); return {"return_id": previous[0], "submission_id": previous[1], "case_id": previous[2], "correlation_status": previous[3], "duplicate": True}
            return_id = self._id()
            submission_id = case_id = None
            correlation = "UNMATCHED"
            if cmd.external_flux_id:
                cur.execute("SELECT id,case_id FROM tw_dpae_submission WHERE external_flux_id=%s", (cmd.external_flux_id,))
                candidates = cur.fetchall()
                if len(candidates) == 1:
                    submission_id, case_id = candidates[0]; correlation = "MATCHED"
                elif len(candidates) > 1:
                    correlation = "AMBIGUOUS"
            cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,external_flux_id,employer_siret,submission_id,case_id,correlation_status,processing_status,version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PROCESSED',1)", (return_id,cmd.provider,cmd.return_type,cmd.raw_hash,cmd.received_at,cmd.external_return_id,cmd.external_flux_id,cmd.employer_siret,submission_id,case_id,correlation))
            if correlation == "MATCHED":
                decision_id = self._id()
                cur.execute("INSERT INTO tw_dpae_correlation_decision (id,return_id,action,actor_id,decided_at,candidate_submission_id,reason_code) VALUES (%s,%s,'CONFIRM_MATCH','DPAE_RETURN_CORRELATOR',NOW(),%s,'EXTERNAL_FLUX_ID_EXACT')", (decision_id,return_id,submission_id))
                cur.execute("INSERT INTO tw_dpae_current_correlation (return_id,submission_id,decision_id,confirmed_at) VALUES (%s,%s,%s,NOW())", (return_id,submission_id,decision_id))
                cur.execute("INSERT INTO tw_dpae_return_effect (return_id,effect_type,created_at) VALUES (%s,'MARK_DPAE_REGISTERED',NOW())", (return_id,))
            conn.commit()
            return {"return_id": return_id, "submission_id": submission_id, "case_id": case_id, "correlation_status": correlation, "duplicate": False}
        except Exception:
            conn.rollback(); raise
        finally: conn.close()

    def get_case(self, case_id):
        conn = self._connect()
        try:
            cur = conn.cursor(); cur.execute("SELECT id,status,version,employee_id,contract_id,establishment_id FROM tw_dpae_case WHERE id=%s", (case_id,)); row = cur.fetchone()
            if not row: return None
            return {"case_id": row[0], "status": row[1], "version": row[2], "employee_id": row[3], "contract_id": row[4], "establishment_id": row[5]}
        finally: conn.close()
