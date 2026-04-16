"""Tests for pipewatch.filters module."""

import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.filters import (
    by_status,
    by_name,
    by_pipeline,
    combine,
    apply_filters,
)


def make_metric(name: str, pipeline_id: str, status: MetricStatus) -> PipelineMetric:
    return PipelineMetric(name=name, pipeline_id=pipeline_id, value=1.0, status=status)


@pytest.fixture
def metrics():
    return [
        make_metric("row_count", "etl_a", MetricStatus.OK),
        make_metric("latency", "etl_a", MetricStatus.WARNING),
        make_metric("error_rate", "etl_b", MetricStatus.CRITICAL),
        make_metric("row_count", "etl_b", MetricStatus.OK),
    ]


def test_by_status_single(metrics):
    result = apply_filters(metrics, by_status(MetricStatus.OK))
    assert len(result) == 2
    assert all(m.status == MetricStatus.OK for m in result)


def test_by_status_multiple(metrics):
    result = apply_filters(metrics, by_status(MetricStatus.WARNING, MetricStatus.CRITICAL))
    assert len(result) == 2


def test_by_name(metrics):
    result = apply_filters(metrics, by_name("row_count"))
    assert len(result) == 2
    assert all(m.name == "row_count" for m in result)


def test_by_pipeline(metrics):
    result = apply_filters(metrics, by_pipeline("etl_a"))
    assert len(result) == 2
    assert all(m.pipeline_id == "etl_a" for m in result)


def test_combine_all(metrics):
    result = apply_filters(metrics, combine(by_pipeline("etl_a"), by_name("row_count")))
    assert len(result) == 1
    assert result[0].pipeline_id == "etl_a"
    assert result[0].name == "row_count"


def test_combine_any(metrics):
    result = apply_filters(
        metrics,
        combine(by_pipeline("etl_b"), by_status(MetricStatus.WARNING), mode="any"),
    )
    assert len(result) == 3


def test_no_filters_returns_all(metrics):
    result = apply_filters(metrics)
    assert len(result) == len(metrics)


def test_combine_invalid_mode():
    with pytest.raises(ValueError, match="mode must be"):
        combine(by_name("x"), mode="invalid")
