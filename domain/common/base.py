from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Entity:
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def touch(self) -> None:
        self.updated_at = utcnow()
