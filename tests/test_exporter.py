"""Tests for pipewatch.exporter."""
import json
from datetime import datetime, timezone

import pytest

from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.exporter import MetricExporter, to_csv, to_jsonlines


def make_metric(name: str, value: float, status: MetricStatus, pipeline: str = "pipe") -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        name=name,
        value=value,
        status=status,
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def metrics():
    return [
        make_metric("row_count", 100.0, MetricStatus.OK),
        make_metric("error_rate", 0.15, MetricStatus.WARNING),
        make_metric("latency", 9.5, MetricStatus.CRITICAL),
    ]


def test_csv_header(metrics):
    output = to_csv(metrics)
    assert output.startswith("pipeline,name,value,status,timestamp")


def test_csv_row_count(metrics):
    lines = to_csv(metrics).strip().splitlines()
    assert len(lines) == 4  # header + 3 rows


def test_csv_contains_values(metrics):
    output = to_csv(metrics)
    assert "row_count" in output
    assert "warning" in output
    assert "critical" in output


def test_jsonlines_count(metrics):
    output = to_jsonlines(metrics)
    lines = output.strip().splitlines()
    assert len(lines) == 3


def test_jsonlines_parseable(metrics):
    output = to_jsonlines(metrics)
    for line in output.splitlines():
        obj = json.loads(line)
        assert "pipeline" in obj
        assert "status" in obj


def test_exporter_add_and_export(metrics):
    exporter = MetricExporter()
    for m in metrics:
        exporter.add(m)
    csv_out = exporter.export_csv()
    jl_out = exporter.export_jsonlines()
    assert "row_count" in csv_out
    assert "latency" in jl_out


def test_exporter_clear(metrics):
    exporter = MetricExporter()
    for m in metrics:
        exporter.add(m)
    exporter.clear()
    assert exporter.export_jsonlines() == ""
    assert exporter.export_csv().strip() == "pipeline,name,value,status,timestamp"
