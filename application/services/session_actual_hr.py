"""Façade applicative de réception du réalisé validé pour ``hr_employment``."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional

from domain.employment import SOURCE_DOMAIN
from infrastructure.persistence.session_actual_hr_repository import (
    SessionActualHrRepository,
    SessionActualReceiveResult,
)


class SessionActualHrConsumer:
    """Point d'entrée applicatif indépendant du transport réseau."""

    def __init__(self, repository: Optional[SessionActualHrRepository] = None):
        self.repository = repository or SessionActualHrRepository()

    def receive(
        self,
        payload: Mapping[str, Any],
        idempotence_key: str,
        source_domain: str = SOURCE_DOMAIN,
        received_at: Optional[datetime] = None,
    ) -> SessionActualReceiveResult:
        return self.repository.receive(
            payload=payload,
            idempotence_key=idempotence_key,
            source_domain=source_domain,
            received_at=received_at,
        )

    def close(self) -> None:
        self.repository.close()
