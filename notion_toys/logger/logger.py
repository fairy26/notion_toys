from importlib import resources
from logging import Logger, getLogger
from logging.config import dictConfig

import yaml

CONFIGFILE = "log_config.yaml"
LOGGERNAME = "notion_toys"


def init_logger(filename: str = CONFIGFILE) -> None:
    with resources.files("docs").joinpath(filename).open() as f:
        dictConfig(yaml.safe_load(f))


def get_logger(name: str = LOGGERNAME) -> Logger:
    return getLogger(name)
