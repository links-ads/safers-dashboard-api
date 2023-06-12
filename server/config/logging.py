import logging
from enum import Enum

from django.utils.log import ServerFormatter


class Colors(str, Enum):
    # possible colors: https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    WHITE = "\x1b[37;20m"
    CYAN = "\x1b[36;20m"
    YELLOW = "\x1b[93;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    DEFAULT = "\x1b[0m"


FormatMap = {
    logging.DEBUG: Colors.DEFAULT.value,
    logging.INFO: Colors.DEFAULT.value,
    logging.WARNING: Colors.YELLOW.value,
    logging.ERROR: Colors.RED.value,
    logging.CRITICAL: Colors.BOLD_RED.value,
}


class ColoredFormatter(ServerFormatter):
    """
    A custom logging formatter to use in development.  Makes different 
    log levels stand out w/ pretty colors.  (Just helps when there are 
    loads of messages to sift through.)
    """
    def format(self, record):

        msg = super().format(record)
        colored_msg_prefix = FormatMap.get(record.levelno, Colors.DEFAULT.value)
        colored_msg_suffix = Colors.DEFAULT.value
        return colored_msg_prefix + msg + colored_msg_suffix
