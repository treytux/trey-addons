# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
import logging
import sys

__all__ = ['init_logger']


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = list(range(8))
RESET_SEQ = '\033[0m'
COLOR_SEQ = '\033[1;%dm'
BOLD_SEQ = '\033[1m'
COLORS = {
    'TRACE': MAGENTA,
    'WARNING': YELLOW,
    'INFO': GREEN,
    'DEBUG': CYAN,
    'CRITICAL': RED,
    'ERROR': RED
}
logging.TRACE = 9


class ColoredFormatter(logging.Formatter):

    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        if self.use_color and record.levelname in COLORS:
            record.msg = (
                COLOR_SEQ % (30 + COLORS[record.levelname]) +
                record.msg + RESET_SEQ)
        return logging.Formatter.format(self, record)


def _use_color():
    return sys.platform == 'darwin' or sys.platform[:5] == 'linux'


def init_logger(name, debug=False):
    log = logging.getLogger(name)
    logging.root = log

    formatter = ColoredFormatter('%(message)s', use_color=_use_color())
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    log.addHandler(console)

    log.setLevel(debug and logging.DEBUG or logging.INFO)

    def out(*args, **kwargs):
        log.log(logging.INFO + 2, *args, **kwargs)

    log.out = out
    return log
