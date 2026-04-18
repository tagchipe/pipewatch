from click.testing import CliRunner
from pipewatch.cli_dependency import dependency_cli
import json


def test_check_text_output():
    runner = CliRunner()
    result = runner.invoke(dependency_cli, ["check"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "transform" in result.output


def test_check_json_output():
    runner = CliRunner()
    result = runner.invoke(dependency_cli, ["check", "--fmt", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert all("pipeline" in d for d in data)
    assert all("propagated_status" in d for d in data)


def test_check_single_pipeline():
    runner = CliRunner()
    result = runner.invoke(dependency_cli, ["check", "--pipeline", "load"])
    assert result.exit_code == 0
    assert "load" in result.output


def test_check_shows_blocking():
    runner = CliRunner()
    result = runner.invoke(dependency_cli, ["check", "--fmt", "json"])
    data = json.loads(result.output)
    report = next(d for d in data if d["pipeline"] == "report")
    assert report["propagated_status"] == "warning"
