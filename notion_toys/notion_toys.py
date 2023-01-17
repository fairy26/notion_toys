from . import argparser, notion
from .logger import ERROR, get_logger


def main():
    logger = get_logger()

    args = argparser.parse()
    if args.quiet:
        logger.setLevel(ERROR)

    if args.filmarks:
        logger.info("FilmarksとNotionを同期します")
        notion.run(logger)
