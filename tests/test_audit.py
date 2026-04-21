"""Tests for pipewatch.audit."""
import pytest
from pipewatch.audit import AuditLog
from pipewatch.metrics import MetricStatus, PipelineMetric


def make_metric(name: str, pipeline: str, status: MetricStatus, value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(name=name, pipeline=pipeline, value=value, status=status)


@pytest.fixture
def log() -> AuditLog:
    return AuditLog()


def test_no_entry_on_first_repeated_status(log):
    m = make_metric("rows", "etl", MetricStatus.OK)
    log.record(m)
    result = log.record(m)
    assert result is None


def test_entry_on_first_record(log):
    m = make_metric("rows", "etl", MetricStatus.OK)
    entry = log.record(m)
    assert entry is not None
    assert entry.previous_status is None
    assert entry.current_status == MetricStatus.OK


def test_entry_on_status_change(log):
    m_ok = make_metric("rows", "etl", MetricStatus.OK)
    m_warn = make_metric("rows", "etl", MetricStatus.WARNING)
    log.record(m_ok)
    entry = log.record(m_warn)
    assert entry is not None
    assert entry.previous_status == MetricStatus.OK
    assert entry.current_status == MetricStatus.WARNING


def test_no_entry_when_status_unchanged(log):
    m = make_metric("rows", "etl", MetricStatus.WARNING)
    log.record(m)
    result = log.record(m)
    assert result is None


def test_entries_filtered_by_pipeline(log):
    log.record(make_metric("rows", "etl", MetricStatus.OK))
    log.record(make_metric("rows", "load", MetricStatus.CRITICAL))
    etl_entries = log.entries(pipeline="etl")
    assert len(etl_entries) == 1
    assert etl_entries[0].pipeline == "etl"


def test_transitions_for_metric(log):
    log.record(make_metric("rows", "etl", MetricStatus.OK))
    log.record(make_metric("rows", "etl", MetricStatus.WARNING))
    log.record(make_metric("rows", "etl", MetricStatus.CRITICAL))
    transitions = log.transitions_for("etl", "rows")
    assert len(transitions) == 3
    statuses = [t.current_status for t in transitions]
    assert MetricStatus.OK in statuses
    assert MetricStatus.CRITICAL in statuses


def test_max_entries_evicts_oldest(log):
    small_log = AuditLog(max_entries=3)
    for i in range(5):
        m = make_metric(f"metric_{i}", "etl", MetricStatus.OK)
        small_log.record(m)
    assert len(small_log.entries()) == 3


def test_to_dict_has_required_keys(log):
    m = make_metric("rows", "etl", MetricStatus.WARNING, value=42.0)
    entry = log.record(m)
    d = entry.to_dict()
    assert set(d.keys()) == {"pipeline", "metric_name", "previous_status", "current_status", "value", "timestamp"}
    assert d["value"] == 42.0
    assert d["current_status"] == "warning"


def test_clear_resets_state(log):
    log.record(make_metric("rows", "etl", MetricStatus.OK))
    log.clear()
    assert log.entries() == []
    entry = log.record(make_metric("rows", "etl", MetricStatus.OK))
    assert entry is not None
    assert entry.previous_status is None
