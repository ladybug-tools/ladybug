# coding=utf-8
"""Utility functions for running the functions of CLI commands outside of the CLI."""
import sys
import os


def run_command_function(command_function, arguments=None, options=None):
    """Run a function used within the Ladybug Tools CLI.

    Args:
        command_function: The CLI function to be executed.
        arguments: A list of required arguments for the command_function. None can
            be used if the command function has no required arguments. (Default: None).
        options: A dictionary of options to be passed to the function. The keys
            of this dictionary should be the full names of the options or flags
            in the CLI and formatted with dashes (eg. --output-file). The values
            of the dictionary should be the values to be passed for each of
            the options. For the case of flag arguments, the value should simply
            be an empty string. None can be used here to indicate that all default
            values for options should be used. (Default: None).
    """
    # process the arguments and options
    args = () if arguments is None else arguments
    kwargs = {}
    if options is not None:
        for key, val in options.items():
            clean_key = key[2:] if key.startswith('--') else key
            clean_key = clean_key.replace('-', '_')
            clean_val = True if val == '' else val
            kwargs[clean_key] = clean_val

    # run the command using arguments and keyword arguments
    return command_function(*args, **kwargs)


def process_content_to_output(content_str, output_file=None):
    """Process output strings from commands for various formats of output_files.

    Args:
        content_str: A text string for file contents that are being output from
            a command.
        output_file: Any of the typically supported --output-file types of the
            CLI. This can be a string for a file path, a file object, or the stdout
            file object used by click. If None, the string is simply returned from
            this method. (Default: None).
    """
    if output_file is None:
        return content_str
    elif isinstance(output_file, str):
        dir_name = os.path.dirname(os.path.abspath(output_file))
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        if (sys.version_info < (3, 0)):  # we need to manually encode it as UTF-8
            with open(output_file, 'w') as of:
                of.write(content_str.encode('utf-8'))
        else:
            with open(output_file, 'w', encoding='utf-8') as of:
                of.write(content_str)
    else:
        if 'stdout' not in str(output_file):
            dir_name = os.path.dirname(os.path.abspath(output_file.name))
            if not os.path.isdir(dir_name):
                os.makedirs(dir_name)
        output_file.write(content_str)
