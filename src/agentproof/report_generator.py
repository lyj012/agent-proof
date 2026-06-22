from __future__ import annotations

from datetime import datetime
from pathlib import Path
from collections.abc import Sequence

from agentproof import __version__
from agentproof.git_reader import CommitInfo
from agentproof.redaction import redact_text
from agentproof.task_reader import TaskInfo
from agentproof.transcript_reader import TranscriptInfo


MANUAL_REVIEW_CHECKLIST = [
    "原始需求与交付内容是否一致",
    "修改文件是否属于本次任务范围",
    "是否存在无关代码修改",
    "是否包含密钥、token、密码、cookie 或其他敏感信息",
    "构建结果是否由开发者确认",
    "测试结果是否由开发者确认",
    "风险和遗留问题是否已经说明",
    "客户验收步骤是否明确、可执行",
    "证据限制是否已经告知客户或项目负责人",
]


def generate_report(
    task: TaskInfo,
    transcript: TranscriptInfo,
    commit: CommitInfo,
    repo: str | Path,
    task_file: str | Path,
    transcript_file: str | Path,
    output: str | Path,
) -> str:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    repo_path = Path(repo)
    repo_summary = repo_path.name or str(repo_path)
    short_hash = commit.hash[:7]

    requirement = redact_text(task.requirement, repo_path)
    risks = [redact_text(item, repo_path) for item in task.risks]
    known_issues = [redact_text(item, repo_path) for item in task.known_issues]
    acceptance_steps = [redact_text(item, repo_path) for item in task.acceptance_steps]
    manual_review = [redact_text(item, repo_path) for item in task.manual_review]
    commit_message = redact_text(commit.message, repo_path)
    stat = redact_text(commit.stat, repo_path)

    sections = [
        "# 交付报告",
        "## 1. 交付概览",
        f"- Task name: {redact_text(task.task_name, repo_path)}",
        f"- Generated at: {generated_at}",
        f"- AgentProof version: {__version__}",
        f"- Git repository: {repo_summary}",
        f"- Latest commit: `{short_hash}`",
        f"- Build result declaration: {task.build_result}",
        f"- Test result declaration: {task.test_result}",
        "## 2. 原始需求",
        requirement,
        "## 3. Git 证据",
        f"- Hash: `{commit.hash}`",
        f"- Message: {commit_message or '(empty)'}",
        f"- Author: {commit.author}",
        f"- Date: {commit.date}",
        "- Evidence source: local Git repository latest 1 commit",
        "## 4. 修改文件",
        _format_list(commit.changed_files),
        "## 5. Diff 摘要",
        f"- Insertions: {commit.insertions}",
        f"- Deletions: {commit.deletions}",
        "- Stat source: `git show --shortstat --format= HEAD` and `git show --stat --format= HEAD`",
        _code_block(stat, "text"),
        "## 6. AI 辅助开发记录摘要",
        f"- Transcript file: {transcript.filename}",
        "- Read status: read from user-specified local transcript file",
        f"- Transcript truncated: {'yes' if transcript.truncated else 'no'}",
        "- Summary type: deterministic redacted excerpt, not AI semantic summary",
        _code_block(transcript.excerpt, "text"),
        "## 7. 构建结果",
        f"Build result: {task.build_result}\nSource: developer-declared\nAgentProof executed build: no",
        "## 8. 测试结果",
        f"Test result: {task.test_result}\nSource: developer-declared\nAgentProof executed tests: no",
        "## 9. 风险与遗留问题",
        "### Risks",
        _format_list(risks),
        "### Known issues",
        _format_list(known_issues),
        "## 10. 人工审核清单",
        _format_checklist(MANUAL_REVIEW_CHECKLIST),
        "### Developer-declared completed review items",
        _format_list(manual_review, empty="None declared"),
        "## 11. 客户验收步骤",
        _format_numbered(acceptance_steps)
        if acceptance_steps
        else "No acceptance steps provided. Developer should add project-specific verification steps before delivery.",
        "## 12. 证据限制说明",
        "\n".join(
            [
                "- AgentProof only reads user-specified local inputs.",
                "- AgentProof v0.1.0 only reads the latest 1 commit.",
                "- AgentProof v0.1.0 does not execute build commands.",
                "- AgentProof v0.1.0 does not execute test commands.",
                "- Build and test results in this report are developer-declared.",
                "- This report does not prove the code is correct or that the requirement is complete.",
                "- Final acceptance requires human confirmation.",
            ]
        ),
        "## 13. 报告元信息",
        "\n".join(
            [
                f"- AgentProof version: {__version__}",
                f"- Report generated at: {generated_at}",
                f"- Task file: {Path(task_file).name}",
                f"- Transcript file: {Path(transcript_file).name}",
                f"- Output file: {Path(output).name}",
                "- Evidence levels: developer-declared task data; AgentProof-read local Git and transcript evidence; human final confirmation required.",
            ]
        ),
    ]
    return "\n\n".join(sections).rstrip() + "\n"


def _format_list(items: Sequence[str], empty: str = "None declared") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def _format_numbered(items: Sequence[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def _format_checklist(items: Sequence[str]) -> str:
    return "\n".join(f"- [ ] {item}" for item in items)


def _code_block(value: str, language: str) -> str:
    content = value.rstrip() or "(empty)"
    fence = "`" * max(3, _longest_backtick_run(content) + 1)
    return f"{fence}{language}\n{content}\n{fence}"


def _longest_backtick_run(content: str) -> int:
    longest = 0
    current = 0
    for character in content:
        if character == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest
