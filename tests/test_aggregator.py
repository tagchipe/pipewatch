"""Tests for MetricAggregator."""

import pytest
from pipewatch.aggregator import MetricAggregator, AggregatedStats
from pipewatch.metrics import PipelineMetric, MetricStatus


def make_metric(value: float, pipeline="etl", name="row_count", status=MetricStatus.OK):
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=status)


@pytest.fixture
def aggregator():
    return MetricAggregator(window_size=10)


def test_stats_none_when_empty(aggregator):
    assert aggregator.stats("etl", "row_count") is None


def test_stats_single_metric(aggregator):
    aggregator.record(make_metric(100.0))
    s = aggregator.stats("etl", "row_count")
    assert s is not None
    assert s.count == 1
    assert s.mean == 100.0
    assert s.min_val == 100.0
    assert s.max_val == 100.0


def test_stats_multiple_metrics(aggregator):
    for v in [10.0, 20.0, 30.0]:
        aggregator.record(make_metric(v))
    s = aggregator.stats("etl", "row_count")
    assert s.count == 3
    assert s.mean == 20.0
    assert s.min_val == 10.0
    assert s.max_val == 30.0


def test_window_eviction(aggregator):
    for v in range(15):
        aggregator.record(make_metric(float(v)))
    s = aggregator.stats("etl", "row_count")
    assert s.count == 10  # window_size=10


def test_latest_status_reflects_last_record(aggregator):
    aggregator.record(make_metric(50.0, status=MetricStatus.OK))
    aggregator.record(make_metric(5.0, status=MetricStatus.CRITICAL))
    s = aggregator.stats("etl", "row_count")
    assert s.latest_status == MetricStatus.CRITICAL


def test_all_stats_multiple_pipelines(aggregator):
    aggregator.record(make_metric(1.0, pipeline="p1", name="latency"))
    aggregator.record(make_metric(2.0, pipeline="p2", name="errors"))
    all_s = aggregator.all_stats()
    keys = {(s.pipeline, s.name) for s in all_s}
    assert ("p1", "latency") in keys
    assert ("p2", "errors") in keys


def test_to_dict_keys(aggregator):
    aggregator.record(make_metric(42.0))
    d = aggregator.stats("etl", "row_count").to_dict()
    for key in ("pipeline", "name", "count", "mean", "min", "max", "latest_status"):
        assert key in d
