"""Tests for pipewatch.cli_circuit_breaker."""
from click.testing import CliRunner

from pipewatch.cli_circuit_breaker import circuit_breaker_cli


def test_demo_text_output():
    runner = CliRunner()
    result = runner.invoke(circuit_breaker_cli, ["demo", "--format", "text"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "ALLOWED" in result.output
    assert "BLOCKED" in result.output


def test_demo_json_output():
    import json
    runner = CliRunner()
    result = runner.invoke(circuit_breaker_cli, ["demo", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "pipeline" in data[0]
    assert "allowed" in data[0]
    assert "state" in data[0]
    assert "failure_count" in data[0]


def test_demo_shows_open_state():
    runner = CliRunner()
    result = runner.invoke(circuit_breaker_cli, ["demo", "--format", "text"])
    assert "open" in result.output


def test_demo_shows_closed_state():
    runner = CliRunner()
    result = runner.invoke(circuit_breaker_cli, ["demo", "--format", "text"])
    assert "closed" in result.output
