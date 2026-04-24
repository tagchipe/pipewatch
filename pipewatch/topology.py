"""Pipeline topology mapper — tracks pipeline relationships and computes execution order."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class TopologyNode:
    name: str
    upstream: List[str] = field(default_factory=list)
    downstream: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "upstream": list(self.upstream),
            "downstream": list(self.downstream),
        }


@dataclass
class TopologyResult:
    order: List[str]  # topological sort
    cycles: List[List[str]]  # detected cycles

    def to_dict(self) -> dict:
        return {"order": self.order, "cycles": self.cycles}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @property
    def has_cycles(self) -> bool:
        return len(self.cycles) > 0


class TopologyMapper:
    def __init__(self) -> None:
        self._nodes: Dict[str, TopologyNode] = {}

    def add_pipeline(self, name: str) -> TopologyNode:
        if name not in self._nodes:
            self._nodes[name] = TopologyNode(name=name)
        return self._nodes[name]

    def add_edge(self, upstream: str, downstream: str) -> None:
        """Register that *downstream* depends on *upstream*."""
        self.add_pipeline(upstream)
        self.add_pipeline(downstream)
        node_up = self._nodes[upstream]
        node_dn = self._nodes[downstream]
        if downstream not in node_up.downstream:
            node_up.downstream.append(downstream)
        if upstream not in node_dn.upstream:
            node_dn.upstream.append(upstream)

    def get(self, name: str) -> Optional[TopologyNode]:
        return self._nodes.get(name)

    def all_nodes(self) -> List[TopologyNode]:
        return list(self._nodes.values())

    def evaluate(self) -> TopologyResult:
        """Return a topological sort and any detected cycles (Kahn's algorithm)."""
        in_degree: Dict[str, int] = {n: len(self._nodes[n].upstream) for n in self._nodes}
        queue = [n for n, d in in_degree.items() if d == 0]
        order: List[str] = []

        while queue:
            queue.sort()  # deterministic output
            node = queue.pop(0)
            order.append(node)
            for child in sorted(self._nodes[node].downstream):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        cycles: List[List[str]] = []
        remaining = [n for n in self._nodes if n not in order]
        if remaining:
            cycles.append(remaining)

        return TopologyResult(order=order, cycles=cycles)
