from argparse import ArgumentParser, BooleanOptionalAction, Namespace


def parse() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("-q", "--quiet", default=False, action=BooleanOptionalAction, help="quiet mode")
    parser.add_argument("-f", "--filmarks", action="store_true")

    return parser.parse_args()
