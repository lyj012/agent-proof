from __future__ import annotations

import json
from pathlib import Path
import subprocess


def git(repo: Path, *args: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def create_committed_repo(repo: Path) -> Path:
    repo.mkdir()
    git(repo, "init", capture_output=True)
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")
    source_file = repo / "hello.txt"
    source_file.write_text("hello\n", encoding="utf-8")
    git(repo, "add", "hello.txt")
    git(repo, "commit", "-m", "add hello", capture_output=True)
    source_file.write_text("hello\nworld\n", encoding="utf-8")
    git(repo, "add", "hello.txt")
    git(repo, "commit", "-m", "update hello", capture_output=True)
    return repo


def write_task(
    path: Path,
    *,
    build_result: str = "not_run",
    test_result: str = "passed",
    requirement: str = "Generate a report",
) -> Path:
    path.write_text(
        json.dumps(
            {
                "task_name": "Smoke task",
                "requirement": requirement,
                "build_result": build_result,
                "test_result": test_result,
                "risks": ["Review edge cases"],
                "known_issues": ["No automated build execution in v0.1.0"],
                "acceptance_steps": ["Run agentproof generate"],
                "manual_review": ["Checked generated report structure"],
            }
        ),
        encoding="utf-8",
    )
    return path


def write_transcript(path: Path, content: str = "Implemented the smoke change.") -> Path:
    path.write_text(content, encoding="utf-8")
    return path

