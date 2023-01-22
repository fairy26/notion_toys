from argparse import ArgumentParser, Namespace


def parse() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("-q", "--quiet", action="store_true", help="quiet mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    parser.add_argument("--debug", action="store_true", help="use only root logger")
    parser.add_argument("-f", "--filmarks", action="store_true", help="parse Filmarks reviews and upload to Notion")
    parser.add_argument("-a", "--all", action="store_true", help="parse all reviews (default: only on first page)")

    return parser.parse_args()
