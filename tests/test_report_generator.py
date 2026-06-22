from agentproof.git_reader import CommitInfo
from agentproof.report_generator import generate_report
from agentproof.task_reader import TaskInfo
from agentproof.transcript_reader import TranscriptInfo


def test_generate_report_contains_required_sections(tmp_path) -> None:
    report = _report(tmp_path)

    for heading in [
        "## 1. 交付概览",
        "## 2. 原始需求",
        "## 3. Git 证据",
        "## 4. 修改文件",
        "## 5. Diff 摘要",
        "## 6. AI 辅助开发记录摘要",
        "## 7. 构建结果",
        "## 8. 测试结果",
        "## 9. 风险与遗留问题",
        "## 10. 人工审核清单",
        "## 11. 客户验收步骤",
        "## 12. 证据限制说明",
        "## 13. 报告元信息",
    ]:
        assert heading in report


def test_generate_report_handles_transcript_code_fences(tmp_path) -> None:
    report = _report(tmp_path, transcript=TranscriptInfo("transcript.txt", "```text\ninside\n```", False))

    assert "````text" in report
    assert "```text\ninside\n```" in report


def test_generate_report_defaults_empty_arrays(tmp_path) -> None:
    report = _report(
        tmp_path,
        task=TaskInfo("Task", "Requirement", "not_run", "not_run", [], [], [], []),
    )

    assert "- None declared" in report
    assert "No acceptance steps provided." in report


def test_generate_report_redacts_sensitive_information(tmp_path) -> None:
    report = _report(
        tmp_path,
        task=TaskInfo(
            "Task",
            "Use api_key=abc123 and notify test@example.com",
            "not_run",
            "not_run",
            [],
            [],
            [],
            [],
        ),
        transcript=TranscriptInfo("transcript.txt", "OpenAI key sk-" + "a" * 32, False),
    )

    assert "abc123" not in report
    assert "test@example.com" not in report
    assert "sk-" + "a" * 32 not in report
    assert "[EMAIL_REDACTED]" in report
    assert "[REDACTED]" in report


def test_generate_report_redacts_git_author_email(tmp_path) -> None:
    report = _report(tmp_path)

    assert "test@example.com" not in report
    assert "Test User" in report
    assert "[EMAIL_REDACTED]" in report


def _report(tmp_path, task=None, transcript=None) -> str:
    task = task or TaskInfo(
        "Task",
        "Requirement",
        "not_run",
        "passed",
        ["Risk"],
        ["Issue"],
        ["Open report"],
        ["Checked scope"],
    )
    transcript = transcript or TranscriptInfo("transcript.txt", "Implemented change.", False)
    commit = CommitInfo(
        hash="a" * 40,
        message="update hello",
        author="Test User <test@example.com>",
        date="2026-06-22T00:00:00+00:00",
        changed_files=["hello.txt"],
        shortstat="1 file changed, 1 insertion(+)",
        stat="hello.txt | 1 +",
        insertions=1,
        deletions=0,
    )
    return generate_report(
        task,
        transcript,
        commit,
        tmp_path,
        tmp_path / "task.json",
        tmp_path / "transcript.txt",
        tmp_path / "report.md",
    )

