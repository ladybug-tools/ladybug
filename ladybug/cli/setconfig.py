"""Commands to set ladybug-core configurations."""
import click
import sys
import logging
import os
import json

from ladybug.config import folders
from ladybug.futil import nukedir

_logger = logging.getLogger(__name__)


@click.group(help='Commands to set ladybug-core configurations.')
def set_config():
    pass


@set_config.command('ladybug-tools-folder')
@click.argument('folder-path', required=False, type=click.Path(
    exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def ladybug_tools_folder(folder_path):
    """Set the ladybug-tools-folder configuration variable.

    \b
    Args:
        folder_path: Path to a folder to be set as the ladybug-tools-folder.
            If unspecified, the ladybug-tools-folder will be set back to the default.
    """
    try:
        # load up the config file and reset the variable
        config_file, original_lbt = folders.config_file, folders.ladybug_tools_folder
        with open(config_file) as inf:
            data = json.load(inf)
        data['ladybug_tools_folder'] = folder_path if folder_path is not None else ''
        with open(config_file, 'w') as fp:
            json.dump(data, fp, indent=4)
        msg_end = 'reset to default' if folder_path is None \
            else 'set to: {}'.format(folder_path)
        # clean up the case where loading the config created the default epw folder
        if os.listdir(original_lbt) == ['resources']:
            if os.listdir(os.path.join(original_lbt, 'resources')) == ['weather']:
                # this was just a weather folder created by running ladybug-core
                nukedir(original_lbt, True)
        print('ladybug-tools-folder successfully {}.'.format(msg_end))
    except Exception as e:
        _logger.exception('Failed to set ladybug-tools-folder.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@set_config.command('default-epw-folder')
@click.argument('folder-path', required=False, type=click.Path(
    exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def default_epw_folder(folder_path):
    """Set the default-epw-folder configuration variable.

    \b
    Args:
        folder_path: Path to a folder to be set as the default-epw-folder.
            If unspecified, the default-epw-folder will be set back to the default.
    """
    try:
        config_file = folders.config_file
        with open(config_file) as inf:
            data = json.load(inf)
        data['default_epw_folder'] = folder_path if folder_path is not None else ''
        with open(config_file, 'w') as fp:
            json.dump(data, fp, indent=4)
        msg_end = 'reset to default' if folder_path is None \
            else 'set to: {}'.format(folder_path)
        print('default-epw-folder successfully {}.'.format(msg_end))
    except Exception as e:
        _logger.exception('Failed to set default-epw-folder.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
