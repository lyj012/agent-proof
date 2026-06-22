import argparse
import subprocess

import agentproof
from agentproof.cli import create_parser


def test_package_can_be_imported() -> None:
    assert agentproof is not None


def test_version_is_0_1_0() -> None:
    assert agentproof.__version__ == "0.1.0"


def test_cli_parser_can_be_created() -> None:
    parser = create_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_generate_creates_delivery_report(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    source_file = repo / "hello.txt"
    source_file.write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "hello.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add hello"], cwd=repo, check=True, capture_output=True, text=True)

    task_file = tmp_path / "task.json"
    task_file.write_text(
        '{"task_name":"Smoke task","requirement":"Generate a report","build_result":"not_run","test_result":"passed","risks":[],"known_issues":[]}',
        encoding="utf-8",
    )
    transcript_file = tmp_path / "transcript.txt"
    transcript_file.write_text("Implemented the smoke change.", encoding="utf-8")
    output_file = tmp_path / "delivery-report.md"

    parser = create_parser()
    args = parser.parse_args(
        [
            "generate",
            "--repo",
            str(repo),
            "--task-file",
            str(task_file),
            "--transcript",
            str(transcript_file),
            "--output",
            str(output_file),
        ]
    )

    assert args.handler(args) == 0
    report = output_file.read_text(encoding="utf-8")
    assert "# Smoke task" in report
    assert "Implemented the smoke change." in report
    assert "add hello" in report
    assert "hello.txt" in report
