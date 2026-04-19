"""Tests for pipewatch.routing."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert
from pipewatch.routing import AlertRouter, RouteRule


def make_alert(pipeline="pipe_a", status=MetricStatus.WARNING):
    metric = PipelineMetric(
        name="row_count",
        pipeline=pipeline,
        value=5.0,
        status=status,
    )
    return Alert(metric=metric, message="test alert")


@pytest.fixture
def router():
    return AlertRouter()


def test_add_route_returns_rule(router):
    rule = router.add_route(lambda a: None, name="r1")
    assert isinstance(rule, RouteRule)
    assert "r1" in router.route_names()


def test_dispatch_calls_matching_handler(router):
    received = []
    router.add_route(received.append, name="catch_all")
    alert = make_alert()
    result = router.dispatch(alert)
    assert len(received) == 1
    assert result.dispatched == 1
    assert "catch_all" in result.matched_routes


def test_pipeline_filter_excludes_other_pipeline(router):
    received = []
    router.add_route(received.append, pipeline="pipe_b", name="b_only")
    result = router.dispatch(make_alert(pipeline="pipe_a"))
    assert len(received) == 0
    assert result.dispatched == 0


def test_pipeline_filter_matches_correct_pipeline(router):
    received = []
    router.add_route(received.append, pipeline="pipe_a", name="a_only")
    result = router.dispatch(make_alert(pipeline="pipe_a"))
    assert result.dispatched == 1


def test_status_filter_excludes_wrong_status(router):
    received = []
    router.add_route(received.append, statuses=[MetricStatus.CRITICAL], name="crit_only")
    result = router.dispatch(make_alert(status=MetricStatus.WARNING))
    assert result.dispatched == 0


def test_status_filter_matches_correct_status(router):
    received = []
    router.add_route(received.append, statuses=[MetricStatus.WARNING, MetricStatus.CRITICAL], name="warn_crit")
    result = router.dispatch(make_alert(status=MetricStatus.CRITICAL))
    assert result.dispatched == 1


def test_multiple_routes_all_matching(router):
    calls = []
    router.add_route(lambda a: calls.append("r1"), name="r1")
    router.add_route(lambda a: calls.append("r2"), name="r2")
    result = router.dispatch(make_alert())
    assert result.dispatched == 2
    assert set(result.matched_routes) == {"r1", "r2"}


def test_to_dict_contains_expected_keys(router):
    router.add_route(lambda a: None, name="r1")
    alert = make_alert()
    result = router.dispatch(alert)
    d = result.to_dict()
    assert "matched_routes" in d
    assert "dispatched" in d
