"""Avenants historisés construits sur le Rail A Contrats existant.

Le contrat historique reste la projection courante consommée par le legacy. Un
avenant ajoute d'abord une trace append-only avant/après puis réutilise
``update_contract`` pour les validations, la transaction et le readback.

V1 est volontairement bornée aux clauses déjà modifiables sans changer la
nature du contrat : groupe CCNS, qualification CEE, durée et rémunération.
Renouvellement CDD et CDD -> CDI restent les opérations dédiées du Rail A.
Les avenants à effet futur ne sont pas projetés prématurément : ils sont refusés
jusqu'à l'introduction d'un mécanisme d'activation différée.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import hashlib
import json
import re
from typing import Optional, Protocol

from application.services.contract_write import (
    ContractEditCommand,
    ContractEditSnapshot,
    ContractWritePort,
    update_contract,
)
from application.services.transactional_write import (
    WriteCode,
    WriteResult,
    invalid_target_result,
    is_valid_target_id,
)
from domain.contracts.contract_amendment import (
    ContractAmendmentKind,
    amendment_kind_for_fields,
)


CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"
IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"

_AMENDABLE_FIELDS = (
    "ccns_group",
    "cee_qualification",
    "weekly_hours",
    "gross_monthly_salary",
    "gross_annual_salary",
)
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ContractAmendmentCommand:
    """Demande d'avenant portant l'état cible complet de l'éditeur Rail A."""

    edit: ContractEditCommand
    effective_date: date
    idempotency_key: str
    expected_before_hash: str
    expected_person_id: int


@dataclass(frozen=True)
class ContractAmendmentRecord:
    amendment_id: int
    contract_id: int
    effective_date: date
    kind: str
    idempotency_key: str
    request_hash: str
    changed_fields: tuple[str, ...]
    before_hash: str
    after_hash: str
    before_payload: str
    after_payload: str
    created_at: str


class ContractAmendmentPort(ContractWritePort, Protocol):
    def lock_contract(self, contract_id: int) -> ContractEditSnapshot | None:
        ...

    def find_amendment_by_key(self, idempotency_key: str) -> ContractAmendmentRecord | None:
        ...

    def latest_amendment(self, contract_id: int) -> ContractAmendmentRecord | None:
        ...

    def insert_amendment(
        self,
        *,
        contract_id: int,
        effective_date: date,
        kind: str,
        idempotency_key: str,
        request_hash: str,
        changed_fields: tuple[str, ...],
        before_hash: str,
        after_hash: str,
        before_payload: str,
        after_payload: str,
    ) -> int:
        ...

    def read_amendment(self, amendment_id: int) -> ContractAmendmentRecord | None:
        ...


def _decimal_text(value: Optional[Decimal]) -> Optional[str]:
    if value is None:
        return None
    return format(value, "f")


def _date_text(value: Optional[date]) -> Optional[str]:
    return value.isoformat() if value is not None else None


def contract_state_dict(snapshot: ContractEditSnapshot) -> dict[str, object]:
    """Projection canonique et stable d'un état contractuel."""

    return {
        "contract_id": snapshot.contract_id,
        "person_id": snapshot.person_id,
        "contract_type_code": snapshot.contract_type_code,
        "convention_code": snapshot.convention_code,
        "ccns_group": snapshot.ccns_group,
        "cee_qualification": snapshot.cee_qualification,
        "weekly_hours": _decimal_text(snapshot.weekly_hours),
        "gross_monthly_salary": _decimal_text(snapshot.gross_monthly_salary),
        "gross_annual_salary": _decimal_text(snapshot.gross_annual_salary),
        "start_date": _date_text(snapshot.start_date),
        "end_date": _date_text(snapshot.end_date),
        "break_date": _date_text(snapshot.break_date),
        "operation_type": snapshot.operation_type,
        "previous_contract_id": snapshot.previous_contract_id,
        "legacy_classification_id": snapshot.legacy_classification_id,
        "legacy_point_id": snapshot.legacy_point_id,
        "legacy_trial_days": snapshot.legacy_trial_days,
        "trial_period_value": snapshot.trial_period_value,
        "trial_period_unit": snapshot.trial_period_unit,
    }


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def contract_state_payload(snapshot: ContractEditSnapshot) -> str:
    return _canonical_json(contract_state_dict(snapshot))


