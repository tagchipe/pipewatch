import pytest
from pipewatch.correlator import MetricCorrelator, CorrelationResult


@pytest.fixture
def correlator():
    return MetricCorrelator(max_samples=50)


def _feed(c: MetricCorrelator, name: str, values):
    for v in values:
        c.record(name, v)


def test_correlate_returns_none_before_two_samples(correlator):
    correlator.record("a", 1.0)
    correlator.record("b", 1.0)
    # only 1 sample each
    assert correlator.correlate("a", "b") is None


def test_perfect_positive_correlation(correlator):
    vals = [float(i) for i in range(20)]
    _feed(correlator, "a", vals)
    _feed(correlator, "b", vals)
    result = correlator.correlate("a", "b")
    assert result is not None
    assert abs(result.coefficient - 1.0) < 1e-6
    assert result.is_strong


def test_perfect_negative_correlation(correlator):
    vals = [float(i) for i in range(20)]
    _feed(correlator, "x", vals)
    _feed(correlator, "y", [-v for v in vals])
    result = correlator.correlate("x", "y")
    assert result is not None
    assert abs(result.coefficient + 1.0) < 1e-6
    assert result.is_strong


def test_no_correlation_on_constant(correlator):
    _feed(correlator, "flat", [5.0] * 20)
    _feed(correlator, "ramp", list(range(20)))
    result = correlator.correlate("flat", "ramp")
    assert result is None  # std dev zero -> undefined


def test_sample_count_in_result(correlator):
    _feed(correlator, "p", list(range(10)))
    _feed(correlator, "q", list(range(15)))
    result = correlator.correlate("p", "q")
    assert result is not None
    assert result.sample_count == 10


def test_all_pairs_returns_results(correlator):
    vals = list(range(10))
    _feed(correlator, "m1", vals)
    _feed(correlator, "m2", vals)
    _feed(correlator, "m3", vals)
    pairs = correlator.all_pairs()
    names = {(r.metric_a, r.metric_b) for r in pairs}
    assert ("m1", "m2") in names
    assert ("m1", "m3") in names
    assert ("m2", "m3") in names


def test_to_dict_keys(correlator):
    _feed(correlator, "a", list(range(5)))
    _feed(correlator, "b", list(range(5)))
    result = correlator.correlate("a", "b")
    d = result.to_dict()
    assert set(d.keys()) == {"metric_a", "metric_b", "coefficient", "sample_count"}


def test_max_samples_evicts_oldest():
    c = MetricCorrelator(max_samples=5)
    for i in range(10):
        c.record("z", float(i))
    assert len(c._series["z"]) == 5
    assert c._series["z"] == [5.0, 6.0, 7.0, 8.0, 9.0]
