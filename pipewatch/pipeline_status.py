"""Aggregate per-pipeline status from a collector snapshot."""
from dataclasses import dataclass, field
from typing import Dict, List
from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class PipelineStatus:
    pipeline: str
    metrics: List[PipelineMetric] = field(default_factory=list)

    @property
    def overall_status(self) -> MetricStatus:
        if any(m.status == MetricStatus.CRITICAL for m in self.metrics):
            return MetricStatus.CRITICAL
        if any(m.status == MetricStatus.WARNING for m in self.metrics):
            return MetricStatus.WARNING
        return MetricStatus.OK

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "overall_status": self.overall_status.value,
            "metrics": [m.to_dict() for m in self.metrics],
        }


class PipelineStatusBoard:
    """Groups metrics by pipeline and exposes per-pipeline status."""

    def __init__(self) -> None:
        self._pipelines: Dict[str, PipelineStatus] = {}

    def ingest(self, metrics: List[PipelineMetric]) -> None:
        self._pipelines.clear()
        for m in metrics:
            key = m.pipeline
            if key not in self._pipelines:
                self._pipelines[key] = PipelineStatus(pipeline=key)
            self._pipelines[key].metrics.append(m)

    def get(self, pipeline: str) -> PipelineStatus | None:
        return self._pipelines.get(pipeline)

    def all(self) -> List[PipelineStatus]:
        return list(self._pipelines.values())

    def critical_pipelines(self) -> List[PipelineStatus]:
        return [p for p in self.all() if p.overall_status == MetricStatus.CRITICAL]

    def to_dict(self) -> dict:
        return {p.pipeline: p.to_dict() for p in self.all()}
