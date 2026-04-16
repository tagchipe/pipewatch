"""Aggregation utilities for pipeline metrics over time windows."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict, deque
import time

from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class AggregatedStats:
    pipeline: str
    name: str
    count: int
    mean: float
    min_val: float
    max_val: float
    latest_status: MetricStatus

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "name": self.name,
            "count": self.count,
            "mean": round(self.mean, 4),
            "min": self.min_val,
            "max": self.max_val,
            "latest_status": self.latest_status.value,
        }


class MetricAggregator:
    """Stores recent metrics in a sliding window and computes stats."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._buckets: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))

    def _key(self, metric: PipelineMetric) -> str:
        return f"{metric.pipeline}::{metric.name}"

    def record(self, metric: PipelineMetric) -> None:
        self._buckets[self._key(metric)].append(metric)

    def stats(self, pipeline: str, name: str) -> Optional[AggregatedStats]:
        key = f"{pipeline}::{name}"
        bucket = self._buckets.get(key)
        if not bucket:
            return None
        values = [m.value for m in bucket]
        return AggregatedStats(
            pipeline=pipeline,
            name=name,
            count=len(values),
            mean=sum(values) / len(values),
            min_val=min(values),
            max_val=max(values),
            latest_status=bucket[-1].status,
        )

    def all_stats(self) -> List[AggregatedStats]:
        results = []
        for key in self._buckets:
            pipeline, name = key.split("::", 1)
            s = self.stats(pipeline, name)
            if s:
                results.append(s)
        return results
