"""Test cli translate module."""
from click.testing import CliRunner
from ladybug.cli.translate import epw_to_wea, epw_to_ddy

import os


def test_epw_to_wea():
    runner = CliRunner()
    input_epw = './tests/fixtures/epw/chicago.epw'

    result = runner.invoke(epw_to_wea, [input_epw])
    assert result.exit_code == 0

    output_wea = './tests/fixtures/wea/test.wea'
    result = runner.invoke(epw_to_wea, [input_epw, '--output-file', output_wea])
    assert result.exit_code == 0
    assert os.path.isfile(output_wea)
    os.remove(output_wea)


def test_epw_to_ddy():
    runner = CliRunner()
    input_epw = './tests/fixtures/epw/chicago.epw'

    result = runner.invoke(epw_to_ddy, [input_epw])
    assert result.exit_code == 0

    output_ddy = './tests/fixtures/ddy/test.ddy'
    result = runner.invoke(epw_to_ddy, [input_epw, '--output-file', output_ddy])
    assert result.exit_code == 0
    assert os.path.isfile(output_ddy)
    os.remove(output_ddy)
