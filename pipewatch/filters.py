"""Filtering utilities for pipeline metrics and alerts."""

from typing import Callable, List, Optional
from pipewatch.metrics import PipelineMetric, MetricStatus


MetricFilter = Callable[[PipelineMetric], bool]


def by_status(*statuses: MetricStatus) -> MetricFilter:
    """Return a filter that matches metrics with any of the given statuses."""
    status_set = set(statuses)

    def _filter(metric: PipelineMetric) -> bool:
        return metric.status in status_set

    return _filter


def by_name(*names: str) -> MetricFilter:
    """Return a filter that matches metrics whose name is in the given list."""
    name_set = set(names)

    def _filter(metric: PipelineMetric) -> bool:
        return metric.name in name_set

    return _filter


def by_pipeline(*pipeline_ids: str) -> MetricFilter:
    """Return a filter that matches metrics belonging to the given pipelines."""
    id_set = set(pipeline_ids)

    def _filter(metric: PipelineMetric) -> bool:
        return metric.pipeline_id in id_set

    return _filter


def combine(*filters: MetricFilter, mode: str = "all") -> MetricFilter:
    """Combine multiple filters with AND ('all') or OR ('any') logic."""
    if mode not in ("all", "any"):
        raise ValueError("mode must be 'all' or 'any'")

    def _filter(metric: PipelineMetric) -> bool:
        if mode == "all":
            return all(f(metric) for f in filters)
        return any(f(metric) for f in filters)

    return _filter


def apply_filters(
    metrics: List[PipelineMetric],
    *filters: MetricFilter,
    mode: str = "all",
) -> List[PipelineMetric]:
    """Apply one or more filters to a list of metrics and return matches."""
    if not filters:
        return list(metrics)
    combined = combine(*filters, mode=mode)
    return [m for m in metrics if combined(m)]
