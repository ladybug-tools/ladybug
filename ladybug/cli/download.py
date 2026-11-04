"""Ladybug commands for downloading and unzipping weather files."""
import click
import sys
import logging

from ladybug.projectinfo import ProjectInfo
from ladybug.commandutil import process_content_to_output

_logger = logging.getLogger(__name__)


@click.group(help='Commands for downloading and unzipping weather files.')
def translate():
    pass


@translate.command('download-weather')
@click.argument('weather-url', type=str)
@click.option('--folder', '-f', help='An optional path to a directory into which the '
              'weather file will be downloaded and unzipped. If None, the weather '
              'files will be downloaded to the ladybug default weather data folder '
              'and placed in a sub-folder with the name of the weather file location.',
              default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--log-file', '-log', help='Optional log file to output the paths of the '
              'generated files (epw, stat, ddy) if successfully'
              ' downloaded. By default the list will be printed out to stdout.',
              type=click.File('w'), default='-', show_default=True)
def download_weather_cli(weather_url, folder, log_file):
    """Download and unzip weather originating from a URL.

    \b
    Args:
        weather_url: Text representing the URL at which the climate data resides.
            To open the a map interface for all publicly available climate data,
            search the EPWmap application.
    """
    try:
        download_weather(weather_url, folder, log_file)
    except Exception as e:
        _logger.exception('Wea translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def download_weather(weather_url, folder=None, log_file=None):
    """Download and unzip weather originating from a URL.

    Args:
        weather_url: Text representing the URL at which the climate data resides.
            To open the a map interface for all publicly available climate data,
            search the EPWmap application.
        folder: An optional path to a directory into which the weather file
            will be downloaded and unzipped. If None, the weather files will be
            downloaded to the ladybug default weather data folder and placed in
            a sub-folder with the name of the weather file location.
        log_file: Optional log file to output the paths of the generated files
            (epw, stat, ddy) if successfully downloaded. If None, the result
            will be returned from this method.
    """
    down_files = ProjectInfo.download_weather(weather_url, folder)
    down_files = [f for f in down_files if f is not None]
    return process_content_to_output(down_files, log_file)
