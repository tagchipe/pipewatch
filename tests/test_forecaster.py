"""Tests for pipewatch.forecaster."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.forecaster import MetricForecaster, ForecastResult


def make_metric(name: str, value: float, pipeline: str = "pipe_a") -> PipelineMetric:
    return PipelineMetric(
        name=name,
        pipeline=pipeline,
        value=value,
        status=MetricStatus.OK,
    )


@pytest.fixture
def forecaster() -> MetricForecaster:
    return MetricForecaster(min_samples=3, horizon=1)


def test_forecast_returns_none_before_min_samples(forecaster):
    m = make_metric("rows", 10.0)
    forecaster.record(m)
    forecaster.record(make_metric("rows", 20.0))
    result = forecaster.forecast(make_metric("rows", 30.0))
    # only 2 recorded so far; forecast requires 3
    assert result is None


def test_forecast_available_at_min_samples(forecaster):
    for v in [10.0, 20.0, 30.0]:
        forecaster.record(make_metric("rows", v))
    result = forecaster.forecast(make_metric("rows", 30.0))
    assert isinstance(result, ForecastResult)
    assert result.samples == 3


def test_perfect_linear_trend(forecaster):
    """Values 0, 10, 20 => slope=10, next=30."""
    for v in [0.0, 10.0, 20.0]:
        forecaster.record(make_metric("rows", v))
    result = forecaster.forecast(make_metric("rows", 20.0))
    assert result is not None
    assert abs(result.slope - 10.0) < 1e-6
    assert abs(result.next_value - 30.0) < 1e-4


def test_flat_trend_gives_zero_slope(forecaster):
    for _ in range(4):
        forecaster.record(make_metric("latency", 5.0))
    result = forecaster.forecast(make_metric("latency", 5.0))
    assert result is not None
    assert abs(result.slope) < 1e-9
    assert abs(result.next_value - 5.0) < 1e-6


def test_forecast_isolated_per_pipeline(forecaster):
    for v in [1.0, 2.0, 3.0]:
        forecaster.record(make_metric("rows", v, pipeline="pipe_a"))
    result = forecaster.forecast(make_metric("rows", 3.0, pipeline="pipe_b"))
    assert result is None


def test_horizon_shifts_next_value():
    fc = MetricForecaster(min_samples=3, horizon=3)
    for v in [0.0, 10.0, 20.0]:
        fc.record(make_metric("rows", v))
    result = fc.forecast(make_metric("rows", 20.0))
    assert result is not None
    # x index of next prediction = (3-1) + 3 = 5 => 10*5 = 50
    assert abs(result.next_value - 50.0) < 1e-4
    assert result.horizon == 3


def test_to_dict_contains_expected_keys(forecaster):
    for v in [2.0, 4.0, 6.0]:
        forecaster.record(make_metric("errors", v))
    result = forecaster.forecast(make_metric("errors", 6.0))
    d = result.to_dict()
    for key in ("pipeline", "metric_name", "samples", "slope", "intercept", "next_value", "horizon"):
        assert key in d


def test_min_samples_validation():
    with pytest.raises(ValueError):
        MetricForecaster(min_samples=1)
