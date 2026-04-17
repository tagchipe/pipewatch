"""Tests for pipewatch.cli_scheduler."""

from click.testing import CliRunner
from pipewatch.cli_scheduler import scheduler_cli


def test_run_exits_after_duration():
    runner = CliRunner()
    result = runner.invoke(scheduler_cli, ["run", "--interval", "0.05", "--duration", "0.2"])
    assert result.exit_code == 0
    assert "Scheduler started" in result.output
    assert "Scheduler stopped" in result.output


def test_run_json_format():
    runner = CliRunner()
    result = runner.invoke(
        scheduler_cli,
        ["run", "--interval", "0.05", "--format", "json", "--duration", "0.15"],
    )
    assert result.exit_code == 0
    assert "Scheduler started" in result.output


def test_run_text_format():
    runner = CliRunner()
    result = runner.invoke(
        scheduler_cli,
        ["run", "--interval", "0.05", "--format", "text", "--duration", "0.15"],
    )
    assert result.exit_code == 0
    assert "Scheduler started" in result.output
