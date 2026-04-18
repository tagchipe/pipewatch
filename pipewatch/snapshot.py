"""Snapshot: capture and compare point-in-time metric state."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import json

from pipewatch.metrics import PipelineMetric


@dataclass
class Snapshot:
    name: str
    captured_at: datetime
    metrics: List[PipelineMetric]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "captured_at": self.captured_at.isoformat(),
            "metrics": [m.to_dict() for m in self.metrics],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class DiffEntry:
    pipeline: str
    metric_name: str
    before: Optional[float]
    after: Optional[float]

    @property
    def delta(self) -> Optional[float]:
        if self.before is not None and self.after is not None:
            return self.after - self.before
        return None

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric_name": self.metric_name,
            "before": self.before,
            "after": self.after,
            "delta": self.delta,
        }


class SnapshotManager:
    def __init__(self) -> None:
        self._snapshots: Dict[str, Snapshot] = {}

    def capture(self, name: str, metrics: List[PipelineMetric]) -> Snapshot:
        snap = Snapshot(name=name, captured_at=datetime.utcnow(), metrics=list(metrics))
        self._snapshots[name] = snap
        return snap

    def get(self, name: str) -> Optional[Snapshot]:
        return self._snapshots.get(name)

    def diff(self, before_name: str, after_name: str) -> List[DiffEntry]:
        before = self._snapshots.get(before_name)
        after = self._snapshots.get(after_name)
        if not before or not after:
            return []

        def _key(m: PipelineMetric):
            return (m.pipeline, m.name)

        before_map = {_key(m): m.value for m in before.metrics}
        after_map = {_key(m): m.value for m in after.metrics}
        all_keys = set(before_map) | set(after_map)

        return [
            DiffEntry(
                pipeline=k[0],
                metric_name=k[1],
                before=before_map.get(k),
                after=after_map.get(k),
            )
            for k in sorted(all_keys)
        ]
