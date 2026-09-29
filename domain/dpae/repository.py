"""Ports de persistance et implémentation mémoire pour le domaine DPAE."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock
from typing import Dict, List, Optional, Tuple

from .model import DpaeCorrelationDecision, DpaeDomainError, DpaeReturn, DpaeReturnEffect


@dataclass
class InMemoryDpaeRepository:
    returns: Dict[str, DpaeReturn] = field(default_factory=dict)
    decisions: List[DpaeCorrelationDecision] = field(default_factory=list)
    effects: Dict[Tuple[str, str], DpaeReturnEffect] = field(default_factory=dict)
    _external_identity: Dict[Tuple[str, str], str] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock, repr=False)

    def ingest_return(self, item: DpaeReturn) -> Tuple[DpaeReturn, str]:
        """Déduplique un retour externe et détecte une collision d'intégrité."""
        with self._lock:
            if item.external_return_id:
                key = (item.provider, item.external_return_id)
                existing_id = self._external_identity.get(key)
                if existing_id:
                    existing = self.returns[existing_id]
                    if existing.raw_hash != item.raw_hash:
                        raise DpaeDomainError(
                            "RETURN_INTEGRITY_CONFLICT",
                            "Même identifiant de retour externe avec un contenu différent.",
                        )
                    return deepcopy(existing), "REPLAY"
                self._external_identity[key] = item.id
            if item.id in self.returns:
                existing = self.returns[item.id]
                if existing.raw_hash != item.raw_hash:
                    raise DpaeDomainError("RETURN_INTEGRITY_CONFLICT", "Identifiant interne réutilisé.")
                return deepcopy(existing), "REPLAY"
            self.returns[item.id] = deepcopy(item)
            return deepcopy(item), "CREATED"

    def get_return(self, return_id: str) -> DpaeReturn:
        with self._lock:
            return deepcopy(self.returns[return_id])

    def confirm_correlation(
        self, return_id: str, submission_id: str, case_id: str, expected_version: int
    ) -> str:
        """Compare-and-swap atomique ; l'adaptateur SQL devra préserver ce contrat."""
        with self._lock:
            item = self.returns[return_id]
            result = item.confirm_correlation(submission_id, case_id, expected_version)
            self.returns[return_id] = item
            return result

    def append_decision(self, decision: DpaeCorrelationDecision) -> None:
        with self._lock:
            if any(existing.id == decision.id for existing in self.decisions):
                return
            self.decisions.append(decision)

    def record_effect_once(self, effect: DpaeReturnEffect) -> bool:
        with self._lock:
            item = self.returns[effect.return_id]
            if not item.may_have_business_effect:
                raise DpaeDomainError(
                    "DPAE_UNCONFIRMED_RETURN_EFFECT",
                    "Un retour non confirmé ne peut produire aucun effet métier.",
                )
            key = (effect.return_id, effect.effect_type)
            if key in self.effects:
                return False
            self.effects[key] = effect
            return True

    def effect_count(self, return_id: str, effect_type: str) -> int:
        with self._lock:
            return int((return_id, effect_type) in self.effects)
