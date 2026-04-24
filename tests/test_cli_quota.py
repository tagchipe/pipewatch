"""Tests for pipewatch.cli_quota."""
from click.testing import CliRunner
from pipewatch.cli_quota import quota_cli


def test_demo_text_output():
    runner = CliRunner()
    result = runner.invoke(quota_cli, ["demo", "--format", "text"])
    assert result.exit_code == 0
    assert "ACCEPTED" in result.output
    assert "BLOCKED" in result.output


def test_demo_json_output():
    import json
    runner = CliRunner()
    result = runner.invoke(quota_cli, ["demo", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 5
    assert "accepted" in data[0]
    assert "used" in data[0]


def test_demo_shows_pipeline_name():
    runner = CliRunner()
    result = runner.invoke(quota_cli, ["demo", "--format", "text"])
    assert "orders" in result.output


def test_demo_json_contains_limit():
    import json
    runner = CliRunner()
    result = runner.invoke(quota_cli, ["demo", "--format", "json"])
    data = json.loads(result.output)
    limits = {r["limit"] for r in data}
    assert 3 in limits