def contract_state_hash(snapshot: ContractEditSnapshot) -> str:
    return _hash_text(contract_state_payload(snapshot))


def _target_state_dict(
    original: ContractEditSnapshot,
    edit: ContractEditCommand,
) -> dict[str, object]:
    payload = contract_state_dict(original)
    payload.update(
        {
            "ccns_group": edit.ccns_group,
            "cee_qualification": edit.cee_qualification,
            "weekly_hours": _decimal_text(edit.weekly_hours),
            "gross_monthly_salary": _decimal_text(edit.gross_monthly_salary),
            "gross_annual_salary": _decimal_text(edit.gross_annual_salary),
        }
    )
    return payload


def _request_hash(command: ContractAmendmentCommand) -> str:
    edit = command.edit
    payload = {
        "contract_id": edit.contract_id,
        "expected_person_id": command.expected_person_id,
        "effective_date": _date_text(command.effective_date),
        "contract_type_code": str(edit.contract_type_code or "").strip().upper(),
        "convention_code": edit.convention_code,
        "ccns_group": edit.ccns_group,
        "cee_qualification": edit.cee_qualification,
        "weekly_hours": _decimal_text(edit.weekly_hours),
        "gross_monthly_salary": _decimal_text(edit.gross_monthly_salary),
        "gross_annual_salary": _decimal_text(edit.gross_annual_salary),
    }
    return _hash_text(_canonical_json(payload))


def _changed_fields(
    original: ContractEditSnapshot,
    edit: ContractEditCommand,
) -> tuple[str, ...]:
    return tuple(
        name for name in _AMENDABLE_FIELDS if getattr(original, name) != getattr(edit, name)
    )


def _safe_rollback(port: ContractAmendmentPort) -> None:
    try:
        port.rollback()
    except Exception:
        pass


def _validation_result(contract_id: int, message: str) -> WriteResult[ContractAmendmentRecord]:
    return WriteResult(
        ok=False,
        code=WriteCode.VALIDATION_ERROR,
        message=message,
        target_id=contract_id,
    )


def _replay_result(record: ContractAmendmentRecord) -> WriteResult[ContractAmendmentRecord]:
    return WriteResult(
        ok=True,
        code=IDEMPOTENT_REPLAY,
        message="Avenant déjà enregistré ; replay sans nouvelle écriture.",
        target_id=record.contract_id,
        value=record,
        committed=True,
    )


