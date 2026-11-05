"""Test cli translate module."""
from click.testing import CliRunner
import os

from ladybug.futil import nukedir
from ladybug.cli.download import download_weather_cli


def test_download_weather():
    runner = CliRunner()
    input_url = 'https://energyplus-weather.s3.amazonaws.com/' \
        'north_and_central_america_wmo_region_4/USA/CA/' \
        'USA_CA_Long.Beach-Daugherty.Field.722970_TMY3/' \
        'USA_CA_Long.Beach-Daugherty.Field.722970_TMY3.zip'
    output_folder = './tests/assets/download'
    in_args = [input_url, '--folder', output_folder]

    if os.name == 'nt':
        result = runner.invoke(download_weather_cli, in_args)
        print(result.output)
        assert result.exit_code == 0
        out_paths = result.output.split('\n')
        assert len(out_paths) == 3
        for f in out_paths:
            assert os.path.isfile(f)
        nukedir(output_folder, True)
