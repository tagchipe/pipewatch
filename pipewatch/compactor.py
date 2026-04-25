"""Metric compaction: merge multiple metric snapshots into a single summary record."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class CompactedMetric:
    pipeline: str
    name: str
    count: int
    min_value: float
    max_value: float
    mean_value: float
    dominant_status: MetricStatus

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "name": self.name,
            "count": self.count,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mean_value": round(self.mean_value, 4),
            "dominant_status": self.dominant_status.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class MetricCompactor:
    """Collapses a list of PipelineMetric instances into per-(pipeline, name) summaries."""

    def compact(self, metrics: List[PipelineMetric]) -> List[CompactedMetric]:
        groups: Dict[tuple, List[PipelineMetric]] = {}
        for m in metrics:
            key = (m.pipeline, m.name)
            groups.setdefault(key, []).append(m)

        results: List[CompactedMetric] = []
        for (pipeline, name), group in groups.items():
            values = [m.value for m in group]
            statuses = [m.status for m in group]
            dominant = self._dominant_status(statuses)
            results.append(
                CompactedMetric(
                    pipeline=pipeline,
                    name=name,
                    count=len(values),
                    min_value=min(values),
                    max_value=max(values),
                    mean_value=sum(values) / len(values),
                    dominant_status=dominant,
                )
            )
        return results

    @staticmethod
    def _dominant_status(statuses: List[MetricStatus]) -> MetricStatus:
        priority = {MetricStatus.CRITICAL: 2, MetricStatus.WARNING: 1, MetricStatus.OK: 0}
        return max(statuses, key=lambda s: priority.get(s, 0))
