import argparse


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("-q", "--quiet", default=False, action=argparse.BooleanOptionalAction, help="quiet mode")

    return parser.parse_args()
