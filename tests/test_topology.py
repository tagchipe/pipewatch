"""Tests for pipewatch.topology."""
import pytest
from pipewatch.topology import TopologyMapper


@pytest.fixture()
def mapper() -> TopologyMapper:
    return TopologyMapper()


def test_add_pipeline_creates_node(mapper):
    node = mapper.add_pipeline("ingest")
    assert node.name == "ingest"
    assert mapper.get("ingest") is node


def test_get_missing_returns_none(mapper):
    assert mapper.get("ghost") is None


def test_add_edge_registers_both_directions(mapper):
    mapper.add_edge("ingest", "transform")
    assert "transform" in mapper.get("ingest").downstream
    assert "ingest" in mapper.get("transform").upstream


def test_add_edge_idempotent(mapper):
    mapper.add_edge("a", "b")
    mapper.add_edge("a", "b")
    assert mapper.get("a").downstream.count("b") == 1


def test_evaluate_simple_chain(mapper):
    mapper.add_edge("ingest", "transform")
    mapper.add_edge("transform", "load")
    result = mapper.evaluate()
    assert result.order == ["ingest", "transform", "load"]
    assert not result.has_cycles


def test_evaluate_no_edges(mapper):
    mapper.add_pipeline("standalone")
    result = mapper.evaluate()
    assert "standalone" in result.order
    assert not result.has_cycles


def test_evaluate_detects_cycle(mapper):
    mapper.add_edge("a", "b")
    mapper.add_edge("b", "c")
    mapper.add_edge("c", "a")  # cycle
    result = mapper.evaluate()
    assert result.has_cycles
    assert set(result.cycles[0]) == {"a", "b", "c"}


def test_evaluate_partial_cycle(mapper):
    # d -> e is fine; a->b->c->a is a cycle
    mapper.add_edge("a", "b")
    mapper.add_edge("b", "c")
    mapper.add_edge("c", "a")
    mapper.add_edge("d", "e")
    result = mapper.evaluate()
    assert "d" in result.order
    assert "e" in result.order
    assert result.has_cycles


def test_all_nodes_returns_all(mapper):
    mapper.add_pipeline("x")
    mapper.add_edge("y", "z")
    names = {n.name for n in mapper.all_nodes()}
    assert names == {"x", "y", "z"}


def test_to_dict_and_to_json(mapper):
    mapper.add_edge("src", "dst")
    result = mapper.evaluate()
    d = result.to_dict()
    assert "order" in d and "cycles" in d
    import json
    parsed = json.loads(result.to_json())
    assert parsed["order"] == d["order"]
