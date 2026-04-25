"""Tests for pipewatch.compactor."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.compactor import MetricCompactor, CompactedMetric


def make_metric(pipeline: str, name: str, value: float, status: MetricStatus) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=status)


@pytest.fixture
def compactor():
    return MetricCompactor()


def test_compact_empty_returns_empty(compactor):
    assert compactor.compact([]) == []


def test_compact_single_metric(compactor):
    m = make_metric("pipe", "rows", 100.0, MetricStatus.OK)
    results = compactor.compact([m])
    assert len(results) == 1
    r = results[0]
    assert r.pipeline == "pipe"
    assert r.name == "rows"
    assert r.count == 1
    assert r.min_value == 100.0
    assert r.max_value == 100.0
    assert r.mean_value == 100.0
    assert r.dominant_status == MetricStatus.OK


def test_compact_multiple_same_key(compactor):
    metrics = [
        make_metric("pipe", "rows", 10.0, MetricStatus.OK),
        make_metric("pipe", "rows", 20.0, MetricStatus.WARNING),
        make_metric("pipe", "rows", 30.0, MetricStatus.OK),
    ]
    results = compactor.compact(metrics)
    assert len(results) == 1
    r = results[0]
    assert r.count == 3
    assert r.min_value == 10.0
    assert r.max_value == 30.0
    assert abs(r.mean_value - 20.0) < 1e-6
    assert r.dominant_status == MetricStatus.WARNING


def test_compact_critical_dominates(compactor):
    metrics = [
        make_metric("pipe", "latency", 1.0, MetricStatus.OK),
        make_metric("pipe", "latency", 2.0, MetricStatus.CRITICAL),
        make_metric("pipe", "latency", 1.5, MetricStatus.WARNING),
    ]
    results = compactor.compact(metrics)
    assert results[0].dominant_status == MetricStatus.CRITICAL


def test_compact_groups_by_pipeline_and_name(compactor):
    metrics = [
        make_metric("pipe_a", "rows", 5.0, MetricStatus.OK),
        make_metric("pipe_b", "rows", 8.0, MetricStatus.WARNING),
        make_metric("pipe_a", "errors", 1.0, MetricStatus.CRITICAL),
    ]
    results = compactor.compact(metrics)
    assert len(results) == 3
    keys = {(r.pipeline, r.name) for r in results}
    assert keys == {("pipe_a", "rows"), ("pipe_b", "rows"), ("pipe_a", "errors")}


def test_to_dict_contains_expected_keys(compactor):
    m = make_metric("p", "n", 42.0, MetricStatus.OK)
    result = compactor.compact([m])[0]
    d = result.to_dict()
    for key in ("pipeline", "name", "count", "min_value", "max_value", "mean_value", "dominant_status"):
        assert key in d


def test_to_json_is_valid_json(compactor):
    import json
    m = make_metric("p", "n", 7.0, MetricStatus.OK)
    result = compactor.compact([m])[0]
    parsed = json.loads(result.to_json())
    assert parsed["pipeline"] == "p"
