"""Tests for pipewatch.digest."""
import json
import pytest
from datetime import datetime

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.digest import DigestBuilder, Digest, DigestEntry


def make_metric(pipeline: str, name: str, status: MetricStatus, value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=status)


@pytest.fixture
def builder() -> DigestBuilder:
    return DigestBuilder()


def test_empty_metrics_returns_empty_digest(builder):
    digest = builder.build([])
    assert isinstance(digest, Digest)
    assert digest.entries == []


def test_single_ok_metric(builder):
    metrics = [make_metric("etl", "rows", MetricStatus.OK)]
    digest = builder.build(metrics)
    assert len(digest.entries) == 1
    e = digest.entries[0]
    assert e.pipeline == "etl"
    assert e.ok == 1
    assert e.warning == 0
    assert e.critical == 0
    assert e.worst_status == MetricStatus.OK


def test_mixed_statuses(builder):
    metrics = [
        make_metric("pipe", "a", MetricStatus.OK),
        make_metric("pipe", "b", MetricStatus.WARNING),
        make_metric("pipe", "c", MetricStatus.CRITICAL),
    ]
    digest = builder.build(metrics)
    assert len(digest.entries) == 1
    e = digest.entries[0]
    assert e.total == 3
    assert e.ok == 1
    assert e.warning == 1
    assert e.critical == 1
    assert e.worst_status == MetricStatus.CRITICAL


def test_warning_worst_when_no_critical(builder):
    metrics = [
        make_metric("pipe", "a", MetricStatus.OK),
        make_metric("pipe", "b", MetricStatus.WARNING),
    ]
    digest = builder.build(metrics)
    assert digest.entries[0].worst_status == MetricStatus.WARNING


def test_multiple_pipelines_sorted(builder):
    metrics = [
        make_metric("z_pipe", "x", MetricStatus.OK),
        make_metric("a_pipe", "y", MetricStatus.CRITICAL),
    ]
    digest = builder.build(metrics)
    assert len(digest.entries) == 2
    assert digest.entries[0].pipeline == "a_pipe"
    assert digest.entries[1].pipeline == "z_pipe"


def test_to_dict_contains_generated_at(builder):
    digest = builder.build([])
    d = digest.to_dict()
    assert "generated_at" in d
    assert "entries" in d


def test_to_json_is_valid(builder):
    metrics = [make_metric("etl", "rows", MetricStatus.OK)]
    digest = builder.build(metrics)
    data = json.loads(digest.to_json())
    assert data["entries"][0]["worst_status"] == "ok"
