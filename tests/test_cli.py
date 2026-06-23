import pytest

from agentproof.cli import create_parser, main
from conftest import create_committed_repo, write_task, write_transcript


def test_cli_version(capsys) -> None:
    parser = create_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])

    assert exc_info.value.code == 0
    assert "agentproof 0.1.0" in capsys.readouterr().out


def test_cli_no_args_shows_help(capsys) -> None:
    assert main([]) == 0

    assert "usage: agentproof" in capsys.readouterr().out


def test_cli_generate_help(capsys) -> None:
    parser = create_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["generate", "--help"])

    assert exc_info.value.code == 0
    assert "--task-file" in capsys.readouterr().out


def test_cli_generate_success(tmp_path) -> None:
    repo = create_committed_repo(tmp_path / "repo")
    task_file = write_task(tmp_path / "task.json")
    transcript_file = write_transcript(tmp_path / "transcript.txt")
    output_file = tmp_path / "report.md"

    result = _run_generate(repo, task_file, transcript_file, output_file)

    assert result == 0
    assert output_file.exists()


def test_cli_generate_writes_html_output(tmp_path) -> None:
    repo = create_committed_repo(tmp_path / "repo")
    task_file = write_task(tmp_path / "task.json")
    transcript_file = write_transcript(tmp_path / "transcript.txt")
    output_file = tmp_path / "report.md"
    html_output_file = tmp_path / "report.html"

    result = _run_generate(repo, task_file, transcript_file, output_file, html_output_file=html_output_file)

    assert result == 0
    assert output_file.exists()
    assert html_output_file.exists()
    assert '<html lang="zh-CN">' in html_output_file.read_text(encoding="utf-8")


def test_cli_generate_open_prefers_html_output(tmp_path, monkeypatch) -> None:
    repo = create_committed_repo(tmp_path / "repo")
    task_file = write_task(tmp_path / "task.json")
    transcript_file = write_transcript(tmp_path / "transcript.txt")
    output_file = tmp_path / "report.md"
    html_output_file = tmp_path / "report.html"
    opened_urls = []

    monkeypatch.setattr("agentproof.cli.webbrowser.open", opened_urls.append)

    result = _run_generate(
        repo,
        task_file,
        transcript_file,
        output_file,
        html_output_file=html_output_file,
        open_report=True,
    )

    assert result == 0
    assert opened_urls == [html_output_file.resolve().as_uri()]


def test_cli_generate_rejects_missing_task(tmp_path) -> None:
    repo = create_committed_repo(tmp_path / "repo")
    transcript_file = write_transcript(tmp_path / "transcript.txt")

    assert _run_generate(repo, tmp_path / "missing.json", transcript_file, tmp_path / "report.md") == 1


def test_cli_generate_rejects_missing_transcript(tmp_path) -> None:
    repo = create_committed_repo(tmp_path / "repo")
    task_file = write_task(tmp_path / "task.json")

    assert _run_generate(repo, task_file, tmp_path / "missing.txt", tmp_path / "report.md") == 1


def test_cli_generate_rejects_missing_repo(tmp_path) -> None:
    task_file = write_task(tmp_path / "task.json")
    transcript_file = write_transcript(tmp_path / "transcript.txt")

    assert _run_generate(tmp_path / "missing-repo", task_file, transcript_file, tmp_path / "report.md") == 1


def test_cli_generate_rejects_missing_output_directory(tmp_path) -> None:
    repo = create_committed_repo(tmp_path / "repo")
    task_file = write_task(tmp_path / "task.json")
    transcript_file = write_transcript(tmp_path / "transcript.txt")

    assert _run_generate(repo, task_file, transcript_file, tmp_path / "missing" / "report.md") == 1


def _run_generate(repo, task_file, transcript_file, output_file, html_output_file=None, open_report=False) -> int:
    parser = create_parser()
    argv = [
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
    if html_output_file:
        argv.extend(["--html-output", str(html_output_file)])
    if open_report:
        argv.append("--open")
    args = parser.parse_args(argv)
    return args.handler(args)
