import argparse
import json
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
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = _write_task(tmp_path / "task.json")
    transcript_file = tmp_path / "transcript.txt"
    transcript_file.write_text("Implemented the smoke change.", encoding="utf-8")
    output_file = tmp_path / "delivery-report.md"

    result = _run_generate(repo, task_file, transcript_file, output_file)

    assert result == 0
    report = output_file.read_text(encoding="utf-8")
    assert "# 交付报告" in report
    assert "## 1. 交付概览" in report
    assert "## 13. 报告元信息" in report
    assert "Implemented the smoke change." in report
    assert "add hello" in report
    assert "hello.txt" in report
    assert "AgentProof executed build: no" in report
    assert "AgentProof executed tests: no" in report


def test_generate_rejects_non_git_directory(tmp_path) -> None:
    repo = tmp_path / "not-git"
    repo.mkdir()
    task_file = _write_task(tmp_path / "task.json")
    transcript_file = _write_transcript(tmp_path / "transcript.txt")

    result = _run_generate(repo, task_file, transcript_file, tmp_path / "report.md")

    assert result == 1


def test_generate_rejects_empty_git_repository(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", capture_output=True)

    task_file = _write_task(tmp_path / "task.json")
    transcript_file = _write_transcript(tmp_path / "transcript.txt")

    result = _run_generate(repo, task_file, transcript_file, tmp_path / "report.md")

    assert result == 1


def test_generate_rejects_missing_task_file(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    transcript_file = _write_transcript(tmp_path / "transcript.txt")

    result = _run_generate(repo, tmp_path / "missing.json", transcript_file, tmp_path / "report.md")

    assert result == 1


def test_generate_rejects_invalid_task_json(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = tmp_path / "task.json"
    task_file.write_text("{not-json", encoding="utf-8")
    transcript_file = _write_transcript(tmp_path / "transcript.txt")

    result = _run_generate(repo, task_file, transcript_file, tmp_path / "report.md")

    assert result == 1


def test_generate_rejects_missing_required_task_field(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps({"task_name": "Task", "build_result": "not_run", "test_result": "not_run"}),
        encoding="utf-8",
    )
    transcript_file = _write_transcript(tmp_path / "transcript.txt")

    result = _run_generate(repo, task_file, transcript_file, tmp_path / "report.md")

    assert result == 1


def test_generate_rejects_invalid_result_enum(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = _write_task(tmp_path / "task.json", build_result="done")
    transcript_file = _write_transcript(tmp_path / "transcript.txt")

    result = _run_generate(repo, task_file, transcript_file, tmp_path / "report.md")

    assert result == 1


def test_generate_rejects_missing_transcript(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = _write_task(tmp_path / "task.json")

    result = _run_generate(repo, task_file, tmp_path / "missing.txt", tmp_path / "report.md")

    assert result == 1


def test_generate_marks_long_transcript_as_truncated(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = _write_task(tmp_path / "task.json")
    transcript_file = _write_transcript(tmp_path / "transcript.txt", "a" * 4100)
    output_file = tmp_path / "report.md"

    result = _run_generate(repo, task_file, transcript_file, output_file)

    assert result == 0
    report = output_file.read_text(encoding="utf-8")
    assert "Transcript truncated: yes" in report
    assert "a" * 4000 in report
    assert "a" * 4001 not in report


def test_generate_preserves_transcript_code_fences(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = _write_task(tmp_path / "task.json")
    transcript_file = _write_transcript(tmp_path / "transcript.txt", "```text\ninside\n```")
    output_file = tmp_path / "report.md"

    result = _run_generate(repo, task_file, transcript_file, output_file)

    assert result == 0
    report = output_file.read_text(encoding="utf-8")
    assert "````text" in report
    assert "```text\ninside\n```" in report


def test_generate_redacts_sensitive_information(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = _write_task(tmp_path / "task.json", requirement="Use api_key=abc123")
    transcript_file = _write_transcript(
        tmp_path / "transcript.txt",
        'token: secret-token\nAuthorization: Bearer bearer-token\nCookie: session=abc',
    )
    output_file = tmp_path / "report.md"

    result = _run_generate(repo, task_file, transcript_file, output_file)

    assert result == 0
    report = output_file.read_text(encoding="utf-8")
    assert "[REDACTED]" in report
    assert "abc123" not in report
    assert "secret-token" not in report
    assert "bearer-token" not in report
    assert "session=abc" not in report


def test_generate_supports_windows_paths_with_spaces_and_chinese(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo with 中文")
    task_file = _write_task(tmp_path / "task with 中文.json")
    transcript_file = _write_transcript(tmp_path / "transcript with 中文.txt")
    output_file = tmp_path / "delivery report 中文.md"

    result = _run_generate(repo, task_file, transcript_file, output_file)

    assert result == 0
    assert output_file.exists()


def test_generate_redacts_windows_absolute_paths(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = _write_task(tmp_path / "task.json")
    transcript_file = _write_transcript(
        tmp_path / "transcript.txt",
        r"See C:\Users\name\项目 资料\secret file.txt before delivery",
    )
    output_file = tmp_path / "report.md"

    result = _run_generate(repo, task_file, transcript_file, output_file)

    assert result == 0
    report = output_file.read_text(encoding="utf-8")
    assert r"C:\Users\name\项目 资料\secret file.txt" not in report
    assert r"[LOCAL_PATH_REDACTED]\secret file.txt before delivery" in report


def test_generate_rejects_missing_output_directory(tmp_path) -> None:
    repo = _create_committed_repo(tmp_path / "repo")
    task_file = _write_task(tmp_path / "task.json")
    transcript_file = _write_transcript(tmp_path / "transcript.txt")

    result = _run_generate(repo, task_file, transcript_file, tmp_path / "missing" / "report.md")

    assert result == 1


def _create_committed_repo(repo):
    repo.mkdir()
    _git(repo, "init", capture_output=True)
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    source_file = repo / "hello.txt"
    source_file.write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "hello.txt")
    _git(repo, "commit", "-m", "add hello", capture_output=True)
    return repo


def _write_task(path, build_result="not_run", test_result="passed", requirement="Generate a report"):
    path.write_text(
        json.dumps(
            {
                "task_name": "Smoke task",
                "requirement": requirement,
                "build_result": build_result,
                "test_result": test_result,
                "risks": [],
                "known_issues": [],
                "acceptance_steps": [],
                "manual_review": [],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_transcript(path, content="Implemented the smoke change."):
    path.write_text(content, encoding="utf-8")
    return path


def _run_generate(repo, task_file, transcript_file, output_file) -> int:
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
    return args.handler(args)


def _git(repo, *args, capture_output=False):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
