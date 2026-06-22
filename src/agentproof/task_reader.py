from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from agentproof.errors import AgentProofError


ALLOWED_RESULTS = {"not_run", "passed", "failed", "unknown"}
OPTIONAL_ARRAY_FIELDS = ("risks", "known_issues", "acceptance_steps", "manual_review")


@dataclass(frozen=True)
class TaskInfo:
    task_name: str
    requirement: str
    build_result: str
    test_result: str
    risks: list[str]
    known_issues: list[str]
    acceptance_steps: list[str]
    manual_review: list[str]


def read_task(path: str | Path) -> TaskInfo:
    task_path = Path(path)
    if not task_path.exists():
        raise AgentProofError(f"Task file does not exist: {task_path}")
    if not task_path.is_file():
        raise AgentProofError(f"Task file is not a file: {task_path}")

    try:
        raw = task_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AgentProofError(f"Task file is not valid UTF-8: {task_path}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AgentProofError(f"Task file is not valid JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise AgentProofError("Task file must contain a JSON object.")

    return validate_task(data)


def validate_task(data: dict[str, Any]) -> TaskInfo:
    for field in ("task_name", "requirement", "build_result", "test_result"):
        if field not in data:
            raise AgentProofError(f"Task file is missing required field: {field}")

    task_name = _required_text(data["task_name"], "task_name")
    requirement = _required_text(data["requirement"], "requirement")
    build_result = _result_value(data["build_result"], "build_result")
    test_result = _result_value(data["test_result"], "test_result")

    arrays = {field: _string_array(data.get(field, []), field) for field in OPTIONAL_ARRAY_FIELDS}
    return TaskInfo(
        task_name=task_name,
        requirement=requirement,
        build_result=build_result,
        test_result=test_result,
        risks=arrays["risks"],
        known_issues=arrays["known_issues"],
        acceptance_steps=arrays["acceptance_steps"],
        manual_review=arrays["manual_review"],
    )


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentProofError(f"Task field must be a non-empty string: {field}")
    return value.strip()


def _result_value(value: object, field: str) -> str:
    if not isinstance(value, str) or value not in ALLOWED_RESULTS:
        allowed = ", ".join(sorted(ALLOWED_RESULTS))
        raise AgentProofError(f"Task field {field} must be one of: {allowed}")
    return value


def _string_array(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise AgentProofError(f"Task field must be an array of strings: {field}")

    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise AgentProofError(f"Task field must be an array of strings: {field}")
        text = item.strip()
        if text:
            cleaned.append(text)
    return cleaned

