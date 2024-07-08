# coding=utf-8
"""Utility functions for running the functions of CLI commands outside of the CLI."""


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
