import argparse
import json
from pathlib import Path

from agentproof import __version__
from agentproof.git_reader import read_latest_commit
from agentproof.report_generator import generate_report
from agentproof.transcript_reader import read_transcript


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
    generate_parser.add_argument("--repo", required=True, help="Path to the local Git repository.")
    generate_parser.add_argument("--task-file", required=True, help="Path to the task JSON file.")
    generate_parser.add_argument("--transcript", required=True, help="Path to the development transcript.")
    generate_parser.add_argument(
        "--output",
        default="delivery-report.md",
        help="Output Markdown report path. Defaults to delivery-report.md.",
    )
    generate_parser.set_defaults(handler=_handle_generate)

    return parser


def _handle_generate(args: argparse.Namespace) -> int:
    task = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
    transcript = read_transcript(args.transcript)
    commit = read_latest_commit(args.repo)
    report = generate_report(task, transcript, commit)
    Path(args.output).write_text(report, encoding="utf-8")
    print(f"Generated report: {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "handler"):
        return args.handler(args)

    parser.print_help()
    return 0
