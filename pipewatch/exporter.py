"""Export pipeline metrics to various formats (CSV, JSON lines)."""
from __future__ import annotations

import csv
import io
import json
from typing import Iterable

from pipewatch.metrics import PipelineMetric


def to_csv(metrics: Iterable[PipelineMetric]) -> str:
    """Serialize metrics to CSV string."""
    buf = io.StringIO()
    fieldnames = ["pipeline", "name", "value", "status", "timestamp"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for m in metrics:
        writer.writerow(
            {
                "pipeline": m.pipeline,
                "name": m.name,
                "value": m.value,
                "status": m.status.value,
                "timestamp": m.timestamp.isoformat() if m.timestamp else "",
            }
        )
    return buf.getvalue()


def to_jsonlines(metrics: Iterable[PipelineMetric]) -> str:
    """Serialize metrics to newline-delimited JSON."""
    lines = []
    for m in metrics:
        lines.append(
            json.dumps(
                {
                    "pipeline": m.pipeline,
                    "name": m.name,
                    "value": m.value,
                    "status": m.status.value,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                }
            )
        )
    return "\n".join(lines)


class MetricExporter:
    """Collects metrics and exports them on demand."""

    def __init__(self) -> None:
        self._metrics: list[PipelineMetric] = []

    def add(self, metric: PipelineMetric) -> None:
        self._metrics.append(metric)

    def export_csv(self) -> str:
        return to_csv(self._metrics)

    def export_jsonlines(self) -> str:
        return to_jsonlines(self._metrics)

    def clear(self) -> None:
        self._metrics.clear()
