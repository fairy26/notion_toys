from importlib import resources
from logging import DEBUG, ERROR, Logger, getLogger
from logging.config import dictConfig

import yaml

CONFIGFILE = "log_config.yaml"
LOGGERNAME = "notion_toys"


def init_logger(filename: str = CONFIGFILE) -> None:
    with resources.files("docs").joinpath(filename).open() as f:
        dictConfig(yaml.safe_load(f))


def get_logger(conf, name: str = LOGGERNAME) -> Logger:
    logger = getLogger(name)

    # change logger
    if conf.debug:
        logger = getLogger()  # root Logger; 'console'

    # change logger level
    if conf.verbose:
        logger.setLevel(DEBUG)
    if conf.quiet:
        logger.setLevel(ERROR)

    return logger
