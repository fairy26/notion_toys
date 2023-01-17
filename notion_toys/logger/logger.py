from importlib import resources
from logging import Logger, getLogger
from logging.config import dictConfig

import yaml

CONFIGFILE = "log_config.yaml"
LOGGERNAME = "notion_toys"


def init_logger() -> None:
    with resources.path("logger", CONFIGFILE) as log_config:
        with open(log_config, encoding="utf-8") as f:
            dictConfig(yaml.safe_load(f))


def get_logger() -> Logger:
    return getLogger(LOGGERNAME)
