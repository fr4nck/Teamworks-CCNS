"""Détection commune des cycles dans les chaînes de reports de scénarios.

Le domaine ne dépend ni de wx ni de Qt et ne choisit aucun message d'interface.
Les adaptateurs peuvent traduire :class:`ReportCycleError` vers leur contrat UI.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import threading
from typing import Iterator


@dataclass(frozen=True)
class ReportNode:
    scenario_id: int
    category_id: int


class ReportCycleError(RuntimeError):
    """Signale qu'un nœud de report est revisité dans la chaîne courante."""

    def __init__(self, cycle: tuple[ReportNode, ...]):
        self.cycle = cycle
        path = " -> ".join(
            f"scenario={node.scenario_id}/categorie={node.category_id}"
            for node in cycle
        )
        super().__init__(f"Cycle de reports détecté : {path}")


class ReportCycleGuard:
    """Garde réutilisable et locale au thread pour un calcul de reports imbriqué."""

    def __init__(self) -> None:
        self._state = threading.local()

    @staticmethod
    def _node(scenario_id, category_id) -> ReportNode:
        return ReportNode(int(scenario_id), int(category_id))

    @contextmanager
    def enter(self, scenario_id, category_id) -> Iterator[ReportNode]:
        node = self._node(scenario_id, category_id)
        stack = getattr(self._state, "stack", None)
        root = stack is None
        if root:
            stack = []
            self._state.stack = stack

        if node in stack:
            start = stack.index(node)
            cycle = tuple(stack[start:] + [node])
            if root and hasattr(self._state, "stack"):
                del self._state.stack
            raise ReportCycleError(cycle)

        stack.append(node)
        try:
            yield node
        finally:
            stack.pop()
            if root and hasattr(self._state, "stack"):
                del self._state.stack


DEFAULT_REPORT_CYCLE_GUARD = ReportCycleGuard()
