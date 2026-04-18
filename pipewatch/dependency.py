"""Pipeline dependency tracking and upstream/downstream health propagation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pipewatch.metrics import MetricStatus


@dataclass
class DependencyNode:
    name: str
    upstream: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "upstream": list(self.upstream)}


@dataclass
class PropagationResult:
    pipeline: str
    direct_status: MetricStatus
    propagated_status: MetricStatus
    blocking_pipelines: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "direct_status": self.direct_status.value,
            "propagated_status": self.propagated_status.value,
            "blocking_pipelines": self.blocking_pipelines,
        }


class DependencyGraph:
    def __init__(self) -> None:
        self._nodes: Dict[str, DependencyNode] = {}

    def register(self, pipeline: str, upstream: Optional[List[str]] = None) -> None:
        self._nodes[pipeline] = DependencyNode(name=pipeline, upstream=upstream or [])

    def upstream_of(self, pipeline: str) -> List[str]:
        node = self._nodes.get(pipeline)
        return list(node.upstream) if node else []

    def all_upstream(self, pipeline: str) -> Set[str]:
        visited: Set[str] = set()
        stack = list(self.upstream_of(pipeline))
        while stack:
            p = stack.pop()
            if p not in visited:
                visited.add(p)
                stack.extend(self.upstream_of(p))
        return visited

    def evaluate(self, pipeline: str, statuses: Dict[str, MetricStatus]) -> PropagationResult:
        direct = statuses.get(pipeline, MetricStatus.OK)
        blocking = [
            p for p in self.all_upstream(pipeline)
            if statuses.get(p, MetricStatus.OK) == MetricStatus.CRITICAL
        ]
        if blocking:
            propagated = MetricStatus.CRITICAL
        elif any(statuses.get(p, MetricStatus.OK) == MetricStatus.WARNING for p in self.all_upstream(pipeline)):
            propagated = MetricStatus.WARNING if direct == MetricStatus.OK else direct
        else:
            propagated = direct
        return PropagationResult(
            pipeline=pipeline,
            direct_status=direct,
            propagated_status=propagated,
            blocking_pipelines=blocking,
        )

    def pipelines(self) -> List[str]:
        return list(self._nodes.keys())
