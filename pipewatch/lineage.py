"""Metric lineage tracking — record which pipeline produced each metric."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

from pipewatch.metrics import PipelineMetric


@dataclass
class LineageEntry:
    pipeline: str
    metric_name: str
    source: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric_name": self.metric_name,
            "source": self.source,
            "tags": self.tags,
        }


class LineageTracker:
    """Track the origin and lineage of pipeline metrics."""

    def __init__(self) -> None:
        self._entries: Dict[str, LineageEntry] = {}

    def _key(self, pipeline: str, metric_name: str) -> str:
        return f"{pipeline}::{metric_name}"

    def record(self, metric: PipelineMetric, source: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> LineageEntry:
        key = self._key(metric.pipeline, metric.name)
        entry = LineageEntry(
            pipeline=metric.pipeline,
            metric_name=metric.name,
            source=source,
            tags=tags or {},
        )
        self._entries[key] = entry
        return entry

    def get(self, pipeline: str, metric_name: str) -> Optional[LineageEntry]:
        return self._entries.get(self._key(pipeline, metric_name))

    def all_entries(self) -> List[LineageEntry]:
        return list(self._entries.values())

    def by_source(self, source: str) -> List[LineageEntry]:
        return [e for e in self._entries.values() if e.source == source]

    def to_json(self) -> str:
        return json.dumps([e.to_dict() for e in self.all_entries()], indent=2)