def apply_contract_amendment(
    port: ContractAmendmentPort,
    *,
    command: ContractAmendmentCommand,
    business_date: Optional[date] = None,
) -> WriteResult[ContractAmendmentRecord]:
    """Historise puis applique atomiquement un avenant sur le contrat courant."""

    edit = command.edit
    if not is_valid_target_id(edit.contract_id):
        return invalid_target_result(edit.contract_id)
    contract_id = edit.contract_id

    if not is_valid_target_id(command.expected_person_id):
        return _validation_result(
            contract_id,
            "L'identifiant de la personne attendue est invalide.",
        )

    if type(command.effective_date) is not date:
        return _validation_result(contract_id, "La date d'effet de l'avenant est invalide.")

    key = str(command.idempotency_key or "").strip()
    if not key or len(key) > 64:
        return _validation_result(
            contract_id,
            "La clé d'idempotence de l'avenant est obligatoire et limitée à 64 caractères.",
        )

    expected_hash = str(command.expected_before_hash or "").strip().lower()
    if not _HASH_RE.match(expected_hash):
        return _validation_result(
            contract_id,
            "L'empreinte de l'état contractuel attendu est invalide.",
        )

    request_hash = _request_hash(command)
    try:
        existing = port.find_amendment_by_key(key)
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Contrôle d'idempotence impossible : %s" % exc,
            target_id=contract_id,
        )

    if existing is not None:
        if existing.contract_id == contract_id and existing.request_hash == request_hash:
            return _replay_result(existing)
        return _validation_result(
            contract_id,
            "La clé d'idempotence est déjà utilisée par un autre avenant.",
        )

    try:
        original = port.lock_contract(contract_id)
    except Exception as exc:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Verrouillage du contrat impossible : %s" % exc,
            target_id=contract_id,
        )

    if original is None:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.TARGET_NOT_FOUND,
            message="Le contrat sélectionné n'existe plus.",
            target_id=contract_id,
        )

    if original.person_id != command.expected_person_id:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "Le contrat sélectionné n'appartient pas à la personne attendue.",
        )

    actual_hash = contract_state_hash(original)
    if actual_hash != expected_hash:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=CONCURRENT_MODIFICATION,
            message="Le contrat a changé depuis son chargement ; rechargez-le avant de créer l'avenant.",
            target_id=contract_id,
        )

    if str(edit.contract_type_code or "").strip().upper() != str(
        original.contract_type_code or ""
    ).strip().upper():
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "Un avenant ne peut pas changer la nature CDI/CDD du contrat.",
        )
    if edit.convention_code != original.convention_code:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "Le changement de convention n'est pas pris en charge par le socle avenants V1.",
        )
    if (
        edit.start_date != original.start_date
        or edit.end_date != original.end_date
        or edit.break_date != original.break_date
    ):
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "Les dates du contrat ne sont pas modifiables par l'avenant V1 ; le renouvellement CDD conserve son parcours dédié.",
        )
    if edit.modern_fields_supported != original.modern_fields_supported:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "Le schéma du contrat a changé depuis son chargement.",
        )

    if command.effective_date < original.start_date:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "La date d'effet de l'avenant est antérieure au début du contrat.",
        )
    if original.end_date is not None and command.effective_date > original.end_date:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "La date d'effet de l'avenant est postérieure à la fin du contrat.",
        )
    if original.break_date is not None and command.effective_date > original.break_date:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "La date d'effet de l'avenant est postérieure à la rupture du contrat.",
        )

    reference_date = business_date if type(business_date) is date else date.today()
    if command.effective_date > reference_date:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "Les avenants à effet futur ne sont pas encore projetés automatiquement ; aucune écriture n'a été faite.",
        )

    try:
        latest = port.latest_amendment(contract_id)
    except Exception as exc:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Lecture de l'historique des avenants impossible : %s" % exc,
            target_id=contract_id,
        )
    if latest is not None and command.effective_date < latest.effective_date:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "Un avenant ne peut pas être antidaté avant le dernier avenant déjà appliqué.",
        )

    changed_fields = _changed_fields(original, edit)
    if not changed_fields:
        _safe_rollback(port)
        return _validation_result(
            contract_id,
            "L'avenant ne modifie aucune clause prise en charge.",
        )

    before_payload = contract_state_payload(original)
    target_state = _target_state_dict(original, edit)
    after_payload = _canonical_json(target_state)
    after_hash = _hash_text(after_payload)
    kind: ContractAmendmentKind = amendment_kind_for_fields(changed_fields)

    try:
        amendment_id = port.insert_amendment(
            contract_id=contract_id,
            effective_date=command.effective_date,
            kind=kind.value,
            idempotency_key=key,
            request_hash=request_hash,
            changed_fields=changed_fields,
            before_hash=actual_hash,
            after_hash=after_hash,
            before_payload=before_payload,
            after_payload=after_payload,
        )
    except Exception as exc:
        _safe_rollback(port)
        try:
            raced = port.find_amendment_by_key(key)
        except Exception:
            raced = None
        if (
            raced is not None
            and raced.contract_id == contract_id
            and raced.request_hash == request_hash
        ):
            return _replay_result(raced)
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Historisation de l'avenant impossible : %s" % exc,
            target_id=contract_id,
        )

    result = update_contract(port, command=edit)
    if not result.committed:
        _safe_rollback(port)
        return WriteResult(
            ok=False,
            code=result.code,
            message=result.message,
            target_id=contract_id,
            committed=False,
        )
    if not result.ok:
        return WriteResult(
            ok=False,
            code=result.code,
            message=result.message,
            target_id=contract_id,
            committed=True,
        )

    if result.value is None or contract_state_hash(result.value) != after_hash:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Avenant validé, mais l'état contractuel relu ne correspond pas à l'état attendu.",
            target_id=contract_id,
            committed=True,
        )

    try:
        record = port.read_amendment(amendment_id)
        if record is None:
            raise LookupError("Avenant introuvable après commit.")
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.READBACK_ERROR,
            message="Avenant validé, mais relecture impossible : %s" % exc,
            target_id=contract_id,
            committed=True,
        )

    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Avenant enregistré et état contractuel relu.",
        target_id=contract_id,
        value=record,
        committed=True,
    )
