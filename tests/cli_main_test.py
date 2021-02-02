"""Test basic CLI commands"""
import json

from click.testing import CliRunner
from ladybug.cli import viz, config


def test_viz():
    runner = CliRunner()
    result = runner.invoke(viz)
    assert result.exit_code == 0
    assert result.output.startswith('vi')
    assert result.output.endswith('z!\n')


def test_config():
    runner = CliRunner()
    result = runner.invoke(config)
    assert result.exit_code == 0
    config_dict = json.loads(result.output)
    assert len(config_dict) >= 2
