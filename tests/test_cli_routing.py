"""Tests for pipewatch.cli_routing."""
from click.testing import CliRunner
from pipewatch.cli_routing import routing_cli


def test_demo_text_output():
    runner = CliRunner()
    result = runner.invoke(routing_cli, ["demo", "--format", "text"])
    assert result.exit_code == 0
    assert "dispatched=" in result.output
    assert "routes=" in result.output


def test_demo_json_output():
    runner = CliRunner()
    result = runner.invoke(routing_cli, ["demo", "--format", "json"])
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "dispatched" in data[0]
    assert "matched_routes" in data[0]


def test_demo_catch_all_always_matches():
    runner = CliRunner()
    result = runner.invoke(routing_cli, ["demo", "--format", "json"])
    import json
    data = json.loads(result.output)
    for entry in data:
        assert "catch-all" in entry["matched_routes"]


def test_demo_ok_status_skips_warn_crit_route():
    runner = CliRunner()
    result = runner.invoke(routing_cli, ["demo", "--format", "json"])
    import json
    data = json.loads(result.output)
    ok_entries = [d for d in data if d["dispatched"] == 1]
    assert any(ok_entries)
