from . import argparser, notion
from .logger import get_logger


def main():
    args = argparser.parse()

    logger = get_logger(conf=args)

    if args.filmarks:
        logger.info("FilmarksとNotionを同期します")
        notion.run(logger, parse_all=args.all)
