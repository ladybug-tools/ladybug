"""ladybug file translation commands."""
import click
import sys
import logging

from ladybug.wea import Wea
from ladybug.ddy import DDY
from ladybug.epw import EPW

from ._helper import _load_analysis_period_str

_logger = logging.getLogger(__name__)


@click.group(help='Commands for translating between various file types.')
def translate():
    pass


@translate.command('epw-to-wea')
@click.argument('epw-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--analysis-period', '-ap', help='An AnalysisPeriod string to filter the '
              'datetimes in the resulting Wea (eg. "6/21 to 9/21 between 8 and 16 @1"). '
              'If unspecified, the Wea will be annual.', default=None, type=str)
@click.option('--timestep', '-t', help='An optional integer to set the number of '
              'time steps per hour. Default is 1 for one value per hour. Note that '
              'this input will only do a linear interpolation over the data in the EPW '
              'file.', type=int, default=1, show_default=True)
@click.option('--output-file', '-f', help='Optional .wea file path to output the Wea '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-')
def epw_to_wea(epw_file, analysis_period, timestep, output_file):
    """Translate an .epw file to a .wea file.

    \b
    Args:
        epw_file: Path to an .epw file.
    """
    try:
        wea_obj = Wea.from_epw_file(epw_file, timestep)
        analysis_period = _load_analysis_period_str(analysis_period)
        if analysis_period is not None:
            wea_obj = wea_obj.filter_by_analysis_period(analysis_period)
        output_file.write(wea_obj.to_file_string())
    except Exception as e:
        _logger.exception('Wea translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('epw-to-ddy')
@click.argument('epw-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--percentile', '-p', help='A number between 0 and 50 for the '
              'percentile difference from the most extreme conditions within the '
              'EPW to be used for the design day. Typical values are 0.4 and 1.0.',
              type=float, default=0.4, show_default=True)
@click.option('--output-file', '-f', help='Optional .wea file path to output the Wea '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-')
def epw_to_ddy(epw_file, percentile, output_file):
    """Get a DDY file with a heating + cooling design day from this EPW.

    This method will first check if there is a heating or cooling design day
    that meets the input percentile within the EPW itself. If None is
    found, the heating and cooling design days will be derived from analysis
    of the annual data within the EPW, which is usually less accurate.

    \b
    Args:
        epw_file: Path to an .epw file.
    """
    try:
        epw_obj = EPW(epw_file)
        ddy_obj = DDY(epw_obj.location, epw_obj.best_available_design_days(percentile))
        output_file.write(ddy_obj.to_file_string())
    except Exception as e:
        _logger.exception('DDY translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('wea-to-constant')
@click.argument('wea-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--value', '-v', help='The direct and diffuse irradiance value that '
              'will be written in for all datetimes of the Wea.',
              type=int, default=1000, show_default=True)
@click.option('--output-file', '-f', help='Optional .wea file path to output the Wea '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-')
def wea_to_constant(wea_file, value, output_file):
    """Convert a Wea file to have a constant value for each datetime.

    This is useful in workflows where hourly irradiance values are inconsequential
    to the analysis and one is only using the Wea as a format to pass location
    and datetime information (eg. for direct sun hours).

    \b
    Args:
        wea_file: Full path to .wea file.
    """
    try:
        output_file.write(Wea.to_constant_value(wea_file, value))
    except Exception as e:
        _logger.exception('Wea translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
