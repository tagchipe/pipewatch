"""Periodic digest summarizing pipeline health across all metrics."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
import json

from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class DigestEntry:
    pipeline: str
    total: int
    ok: int
    warning: int
    critical: int
    worst_status: MetricStatus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline": self.pipeline,
            "total": self.total,
            "ok": self.ok,
            "warning": self.warning,
            "critical": self.critical,
            "worst_status": self.worst_status.value,
        }


@dataclass
class Digest:
    generated_at: str
    entries: List[DigestEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "entries": [e.to_dict() for e in self.entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class DigestBuilder:
    """Builds a Digest from a collection of PipelineMetric instances."""

    def build(self, metrics: List[PipelineMetric]) -> Digest:
        buckets: Dict[str, List[PipelineMetric]] = {}
        for m in metrics:
            buckets.setdefault(m.pipeline, []).append(m)

        entries: List[DigestEntry] = []
        for pipeline, ms in sorted(buckets.items()):
            ok = sum(1 for m in ms if m.status == MetricStatus.OK)
            warning = sum(1 for m in ms if m.status == MetricStatus.WARNING)
            critical = sum(1 for m in ms if m.status == MetricStatus.CRITICAL)
            if critical:
                worst = MetricStatus.CRITICAL
            elif warning:
                worst = MetricStatus.WARNING
            else:
                worst = MetricStatus.OK
            entries.append(DigestEntry(
                pipeline=pipeline,
                total=len(ms),
                ok=ok,
                warning=warning,
                critical=critical,
                worst_status=worst,
            ))

        return Digest(
            generated_at=datetime.utcnow().isoformat(),
            entries=entries,
        )
