from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from agentproof.git_reader import CommitInfo


def generate_report(task: Mapping[str, object], transcript: str, commit: CommitInfo) -> str:
    task_name = _text(task.get("task_name"), "Untitled delivery task")
    requirement = _text(task.get("requirement"), "")
    build_result = _text(task.get("build_result"), "not_provided")
    test_result = _text(task.get("test_result"), "not_provided")
    risks = _list_text(task.get("risks"))
    known_issues = _list_text(task.get("known_issues"))
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")

    sections = [
        f"# {task_name}",
        "## Summary",
        f"- Generated at: {generated_at}",
        f"- Requirement: {requirement or 'Not provided'}",
        f"- Build result: {build_result}",
        f"- Test result: {test_result}",
        "## Latest Commit",
        f"- Hash: `{commit.hash}`",
        f"- Subject: {commit.subject}",
        f"- Author: {commit.author}",
        f"- Date: {commit.date}",
        "## Changed Files",
        _format_list(commit.changed_files),
        "## Development Transcript",
        _code_block(transcript, "text"),
        "## Diff",
        _code_block(commit.diff, "diff"),
        "## Risks",
        _format_list(risks),
        "## Known Issues",
        _format_list(known_issues),
    ]
    return "\n\n".join(sections).rstrip() + "\n"


def _text(value: object, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _list_text(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [str(item) for item in value]


def _format_list(items: Sequence[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def _code_block(value: str, language: str) -> str:
    content = value.rstrip() or "(empty)"
    return f"```{language}\n{content}\n```"
