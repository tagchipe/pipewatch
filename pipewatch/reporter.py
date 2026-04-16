"""Pipeline health report generation."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewatch.collector import MetricCollector
from pipewatch.metrics import MetricStatus, PipelineMetric


@dataclass
class PipelineReport:
    pipeline_name: str
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metrics: List[dict] = field(default_factory=list)
    overall_status: str = MetricStatus.OK.value
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline_name,
            "generated_at": self.generated_at,
            "overall_status": self.overall_status,
            "summary": self.summary,
            "metrics": self.metrics,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class Reporter:
    def __init__(self, collector: MetricCollector, pipeline_name: str = "default"):
        self.collector = collector
        self.pipeline_name = pipeline_name

    def generate(self) -> PipelineReport:
        results = self.collector.evaluate_all()
        metric_rows = []
        status_counts = {s.value: 0 for s in MetricStatus}

        for metric, status in results:
            row = metric.to_dict()
            row["status"] = status.value
            metric_rows.append(row)
            status_counts[status.value] += 1

        overall = MetricStatus.OK
        if status_counts[MetricStatus.CRITICAL.value] > 0:
            overall = MetricStatus.CRITICAL
        elif status_counts[MetricStatus.WARNING.value] > 0:
            overall = MetricStatus.WARNING

        return PipelineReport(
            pipeline_name=self.pipeline_name,
            metrics=metric_rows,
            overall_status=overall.value,
            summary=status_counts,
        )
