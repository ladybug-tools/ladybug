import logging
from logging.handlers import TimedRotatingFileHandler
import os
import tempfile

# This is copied from logging module since python 2 doesn't have it under the same name.
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

_name_to_level = {
    'CRITICAL': CRITICAL,
    'FATAL': FATAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
}


def _get_log_folder():
    home_folder = os.getenv('HOME') or os.path.expanduser('~')
    if not os.access(home_folder, os.W_OK):
        home_folder = tempfile.gettempdir()
    log_folder = os.path.join(home_folder, '.ladybug')
    if not os.path.isdir(log_folder):
        os.mkdir(log_folder)
    return log_folder


def _get_log_level(level):
    level = _name_to_level.get(level)
    return level or logging.INFO


def get_logger(name, filename='ladybug.log', file_log_level='DEBUG',
               console_log_level='WARNING'):
    """Get a logger to be used for each module.

    Args:
        name: Logger name. The good practice is to set it to __init__ from inside each
            modules.
        filename: Logger filename.Setting filename to None will remove the file handler
            (Default: ladybug.log).
        file_log_level: Log level for file handler as a string (Default: DEBUG).
        console_log_level: Log level for stream handler as a string (Default: WARNING).
    """
    logger = logging.getLogger(name)

    # create a file handler to log debug and higher level logs
    if filename:
        log_file = os.path.join(_get_log_folder(), filename)
        file_handler = TimedRotatingFileHandler(log_file, when='midnight')
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        file_handler.setLevel(_get_log_level(file_log_level))
        logger.addHandler(file_handler)

    # create a console handler that only prints out errors and warnings
    stream_handler = logging.StreamHandler()
    stream_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_format)
    stream_handler.setLevel(_get_log_level(console_log_level))

    logger.addHandler(stream_handler)

    return logger
