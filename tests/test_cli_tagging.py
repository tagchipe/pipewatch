"""Tests for pipewatch.cli_tagging."""
from click.testing import CliRunner
from pipewatch.cli_tagging import tagging_cli


def test_list_tags_shows_known_tags():
    runner = CliRunner()
    result = runner.invoke(tagging_cli, ["list"])
    assert result.exit_code == 0
    assert "etl" in result.output
    assert "volume" in result.output


def test_filter_known_tag():
    runner = CliRunner()
    result = runner.invoke(tagging_cli, ["filter", "quality"])
    assert result.exit_code == 0
    assert "error_rate" in result.output


def test_filter_unknown_tag():
    runner = CliRunner()
    result = runner.invoke(tagging_cli, ["filter", "unknown_tag"])
    assert result.exit_code == 0
    assert "No metrics found" in result.output


def test_list_shows_multiple_tags():
    runner = CliRunner()
    result = runner.invoke(tagging_cli, ["list"])
    assert "perf" in result.output
    assert "volume" in result.output
