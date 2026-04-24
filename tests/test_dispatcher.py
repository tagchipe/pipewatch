"""Tests for pipewatch.dispatcher."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.dispatcher import EventDispatcher, DispatchResult


def make_metric(
    name: str = "row_count",
    value: float = 100.0,
    status: MetricStatus = MetricStatus.OK,
    pipeline: str = "etl_main",
) -> PipelineMetric:
    return PipelineMetric(
        name=name,
        value=value,
        status=status,
        pipeline=pipeline,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def dispatcher() -> EventDispatcher:
    return EventDispatcher()


def test_no_listeners_returns_zero_called(dispatcher):
    result = dispatcher.dispatch(make_metric())
    assert result.listeners_called == 0
    assert result.skipped == 0


def test_global_listener_receives_any_metric(dispatcher):
    received: List[PipelineMetric] = []
    dispatcher.register(received.append)
    dispatcher.dispatch(make_metric(pipeline="pipe_a"))
    dispatcher.dispatch(make_metric(pipeline="pipe_b"))
    assert len(received) == 2


def test_pipeline_filter_restricts_delivery(dispatcher):
    received: List[PipelineMetric] = []
    dispatcher.register(received.append, pipeline="pipe_a")
    dispatcher.dispatch(make_metric(pipeline="pipe_a"))
    dispatcher.dispatch(make_metric(pipeline="pipe_b"))
    assert len(received) == 1
    assert received[0].pipeline == "pipe_a"


def test_status_filter_restricts_delivery(dispatcher):
    received: List[PipelineMetric] = []
    dispatcher.register(received.append, status=MetricStatus.CRITICAL)
    dispatcher.dispatch(make_metric(status=MetricStatus.OK))
    dispatcher.dispatch(make_metric(status=MetricStatus.WARNING))
    dispatcher.dispatch(make_metric(status=MetricStatus.CRITICAL))
    assert len(received) == 1
    assert received[0].status == MetricStatus.CRITICAL


def test_combined_filter(dispatcher):
    received: List[PipelineMetric] = []
    dispatcher.register(received.append, pipeline="pipe_a", status=MetricStatus.WARNING)
    dispatcher.dispatch(make_metric(pipeline="pipe_a", status=MetricStatus.OK))
    dispatcher.dispatch(make_metric(pipeline="pipe_b", status=MetricStatus.WARNING))
    dispatcher.dispatch(make_metric(pipeline="pipe_a", status=MetricStatus.WARNING))
    assert len(received) == 1


def test_skipped_count_reflects_filtered_listeners(dispatcher):
    dispatcher.register(lambda m: None, pipeline="other")
    result = dispatcher.dispatch(make_metric(pipeline="etl_main"))
    assert result.skipped == 1
    assert result.listeners_called == 0


def test_to_dict_contains_expected_keys(dispatcher):
    dispatcher.register(lambda m: None)
    result = dispatcher.dispatch(make_metric())
    d = result.to_dict()
    assert "pipeline" in d
    assert "metric_name" in d
    assert "status" in d
    assert "listeners_called" in d


def test_clear_removes_all_listeners(dispatcher):
    dispatcher.register(lambda m: None)
    dispatcher.register(lambda m: None)
    assert dispatcher.listener_count() == 2
    dispatcher.clear()
    assert dispatcher.listener_count() == 0
    result = dispatcher.dispatch(make_metric())
    assert result.listeners_called == 0
