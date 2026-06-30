import pytest

from agentproof.git_reader import CommitInfo
from agentproof.report_generator import generate_html_report, generate_report
from agentproof.task_reader import TaskInfo
from agentproof.transcript_reader import TranscriptInfo


def test_generate_report_contains_required_sections(tmp_path) -> None:
    report = _report(tmp_path)

    for heading in [
        "## 管理者摘要",
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

    assert report.index("## 管理者摘要") < report.index("## 1. 交付概览")


def test_generate_report_handles_transcript_code_fences(tmp_path) -> None:
    report = _report(tmp_path, transcript=TranscriptInfo("transcript.txt", "```text\ninside\n```", False))

    assert "````text" in report
    assert "```text\ninside\n```" in report


def test_generate_report_defaults_empty_arrays(tmp_path) -> None:
    report = _report(
        tmp_path,
        task=TaskInfo("Task", "Requirement", "not_run", "not_run", [], [], [], []),
    )

    assert "- 未声明" in report
    assert "未提供客户验收步骤。" in report
    assert "None declared" not in report


def test_manager_summary_contains_required_fields(tmp_path) -> None:
    report = _report(tmp_path)
    summary = _section_between(report, "## 管理者摘要", "## 1. 交付概览")

    for text in [
        "交付结论：构建或测试声明未全部通过，需要人工复核后再验收。",
        "任务名称：Task",
        "构建情况：未执行（来自开发者声明；AgentProof 未实际执行构建）",
        "测试情况：通过（来自开发者声明；AgentProof 未实际执行测试）",
        "风险数量：1",
        "已知问题数量：1",
        "风险/问题提示：存在风险或遗留问题，需要人工确认。",
        "建议验收动作：Open report",
    ]:
        assert text in summary


@pytest.mark.parametrize(
    ("status", "label"),
    [
        ("passed", "通过"),
        ("failed", "失败"),
        ("not_run", "未执行"),
        ("unknown", "未知"),
    ],
)
def test_generate_report_maps_statuses_to_chinese(tmp_path, status, label) -> None:
    report = _report(
        tmp_path,
        task=TaskInfo("Task", "Requirement", status, status, [], [], ["Accept"], []),
    )

    assert f"构建结果声明：{label}" in report
    assert f"测试结果声明：{label}" in report
    assert f"构建结果：{label}" in report
    assert f"测试结果：{label}" in report
    assert f"构建情况：{label}" in report
    assert f"测试情况：{label}" in report


@pytest.mark.parametrize(
    ("build_result", "test_result"),
    [
        ("failed", "passed"),
        ("not_run", "passed"),
        ("unknown", "passed"),
        ("passed", "failed"),
        ("passed", "not_run"),
        ("passed", "unknown"),
    ],
)
def test_manager_summary_requires_review_for_non_passed_statuses(tmp_path, build_result, test_result) -> None:
    report = _report(
        tmp_path,
        task=TaskInfo("Task", "Requirement", build_result, test_result, [], [], ["Accept"], []),
    )
    conclusion_line = next(
        line for line in _section_between(report, "## 管理者摘要", "## 1. 交付概览").splitlines()
        if line.startswith("- 交付结论：")
    )

    assert "需要人工复核后再验收" in conclusion_line
    assert "已通过" not in conclusion_line
    assert "可直接验收" not in conclusion_line


def test_manager_summary_uses_default_acceptance_action(tmp_path) -> None:
    report = _report(
        tmp_path,
        task=TaskInfo("Task", "Requirement", "passed", "passed", [], [], [], []),
    )
    summary = _section_between(report, "## 管理者摘要", "## 1. 交付概览")

    assert "交付结论：构建和测试声明均为通过，可进入人工验收。" in summary
    assert "建议验收动作：请项目负责人按人工审核清单和客户验收步骤确认后再验收。" in summary
    assert "风险/问题提示：未声明风险或遗留问题。" in summary


def test_manager_summary_warns_when_risks_or_issues_exist(tmp_path) -> None:
    report = _report(
        tmp_path,
        task=TaskInfo("Task", "Requirement", "passed", "passed", ["Risk"], ["Issue"], ["Accept"], []),
    )
    summary = _section_between(report, "## 管理者摘要", "## 1. 交付概览")

    assert "存在风险或遗留问题，需要人工确认。" in summary


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


def test_generate_report_uses_chinese_fixed_labels(tmp_path) -> None:
    report = _report(tmp_path)

    assert "任务名称：Task" in report
    assert "构建结果：未执行" in report
    assert "测试结果：通过" in report
    assert "来源：开发者声明" in report
    assert "Evidence source" not in report


def test_generate_html_report_renders_browser_friendly_html(tmp_path) -> None:
    report = _report(tmp_path)
    html = generate_html_report(report)

    assert '<html lang="zh-CN">' in html
    assert "<h1>交付报告</h1>" in html
    assert html.index("<h2>管理者摘要</h2>") < html.index("<h2>1. 交付概览</h2>")
    assert "<h2>管理者摘要</h2>" in html
    assert "<h2>1. 交付概览</h2>" in html
    assert "任务名称：Task" in html


def _section_between(report: str, start: str, end: str) -> str:
    return report[report.index(start):report.index(end)]


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
