from click.testing import CliRunner
from pipewatch.cli_scorer import scorer_cli
import json


def test_score_text_output():
    runner = CliRunner()
    result = runner.invoke(scorer_cli, ["score"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "transform" in result.output
    assert "load" in result.output


def test_score_json_output():
    runner = CliRunner()
    result = runner.invoke(scorer_cli, ["score", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 3
    keys = set(data[0].keys())
    assert "pipeline" in keys
    assert "score" in keys


def test_score_filter_by_pipeline():
    runner = CliRunner()
    result = runner.invoke(scorer_cli, ["score", "--pipeline", "ingest", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["pipeline"] == "ingest"


def test_score_unknown_pipeline_no_results():
    runner = CliRunner()
    result = runner.invoke(scorer_cli, ["score", "--pipeline", "nonexistent"])
    assert result.exit_code == 0
    assert "No metrics found" in result.output
