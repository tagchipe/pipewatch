from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import statistics
from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class ProfileEntry:
    pipeline: str
    metric_name: str
    samples: List[float] = field(default_factory=list)

    def record(self, value: float) -> None:
        self.samples.append(value)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def mean(self) -> Optional[float]:
        return statistics.mean(self.samples) if self.samples else None

    @property
    def stddev(self) -> Optional[float]:
        return statistics.pstdev(self.samples) if len(self.samples) >= 2 else None

    @property
    def p95(self) -> Optional[float]:
        if not self.samples:
            return None
        sorted_s = sorted(self.samples)
        idx = max(0, int(len(sorted_s) * 0.95) - 1)
        return sorted_s[idx]

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric_name": self.metric_name,
            "count": self.count,
            "mean": self.mean,
            "stddev": self.stddev,
            "p95": self.p95,
        }


class MetricProfiler:
    def __init__(self) -> None:
        self._entries: Dict[str, ProfileEntry] = {}

    def _key(self, pipeline: str, metric_name: str) -> str:
        return f"{pipeline}::{metric_name}"

    def record(self, metric: PipelineMetric) -> ProfileEntry:
        key = self._key(metric.pipeline, metric.name)
        if key not in self._entries:
            self._entries[key] = ProfileEntry(pipeline=metric.pipeline, metric_name=metric.name)
        self._entries[key].record(metric.value)
        return self._entries[key]

    def get(self, pipeline: str, metric_name: str) -> Optional[ProfileEntry]:
        return self._entries.get(self._key(pipeline, metric_name))

    def all_entries(self) -> List[ProfileEntry]:
        return list(self._entries.values())

    def summary(self) -> List[dict]:
        return [e.to_dict() for e in self.all_entries()]
