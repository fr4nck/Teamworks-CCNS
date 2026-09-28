"""Adaptateur MariaDB/MySQL du service DPAE — DATA-001 / V2."""
import hashlib
import uuid


class IdempotencyPayloadConflict(Exception):
    pass


class InvalidDpaeTransition(Exception):
    pass


class DpaeMariaDbAdapter:
    def __init__(self, connection_factory, failure_injector=None):
        self._connect = connection_factory
        self._failure_injector = failure_injector

    @staticmethod
    def _id(): return uuid.uuid4().hex

    @staticmethod
    def _hash(*parts):
        raw = "\x1f".join(str(part) for part in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _failure_point(self, name):
        if self._failure_injector is not None: self._failure_injector(name)

    def _prepare_command_hash(self, cmd): return self._hash(cmd.case_key, cmd.contract_id)

    def replay_prepare(self, cmd):
        conn = self._connect()
        try:
            cur = conn.cursor(); cur.execute("SELECT command_hash,case_id,decision FROM tw_dpae_command_audit WHERE command_id=%s", (cmd.command_id,)); previous = cur.fetchone()
            if not previous: return None
            if previous[0] != self._prepare_command_hash(cmd): raise IdempotencyPayloadConflict("IDEMPOTENCY_PAYLOAD_CONFLICT")
            cur.execute("SELECT id,payload_hash FROM tw_dpae_snapshot WHERE case_id=%s ORDER BY created_at DESC,id DESC LIMIT 1", (previous[1],)); snapshot = cur.fetchone()
            return {"case_id": previous[1], "snapshot_id": snapshot[0] if snapshot else None, "payload_hash": snapshot[1] if snapshot else None, "status": "READY", "replayed": True}
        finally: conn.close()

    def prepare(self, cmd, business_data):
        conn = self._connect()
        try:
            cur = conn.cursor(); command_hash = self._prepare_command_hash(cmd)
            cur.execute("SELECT command_hash,case_id,decision FROM tw_dpae_command_audit WHERE command_id=%s FOR UPDATE", (cmd.command_id,)); previous = cur.fetchone()
            if previous:
                if previous[0] != command_hash: raise IdempotencyPayloadConflict("IDEMPOTENCY_PAYLOAD_CONFLICT")
                conn.rollback(); return {"case_id": previous[1], "status": "READY", "replayed": True}
            case_id = self._id(); snapshot_id = self._id()
            cur.execute("INSERT INTO tw_dpae_case (id,case_key,contract_id,status,origin,created_at,version) VALUES (%s,%s,%s,'READY','TEAMWORKS',NOW(),0)", (case_id, cmd.case_key, cmd.contract_id))
            cur.execute("INSERT INTO tw_dpae_snapshot (id,case_id,contract_id,rules_version,source_fingerprint,canonical_payload,payload_hash,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())", (snapshot_id, case_id, cmd.contract_id, business_data.rules_version, business_data.source_fingerprint, business_data.canonical_payload, business_data.payload_hash))
            self._failure_point("after_snapshot_write")
            cur.execute("INSERT INTO tw_dpae_command_audit (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,requested_at,decided_at,decision,case_version_seen) VALUES (%s,%s,'PrepareDpae',%s,'USER',%s,%s,NOW(),NOW(),'APPLIED',0)", (self._id(), cmd.command_id, command_hash, cmd.actor_id, case_id))
            conn.commit(); return {"case_id": case_id, "snapshot_id": snapshot_id, "payload_hash": business_data.payload_hash, "status": "READY", "replayed": False}
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def submit(self, cmd):
        conn = self._connect()
        try:
            cur = conn.cursor(); cur.execute("SELECT id,payload_hash,canonical_payload FROM tw_dpae_snapshot WHERE case_id=%s ORDER BY created_at DESC,id DESC LIMIT 1 FOR UPDATE", (cmd.case_id,)); snapshot = cur.fetchone()
            if not snapshot: raise InvalidDpaeTransition("DPAE_SNAPSHOT_REQUIRED")
            snapshot_id, payload_hash, canonical_payload = snapshot; command_hash = self._hash(cmd.case_id, snapshot_id, payload_hash)
            cur.execute("SELECT command_hash,case_id,submission_id,decision FROM tw_dpae_command_audit WHERE command_id=%s", (cmd.command_id,)); previous = cur.fetchone()
            if previous:
                if previous[0] != command_hash: raise IdempotencyPayloadConflict("IDEMPOTENCY_PAYLOAD_CONFLICT")
                conn.rollback(); return {"case_id": previous[1], "submission_id": previous[2], "decision": previous[3], "payload_hash": payload_hash, "canonical_payload": canonical_payload, "snapshot_id": snapshot_id, "replayed": True}
            cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s FOR UPDATE", (cmd.case_id,)); case = cur.fetchone()
            if case != ("READY", 0): raise InvalidDpaeTransition("DPAE_NOT_SUBMITTABLE")
            submission_id = self._id(); cur.execute("UPDATE tw_dpae_case SET status='SUBMITTING',version=1 WHERE id=%s AND version=0", (cmd.case_id,))
            cur.execute("INSERT INTO tw_dpae_submission (id,case_id,snapshot_id,attempt_no,idempotency_key,payload_hash,state,created_at,version) VALUES (%s,%s,%s,1,%s,%s,'PREPARED',NOW(),0)", (submission_id, cmd.case_id, snapshot_id, cmd.command_id, payload_hash))
            self._failure_point("after_submission_write")
            cur.execute("INSERT INTO tw_dpae_case_event (id,case_id,event_type,state_before,state_after,version_before,version_after,actor_type,actor_id,idempotency_key,command_hash,occurred_at,recorded_at) VALUES (%s,%s,'SUBMISSION_REQUESTED','READY','SUBMITTING',0,1,'USER',%s,%s,%s,NOW(),NOW())", (self._id(), cmd.case_id, cmd.actor_id, cmd.command_id, command_hash)); self._failure_point("after_case_event_write")
            cur.execute("INSERT INTO tw_dpae_command_audit (id,command_id,command_type,command_hash,actor_type,actor_id,case_id,submission_id,requested_at,decided_at,decision,case_version_seen) VALUES (%s,%s,'SubmitDpae',%s,'USER',%s,%s,%s,NOW(),NOW(),'APPLIED',0)", (self._id(), cmd.command_id, command_hash, cmd.actor_id, cmd.case_id, submission_id))
            conn.commit(); return {"case_id": cmd.case_id, "submission_id": submission_id, "snapshot_id": snapshot_id, "payload_hash": payload_hash, "canonical_payload": canonical_payload, "decision": "APPLIED", "replayed": False}
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def start_transmission(self, submission_id):
        conn = self._connect()
        try:
            cur=conn.cursor(); cur.execute("SELECT state,version FROM tw_dpae_submission WHERE id=%s FOR UPDATE",(submission_id,)); row=cur.fetchone()
            if row != ("PREPARED",0): raise InvalidDpaeTransition("SUBMISSION_NOT_SENDABLE")
            cur.execute("UPDATE tw_dpae_submission SET state='SENDING',version=1 WHERE id=%s AND version=0",(submission_id,)); conn.commit()
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def retry_submission(self, submission_id):
        """Réarme la même tentative incertaine et recharge exclusivement son snapshot durable.

        ``UNKNOWN`` reste accepté en lecture pour les lignes écrites par les premières
        itérations de #477 ; toute nouvelle écriture utilise le vocabulaire du domaine.
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT s.case_id,s.snapshot_id,s.payload_hash,s.attempt_no,s.state,s.version,p.canonical_payload,p.payload_hash FROM tw_dpae_submission s JOIN tw_dpae_snapshot p ON p.id=s.snapshot_id WHERE s.id=%s FOR UPDATE", (submission_id,))
            row = cur.fetchone()
            if not row or row[4] not in ("OUTCOME_UNKNOWN", "UNKNOWN"): raise InvalidDpaeTransition("SUBMISSION_NOT_RETRYABLE")
            case_id, snapshot_id, payload_hash, attempt_no, _state, version, canonical_payload, snapshot_hash = row
            if payload_hash != snapshot_hash: raise InvalidDpaeTransition("SUBMISSION_SNAPSHOT_HASH_MISMATCH")
            cur.execute("UPDATE tw_dpae_submission SET state='SENDING',version=%s WHERE id=%s AND version=%s", (version + 1, submission_id, version))
            if cur.rowcount != 1: raise InvalidDpaeTransition("SUBMISSION_RETRY_RACE")
            conn.commit()
            return {"case_id": case_id, "submission_id": submission_id, "snapshot_id": snapshot_id, "payload_hash": payload_hash, "canonical_payload": canonical_payload, "attempt_no": attempt_no, "replayed": False}
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def finish_transmission(self, submission_id, result):
        transport_to_submission = {
            "SENT": "TECHNICALLY_ACCEPTED",
            "REJECTED": "REJECTED",
            "UNKNOWN": "OUTCOME_UNKNOWN",
        }
        if result.outcome not in transport_to_submission: raise ValueError("invalid transmission outcome")
        submission_state = transport_to_submission[result.outcome]
        conn=self._connect()
        try:
            cur=conn.cursor(); cur.execute("SELECT state,version,case_id FROM tw_dpae_submission WHERE id=%s FOR UPDATE",(submission_id,)); row=cur.fetchone()
            if not row or row[0] != "SENDING": raise InvalidDpaeTransition("INVALID_SUBMISSION_TRANSITION")
            version=row[1]; case_id=row[2]; completed=result.outcome in ("SENT","REJECTED")
            cur.execute("UPDATE tw_dpae_submission SET state=%s,external_flux_id=%s,sent_at=CASE WHEN %s='SENT' THEN NOW() ELSE sent_at END,completed_at=CASE WHEN %s THEN NOW() ELSE completed_at END,version=%s WHERE id=%s AND version=%s",(submission_state,result.external_flux_id,result.outcome,completed,version+1,submission_id,version))
            if cur.rowcount != 1: raise InvalidDpaeTransition("SUBMISSION_FINISH_RACE")
            if result.outcome in ("SENT","REJECTED","UNKNOWN"):
                case_state = {"SENT": "WAITING_RETURN", "REJECTED": "REJECTED", "UNKNOWN": "OUTCOME_UNKNOWN"}[result.outcome]
                cur.execute("SELECT status,version FROM tw_dpae_case WHERE id=%s FOR UPDATE",(case_id,)); case=cur.fetchone()
                if case and case[0] in ("SUBMITTING","OUTCOME_UNKNOWN","UNKNOWN"):
                    cur.execute("UPDATE tw_dpae_case SET status=%s,version=%s WHERE id=%s AND version=%s",(case_state,case[1]+1,case_id,case[1]))
            conn.commit()
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def ingest_return(self, cmd):
        conn=self._connect()
        try:
            cur=conn.cursor()
            if cmd.external_return_id:
                cur.execute("SELECT id,submission_id,case_id,correlation_status,raw_hash FROM tw_dpae_return WHERE provider=%s AND external_return_id=%s",(cmd.provider,cmd.external_return_id)); previous=cur.fetchone()
                if previous:
                    if previous[4] != cmd.raw_hash: raise ValueError("RETURN_INTEGRITY_CONFLICT")
                    conn.rollback(); return {"return_id":previous[0],"submission_id":previous[1],"case_id":previous[2],"correlation_status":previous[3],"duplicate":True}
            return_id=self._id(); submission_id=case_id=None; correlation="UNMATCHED"
            if cmd.external_flux_id:
                cur.execute("SELECT id,case_id FROM tw_dpae_submission WHERE external_flux_id=%s",(cmd.external_flux_id,)); candidates=cur.fetchall()
                if len(candidates)==1: submission_id,case_id=candidates[0]; correlation="MATCHED"
                elif len(candidates)>1: correlation="AMBIGUOUS"
            cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,external_flux_id,employer_siret,submission_id,case_id,correlation_status,processing_status,version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PROCESSED',1)",(return_id,cmd.provider,cmd.return_type,cmd.raw_hash,cmd.received_at,cmd.external_return_id,cmd.external_flux_id,cmd.employer_siret,submission_id,case_id,correlation))
            if correlation=="MATCHED":
                decision_id=self._id(); cur.execute("INSERT INTO tw_dpae_correlation_decision (id,return_id,action,actor_id,decided_at,candidate_submission_id,reason_code) VALUES (%s,%s,'CONFIRM_MATCH','DPAE_RETURN_CORRELATOR',NOW(),%s,'EXTERNAL_FLUX_ID_EXACT')",(decision_id,return_id,submission_id)); cur.execute("INSERT INTO tw_dpae_current_correlation (return_id,submission_id,decision_id,confirmed_at) VALUES (%s,%s,%s,NOW())",(return_id,submission_id,decision_id)); cur.execute("INSERT INTO tw_dpae_return_effect (return_id,effect_type,created_at) VALUES (%s,'MARK_DPAE_REGISTERED',NOW())",(return_id,))
            conn.commit(); return {"return_id":return_id,"submission_id":submission_id,"case_id":case_id,"correlation_status":correlation,"duplicate":False}
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def get_historical_evidence(self, return_id):
        """Projection de preuve purement transactionnelle : aucun accès au resolver RH."""
        conn = self._connect()
        try:
            cur = conn.cursor(); cur.execute("SELECT r.id,s.id,p.id,c.id,c.contract_id,p.canonical_payload,p.payload_hash FROM tw_dpae_return r JOIN tw_dpae_submission s ON s.id=r.submission_id JOIN tw_dpae_snapshot p ON p.id=s.snapshot_id JOIN tw_dpae_case c ON c.id=p.case_id WHERE r.id=%s", (return_id,)); row = cur.fetchone()
            if not row: return None
            return {"return_id": row[0], "submission_id": row[1], "snapshot_id": row[2], "case_id": row[3], "contract_id": str(row[4]), "canonical_payload": row[5], "payload_hash": row[6]}
        finally: conn.close()

    def get_case(self, case_id):
        conn=self._connect()
        try:
            cur=conn.cursor(); cur.execute("SELECT id,status,version,contract_id FROM tw_dpae_case WHERE id=%s",(case_id,)); row=cur.fetchone(); return None if not row else {"case_id":row[0],"status":row[1],"version":row[2],"contract_id":row[3]}
        finally: conn.close()