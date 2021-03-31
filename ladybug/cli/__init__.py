"""
Command Line Interface (CLI) entry point for ladybug and ladybug extensions.

Use this file only to add command related to ladybug-core. For adding extra commands
from each extention see below.

Note:

    Do not import this module in your code directly unless you are extending the command
    line interface. For running the commands execute them from the command line or as a
    subprocess (e.g. ``subprocess.call(['ladybug', 'viz'])``)

Ladybug uses click (https://click.palletsprojects.com/en/7.x/) for creating the CLI.
You can extend the command line interface from inside each extention by following these
steps:

1. Create a ``cli.py`` file in your extension.
2. Import the ``main`` function from this ``ladybug.cli``.
3. Add your commands and command groups to main using add_command method.
4. Add ``import [your-extention].cli`` to ``__init__.py`` file to the commands are added
   to the cli when the module is loaded.

The good practice is to group all your extention commands in a command group named after
the extension. This will make the commands organized under extension namespace. For
instance commands for `ladybug-comfort` will be called like
``ladybug comfort [comfort-command]``.


.. code-block:: python

    import click
    from ladybug.cli import main

    @click.group()
    def comfort():
        pass

    # add commands to comfort group
    @comfort.command('utci-from-epw')
    # ...
    def utci_from_epw():
        pass

    # finally add the newly created commands to ladybug cli
    main.add_command(comfort)

    # do not forget to import this module in __init__.py otherwise it will not be added
    # to ladybug commands.

Note:

    For extension with several commands you can use a folder structure instead of a single
    file. Refer to ``ladybug-comfort`` for an example.

"""
import click
import sys
import logging
import json

from ..config import folders
from ladybug.cli.setconfig import set_config
from ladybug.cli.translate import translate

_logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def main():
    pass


@main.command('config')
@click.option('--output-file', help='Optional file to output the JSON string of '
              'the config object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def config(output_file):
    """Get a JSON object with all configuration information"""
    try:
        config_dict = {
            'ladybug_tools_folder': folders.ladybug_tools_folder,
            'default_epw_folder': folders.default_epw_folder
        }
        output_file.write(json.dumps(config_dict, indent=4))
    except Exception as e:
        _logger.exception('Failed to retrieve configurations.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@main.command('viz')
def viz():
    """Check if ladybug is flying!"""
    click.echo('viiiiiiiiiiiiizzzzzzzzz!')


main.add_command(set_config, name='set-config')
main.add_command(translate)

if __name__ == "__main__":
    main()
