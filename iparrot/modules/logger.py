# -*- coding: utf-8 -*-

import logging
from logging import handlers

from iparrot.modules.helper import make_dir

logger = logging.getLogger()


def set_logger(mode=1, path="logs", name='parrot.log', level='info'):
    """
    :param mode: 1-on screen, 2-in log file, 3-both 1&2
    :param path: log path, 'None' - <project path>/logs
    :param name: log file name
    :param level: debug / info / warn / error
    """
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARN,
        'error': logging.ERROR
    }
    if mode not in (1, 2, 3):
        mode = 1

    if str(level).lower() not in level_map.keys():
        level = 'info'

    log_file = "{}/{}".format(path, name)

    # logger = logging.getLogger(log_file)
    logger.name = log_file
    # define log format
    fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    logger.setLevel(level_map.get(level))

    if mode in (1, 3):
        # define screen stream handler
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    if mode in (2, 3):
        make_dir(path)
        # define log file handler, backup per week
        fh = handlers.TimedRotatingFileHandler(filename=log_file, when='W0', backupCount=4)
        fh.setFormatter(fmt)
        logger.addHandler(fh)


if __name__ == "__main__":
    set_logger(mode=1)
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warn message")
    logger.error("Error message")

