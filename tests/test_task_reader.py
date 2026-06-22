import json

import pytest

from agentproof.errors import AgentProofError
from agentproof.task_reader import read_task


def test_read_task_accepts_valid_json(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps(
            {
                "task_name": "Add report",
                "requirement": "Generate a delivery report",
                "build_result": "not_run",
                "test_result": "passed",
                "risks": ["Manual review required", ""],
                "known_issues": [],
                "acceptance_steps": ["Open the report"],
                "manual_review": ["Checked scope"],
                "unknown": "ignored",
            }
        ),
        encoding="utf-8",
    )

    task = read_task(task_file)

    assert task.task_name == "Add report"
    assert task.risks == ["Manual review required"]
    assert task.acceptance_steps == ["Open the report"]


def test_read_task_rejects_missing_required_field(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps({"task_name": "Task", "build_result": "not_run", "test_result": "passed"}),
        encoding="utf-8",
    )

    with pytest.raises(AgentProofError, match="missing required field"):
        read_task(task_file)


def test_read_task_rejects_empty_string(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps(
            {"task_name": " ", "requirement": "Requirement", "build_result": "not_run", "test_result": "passed"}
        ),
        encoding="utf-8",
    )

    with pytest.raises(AgentProofError, match="non-empty string"):
        read_task(task_file)


def test_read_task_rejects_invalid_build_result(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps(
            {"task_name": "Task", "requirement": "Requirement", "build_result": "done", "test_result": "passed"}
        ),
        encoding="utf-8",
    )

    with pytest.raises(AgentProofError, match="build_result"):
        read_task(task_file)


def test_read_task_rejects_invalid_test_result(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps(
            {"task_name": "Task", "requirement": "Requirement", "build_result": "not_run", "test_result": "done"}
        ),
        encoding="utf-8",
    )

    with pytest.raises(AgentProofError, match="test_result"):
        read_task(task_file)


def test_read_task_rejects_non_string_array_item(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps(
            {
                "task_name": "Task",
                "requirement": "Requirement",
                "build_result": "not_run",
                "test_result": "passed",
                "risks": ["ok", 123],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(AgentProofError, match="array of strings"):
        read_task(task_file)


def test_read_task_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(AgentProofError, match="does not exist"):
        read_task(tmp_path / "missing.json")


def test_read_task_rejects_invalid_json(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_text("{not-json", encoding="utf-8")

    with pytest.raises(AgentProofError, match="valid JSON"):
        read_task(task_file)


def test_read_task_rejects_non_utf8_file(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(AgentProofError, match="UTF-8"):
        read_task(task_file)

