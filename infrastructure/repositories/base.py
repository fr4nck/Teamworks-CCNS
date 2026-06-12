from __future__ import annotations

from typing import Dict, Generic, Iterable, Optional, TypeVar

T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    def __init__(self) -> None:
        self._items: Dict[str, T] = {}

    def add(self, item: T) -> None:
        self._items[getattr(item, "id")] = item

    def get(self, item_id: str) -> Optional[T]:
        return self._items.get(item_id)

    def list_all(self) -> list[T]:
        return list(self._items.values())

    def remove(self, item_id: str) -> None:
        self._items.pop(item_id, None)

    def replace_all(self, items: Iterable[T]) -> None:
        self._items = {getattr(item, "id"): item for item in items}
