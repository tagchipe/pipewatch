"""Tests for metric collection and threshold evaluation."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricThreshold, MetricStatus
from pipewatch.collector import MetricCollector


@pytest.fixture
def collector():
    c = MetricCollector()
    c.register_threshold(MetricThreshold("row_count", warning=1000, critical=5000, comparison="gt"))
    c.register_threshold(MetricThreshold("freshness_minutes", warning=30, critical=60, comparison="gt"))
    return c


def make_metric(name, value, pipeline_id="pipe_1"):
    return PipelineMetric(pipeline_id=pipeline_id, metric_name=name, value=value)


def test_ok_status(collector):
    m = make_metric("row_count", 500)
    assert collector.evaluate(m) == MetricStatus.OK


def test_warning_status(collector):
    m = make_metric("row_count", 2000)
    assert collector.evaluate(m) == MetricStatus.WARNING


def test_critical_status(collector):
    m = make_metric("row_count", 6000)
    assert collector.evaluate(m) == MetricStatus.CRITICAL


def test_unknown_metric(collector):
    m = make_metric("unknown_metric", 42)
    assert collector.evaluate(m) == MetricStatus.UNKNOWN


def test_get_alerts(collector):
    collector.record(make_metric("row_count", 200))
    collector.record(make_metric("row_count", 2000))
    collector.record(make_metric("freshness_minutes", 90))
    alerts = collector.get_alerts()
    assert len(alerts) == 2
    statuses = {s for _, s in alerts}
    assert MetricStatus.WARNING in statuses
    assert MetricStatus.CRITICAL in statuses


def test_summary(collector):
    collector.record(make_metric("row_count", 100))
    collector.record(make_metric("row_count", 2000))
    collector.record(make_metric("row_count", 9000))
    s = collector.summary()
    assert s["ok"] == 1
    assert s["warning"] == 1
    assert s["critical"] == 1
