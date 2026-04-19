"""Periodic metric rollup: aggregate metrics over a time window into a summary record."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

from pipewatch.metrics import PipelineMetric


@dataclass
class RollupWindow:
    pipeline: str
    metric_name: str
    window_seconds: float
    _samples: List[float] = field(default_factory=list, repr=False)
    _timestamps: List[float] = field(default_factory=list, repr=False)

    def add(self, metric: PipelineMetric) -> None:
        now = time.time()
        self._samples.append(metric.value)
        self._timestamps.append(now)
        self._prune(now)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        pairs = [(t, v) for t, v in zip(self._timestamps, self._samples) if t >= cutoff]
        if pairs:
            self._timestamps, self._samples = map(list, zip(*pairs))
        else:
            self._timestamps, self._samples = [], []

    def count(self) -> int:
        return len(self._samples)

    def mean(self) -> Optional[float]:
        return sum(self._samples) / len(self._samples) if self._samples else None

    def minimum(self) -> Optional[float]:
        return min(self._samples) if self._samples else None

    def maximum(self) -> Optional[float]:
        return max(self._samples) if self._samples else None

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric_name": self.metric_name,
            "window_seconds": self.window_seconds,
            "count": self.count(),
            "mean": self.mean(),
            "min": self.minimum(),
            "max": self.maximum(),
        }


class MetricRollup:
    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window_seconds = window_seconds
        self._windows: Dict[str, RollupWindow] = {}

    def _key(self, metric: PipelineMetric) -> str:
        return f"{metric.pipeline}::{metric.name}"

    def record(self, metric: PipelineMetric) -> RollupWindow:
        key = self._key(metric)
        if key not in self._windows:
            self._windows[key] = RollupWindow(
                pipeline=metric.pipeline,
                metric_name=metric.name,
                window_seconds=self.window_seconds,
            )
        self._windows[key].add(metric)
        return self._windows[key]

    def get(self, pipeline: str, metric_name: str) -> Optional[RollupWindow]:
        return self._windows.get(f"{pipeline}::{metric_name}")

    def all_windows(self) -> List[RollupWindow]:
        return list(self._windows.values())
