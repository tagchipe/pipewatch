"""Metric labeler: attach and query arbitrary key-value labels on metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import PipelineMetric


@dataclass
class LabelSet:
    """A collection of key-value labels attached to a metric key."""
    metric_name: str
    pipeline: str
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "pipeline": self.pipeline,
            "labels": dict(self.labels),
        }

    def get(self, key: str) -> Optional[str]:
        return self.labels.get(key)

    def set(self, key: str, value: str) -> None:
        self.labels[key] = value

    def remove(self, key: str) -> None:
        self.labels.pop(key, None)


class MetricLabeler:
    """Attach and query labels on pipeline metrics."""

    def __init__(self) -> None:
        self._store: Dict[str, LabelSet] = {}

    def _key(self, metric: PipelineMetric) -> str:
        return f"{metric.pipeline}::{metric.name}"

    def label(self, metric: PipelineMetric, **labels: str) -> LabelSet:
        """Attach one or more labels to a metric. Returns the updated LabelSet."""
        k = self._key(metric)
        if k not in self._store:
            self._store[k] = LabelSet(metric_name=metric.name, pipeline=metric.pipeline)
        for key, value in labels.items():
            self._store[k].set(key, value)
        return self._store[k]

    def get_labels(self, metric: PipelineMetric) -> Optional[LabelSet]:
        """Return the LabelSet for a metric, or None if not labelled."""
        return self._store.get(self._key(metric))

    def find_by_label(self, key: str, value: str) -> List[LabelSet]:
        """Return all LabelSets that have a matching key=value label."""
        return [
            ls for ls in self._store.values()
            if ls.get(key) == value
        ]

    def all_label_sets(self) -> List[LabelSet]:
        """Return all registered LabelSets."""
        return list(self._store.values())

    def remove_label(self, metric: PipelineMetric, key: str) -> None:
        """Remove a single label key from a metric's LabelSet."""
        ls = self._store.get(self._key(metric))
        if ls:
            ls.remove(key)
