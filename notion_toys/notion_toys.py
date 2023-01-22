from . import argparser, notion
from .logger import DEBUG, ERROR, get_logger


def main():
    logger = get_logger()

    args = argparser.parse()
    if args.verbose:
        logger.setLevel(DEBUG)
    if args.quiet:
        logger.setLevel(ERROR)

    if args.filmarks:
        logger.info("FilmarksとNotionを同期します")
        notion.run(logger, parse_all=args.all)
