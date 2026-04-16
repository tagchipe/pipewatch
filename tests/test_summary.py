"""Tests for SummaryBuilder and PipelineSummary."""

import json
import pytest

from pipewatch.aggregator import MetricAggregator
from pipewatch.collector import MetricCollector
from pipewatch.metrics import PipelineMetric, MetricStatus, MetricThreshold
from pipewatch.reporter import Reporter
from pipewatch.summary import SummaryBuilder, PipelineSummary


def make_metric(value, pipeline="etl", name="rows", status=MetricStatus.OK):
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=status)


@pytest.fixture
def builder():
    collector = MetricCollector()
    collector.register_threshold("rows", MetricThreshold(warning=50, critical=10))
    for v in [100.0, 90.0, 80.0]:
        m = make_metric(v)
        collector.record(m)
    collector.evaluate()

    aggregator = MetricAggregator()
    for v in [100.0, 90.0, 80.0]:
        aggregator.record(make_metric(v))

    reporter = Reporter(collector)
    return SummaryBuilder(reporter=reporter, aggregator=aggregator)


def test_build_returns_summary(builder):
    summary = builder.build()
    assert isinstance(summary, PipelineSummary)


def test_overall_status_ok(builder):
    summary = builder.build()
    assert summary.overall_status == MetricStatus.OK


def test_stats_included(builder):
    summary = builder.build()
    assert len(summary.stats) >= 1


def test_to_dict_structure(builder):
    d = builder.build().to_dict()
    assert "overall_status" in d
    assert "report" in d
    assert "aggregated_stats" in d
    assert isinstance(d["aggregated_stats"], list)


def test_to_json_valid(builder):
    js = builder.build().to_json()
    parsed = json.loads(js)
    assert parsed["overall_status"] in ("ok", "warning", "critical")
