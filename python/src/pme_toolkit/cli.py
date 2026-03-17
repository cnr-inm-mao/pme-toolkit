import argparse

from .run_case import main as run_case_main
from .run_back import main as run_back_main


def main():
    parser = argparse.ArgumentParser(prog="pme-toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a PME case from case.json")
    run_parser.add_argument("config", help="Path to case.json")

    back_parser = subparsers.add_parser("back", help="Run backmapping from backmapping.json")
    back_parser.add_argument("config", help="Path to backmapping.json")

    args = parser.parse_args()

    if args.command == "run":
        run_case_main(args.config)
    elif args.command == "back":
        run_back_main(args.config)


if __name__ == "__main__":
    main()
