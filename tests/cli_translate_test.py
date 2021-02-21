"""Test cli translate module."""
from click.testing import CliRunner
import os

from ladybug.cli.translate import epw_to_wea, epw_to_ddy
from ladybug.analysisperiod import AnalysisPeriod




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


def test_epw_to_wea_analysis_period():
    runner = CliRunner()
    input_epw = './tests/fixtures/epw/chicago.epw'

    a_per = AnalysisPeriod(6, 21, 8, 9, 21, 17)
    result = runner.invoke(epw_to_wea, [input_epw, '--analysis-period', str(a_per)])
    assert result.exit_code == 0


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
