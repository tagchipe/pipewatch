"""Metric history tracking for trend detection."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional
from pipewatch.metrics import PipelineMetric


@dataclass
class MetricHistory:
    pipeline: str
    name: str
    max_size: int = 100
    _entries: Deque[PipelineMetric] = field(default_factory=deque, repr=False)

    def add(self, metric: PipelineMetric) -> None:
        if len(self._entries) >= self.max_size:
            self._entries.popleft()
        self._entries.append(metric)

    def values(self) -> List[float]:
        return [m.value for m in self._entries]

    def latest(self) -> Optional[PipelineMetric]:
        return self._entries[-1] if self._entries else None

    def trend(self) -> Optional[str]:
        """Return 'up', 'down', or 'stable' based on last 3 entries."""
        vals = self.values()
        if len(vals) < 2:
            return None
        recent = vals[-min(3, len(vals)):]
        if recent[-1] > recent[0]:
            return "up"
        elif recent[-1] < recent[0]:
            return "down"
        return "stable"

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "name": self.name,
            "count": len(self._entries),
            "latest": self.latest().value if self.latest() else None,
            "trend": self.trend(),
            "values": self.values(),
        }


class HistoryTracker:
    def __init__(self, max_size: int = 100) -> None:
        self.max_size = max_size
        self._store: Dict[tuple, MetricHistory] = {}

    def _key(self, metric: PipelineMetric) -> tuple:
        return (metric.pipeline, metric.name)

    def record(self, metric: PipelineMetric) -> None:
        key = self._key(metric)
        if key not in self._store:
            self._store[key] = MetricHistory(
                pipeline=metric.pipeline,
                name=metric.name,
                max_size=self.max_size,
            )
        self._store[key].add(metric)

    def get(self, pipeline: str, name: str) -> Optional[MetricHistory]:
        return self._store.get((pipeline, name))

    def all_histories(self) -> List[MetricHistory]:
        return list(self._store.values())
