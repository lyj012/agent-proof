import argparse

from agentproof import __version__


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentproof",
        description="Generate local AI-assisted delivery reports.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a delivery report.",
        description="Generate a delivery report.",
    )
    generate_parser.add_argument("--repo", help="Path to the local Git repository.")
    generate_parser.add_argument("--task-file", help="Path to the task JSON file.")
    generate_parser.add_argument("--transcript", help="Path to the development transcript.")
    generate_parser.add_argument(
        "--output",
        default="delivery-report.md",
        help="Output Markdown report path. Defaults to delivery-report.md.",
    )
    generate_parser.set_defaults(handler=_handle_generate)

    return parser


def _handle_generate(args: argparse.Namespace) -> int:
    raise SystemExit("generate is not implemented yet.")


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "handler"):
        return args.handler(args)

    parser.print_help()
    return 0
