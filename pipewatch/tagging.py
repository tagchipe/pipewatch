"""Tag-based grouping and filtering for pipeline metrics."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set
from pipewatch.metrics import PipelineMetric


@dataclass
class TagIndex:
    """Maintains an index of metrics by tag."""
    _index: Dict[str, List[PipelineMetric]] = field(default_factory=dict)

    def add(self, metric: PipelineMetric, tags: List[str]) -> None:
        """Index a metric under each of its tags."""
        for tag in tags:
            self._index.setdefault(tag, []).append(metric)

    def get(self, tag: str) -> List[PipelineMetric]:
        """Return all metrics associated with a tag."""
        return list(self._index.get(tag, []))

    def all_tags(self) -> Set[str]:
        """Return the set of all known tags."""
        return set(self._index.keys())

    def tags_for(self, metric: PipelineMetric) -> List[str]:
        """Return tags that include the given metric."""
        return [tag for tag, metrics in self._index.items() if metric in metrics]


class TagManager:
    """Attach and query tags on pipeline metrics."""

    def __init__(self) -> None:
        self._tags: Dict[str, List[str]] = {}
        self._index = TagIndex()

    def tag(self, metric: PipelineMetric, tags: List[str]) -> None:
        """Assign tags to a metric (keyed by metric name)."""
        key = metric.name
        existing = self._tags.get(key, [])
        new_tags = [t for t in tags if t not in existing]
        self._tags[key] = existing + new_tags
        self._index.add(metric, new_tags)

    def get_tags(self, metric: PipelineMetric) -> List[str]:
        return self._tags.get(metric.name, [])

    def by_tag(self, tag: str) -> List[PipelineMetric]:
        return self._index.get(tag)

    def all_tags(self) -> Set[str]:
        return self._index.all_tags()
