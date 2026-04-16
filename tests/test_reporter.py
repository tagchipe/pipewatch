"""Tests for pipewatch.reporter."""
import time
import pytest

from pipewatch.collector import MetricCollector
from pipewatch.metrics import MetricThreshold, MetricStatus, PipelineMetric
from pipewatch.reporter import Reporter, PipelineReport


@pytest.fixture
def collector():
    c = MetricCollector()
    c.register_threshold("rows", MetricThreshold(warning=50, critical=10))
    c.register_threshold("lag", MetricThreshold(warning=200, critical=1000))
    return c


def make_metric(name: str, value: float) -> PipelineMetric:
    return PipelineMetric(name=name, value=value, timestamp=time.time())


def test_report_overall_ok(collector):
    collector.record(make_metric("rows", 100))
    collector.record(make_metric("lag", 50))
    rep = Reporter(collector, "test-pipe").generate()
    assert rep.overall_status == MetricStatus.OK.value
    assert rep.pipeline_name == "test-pipe"


def test_report_overall_warning(collector):
    collector.record(make_metric("rows", 30))
    collector.record(make_metric("lag", 50))
    rep = Reporter(collector).generate()
    assert rep.overall_status == MetricStatus.WARNING.value


def test_report_overall_critical(collector):
    collector.record(make_metric("rows", 5))
    collector.record(make_metric("lag", 50))
    rep = Reporter(collector).generate()
    assert rep.overall_status == MetricStatus.CRITICAL.value


def test_report_metrics_count(collector):
    collector.record(make_metric("rows", 100))
    collector.record(make_metric("lag", 50))
    rep = Reporter(collector).generate()
    assert len(rep.metrics) == 2


def test_report_to_dict_keys(collector):
    collector.record(make_metric("rows", 100))
    rep = Reporter(collector).generate()
    d = rep.to_dict()
    assert "pipeline" in d
    assert "overall_status" in d
    assert "summary" in d
    assert "metrics" in d


def test_report_to_json(collector):
    import json
    collector.record(make_metric("rows", 100))
    rep = Reporter(collector).generate()
    parsed = json.loads(rep.to_json())
    assert parsed["pipeline"] == "default"
