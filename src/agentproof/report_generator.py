from __future__ import annotations

from datetime import datetime
from html import escape
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

RESULT_LABELS = {
    "passed": "通过",
    "failed": "失败",
    "not_run": "未执行",
    "unknown": "未知",
}


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
    task_name = redact_text(task.task_name, repo_path)
    build_result = _result_label(task.build_result)
    test_result = _result_label(task.test_result)
    commit_message = redact_text(commit.message, repo_path)
    author = redact_text(commit.author, repo_path)
    stat = redact_text(commit.stat, repo_path)
    transcript_excerpt = redact_text(transcript.excerpt, repo_path)

    sections = [
        "# 交付报告",
        "## 管理者摘要",
        _format_manager_summary(
            task_name=task_name,
            build_result=build_result,
            test_result=test_result,
            risks=risks,
            known_issues=known_issues,
            acceptance_steps=acceptance_steps,
        ),
        "## 1. 交付概览",
        f"- 任务名称：{task_name}",
        f"- 生成时间：{generated_at}",
        f"- AgentProof 版本：{__version__}",
        f"- Git 仓库：{repo_summary}",
        f"- 最新提交：`{short_hash}`",
        f"- 构建结果声明：{build_result}",
        f"- 测试结果声明：{test_result}",
        "## 2. 原始需求",
        requirement,
        "## 3. Git 证据",
        f"- 提交哈希：`{commit.hash}`",
        f"- 提交说明：{commit_message or '（空）'}",
        f"- 作者：{author}",
        f"- 提交时间：{commit.date}",
        "- 证据来源：本地 Git 仓库最新 1 次提交",
        "## 4. 修改文件",
        _format_list(commit.changed_files),
        "## 5. Diff 摘要",
        f"- 新增行数：{commit.insertions}",
        f"- 删除行数：{commit.deletions}",
        "- 统计来源：`git show --shortstat --format= HEAD` 和 `git show --stat --format= HEAD`",
        _code_block(stat, "text"),
        "## 6. AI 辅助开发记录摘要",
        f"- 开发记录文件：{transcript.filename}",
        "- 读取状态：已读取用户指定的本地开发记录文件",
        f"- 是否截断：{'是' if transcript.truncated else '否'}",
        "- 摘要类型：确定性脱敏摘录，不是 AI 语义总结",
        _code_block(transcript_excerpt, "text"),
        "## 7. 构建结果",
        f"构建结果：{build_result}\n来源：开发者声明\nAgentProof 是否执行构建：否",
        "## 8. 测试结果",
        f"测试结果：{test_result}\n来源：开发者声明\nAgentProof 是否执行测试：否",
        "## 9. 风险与遗留问题",
        "### 风险",
        _format_list(risks, empty="未声明"),
        "### 已知问题",
        _format_list(known_issues, empty="未声明"),
        "## 10. 人工审核清单",
        _format_checklist(MANUAL_REVIEW_CHECKLIST),
        "### 开发者声明已完成的审核项",
        _format_list(manual_review, empty="未声明"),
        "## 11. 客户验收步骤",
        _format_numbered(acceptance_steps)
        if acceptance_steps
        else "未提供客户验收步骤。对外交付前，开发者应补充针对本项目的验收步骤。",
        "## 12. 证据限制说明",
        "\n".join(
            [
                "- AgentProof 只读取用户指定的本地输入。",
                "- AgentProof v0.1.0 只读取最新 1 次提交。",
                "- AgentProof v0.1.0 不会执行构建命令。",
                "- AgentProof v0.1.0 不会执行测试命令。",
                "- 本报告中的构建和测试结果来自开发者声明。",
                "- 本报告不能证明代码绝对正确，也不能证明需求已经完整交付。",
                "- 最终验收仍需要人工确认。",
            ]
        ),
        "## 13. 报告元信息",
        "\n".join(
            [
                f"- AgentProof 版本：{__version__}",
                f"- 报告生成时间：{generated_at}",
                f"- 任务文件：{Path(task_file).name}",
                f"- 开发记录文件：{Path(transcript_file).name}",
                f"- 输出文件：{Path(output).name}",
                "- 证据等级：开发者声明的任务数据；AgentProof 读取的本地 Git 和开发记录证据；最终仍需人工确认。",
            ]
        ),
    ]
    return "\n\n".join(sections).rstrip() + "\n"


def _result_label(result: str) -> str:
    return RESULT_LABELS.get(result, "未知")


def _format_manager_summary(
    *,
    task_name: str,
    build_result: str,
    test_result: str,
    risks: Sequence[str],
    known_issues: Sequence[str],
    acceptance_steps: Sequence[str],
) -> str:
    needs_review = build_result != "通过" or test_result != "通过"
    has_open_items = bool(risks or known_issues)

    if needs_review:
        conclusion = "构建或测试声明未全部通过，需要人工复核后再验收。"
    elif has_open_items:
        conclusion = "构建和测试声明均为通过，但存在风险或遗留问题，需要人工确认。"
    else:
        conclusion = "构建和测试声明均为通过，可进入人工验收。"

    risk_note = (
        "存在风险或遗留问题，需要人工确认。"
        if has_open_items
        else "未声明风险或遗留问题。"
    )
    acceptance_action = (
        acceptance_steps[0]
        if acceptance_steps
        else "请项目负责人按人工审核清单和客户验收步骤确认后再验收。"
    )

    return "\n".join(
        [
            f"- 交付结论：{conclusion}",
            f"- 任务名称：{task_name}",
            f"- 构建情况：{build_result}（来自开发者声明；AgentProof 未实际执行构建）",
            f"- 测试情况：{test_result}（来自开发者声明；AgentProof 未实际执行测试）",
            f"- 风险数量：{len(risks)}",
            f"- 已知问题数量：{len(known_issues)}",
            f"- 风险/问题提示：{risk_note}",
            f"- 建议验收动作：{acceptance_action}",
        ]
    )


def generate_html_report(markdown_report: str, title: str = "交付报告") -> str:
    body = _markdown_to_html(markdown_report)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --paper: #ffffff;
      --text: #20242a;
      --muted: #5c6672;
      --border: #d9dee7;
      --accent: #1f6feb;
      --code-bg: #f1f4f8;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif;
      line-height: 1.72;
    }}
    main {{
      width: min(960px, calc(100% - 32px));
      margin: 32px auto;
      padding: 40px;
      background: var(--paper);
      border: 1px solid var(--border);
      border-radius: 8px;
      box-sizing: border-box;
    }}
    h1 {{
      margin: 0 0 24px;
      font-size: 32px;
      line-height: 1.25;
    }}
    h2 {{
      margin: 32px 0 12px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
      font-size: 22px;
    }}
    h3 {{
      margin: 20px 0 8px;
      font-size: 18px;
    }}
    p, ul, ol, pre {{
      margin: 10px 0;
    }}
    li {{
      margin: 4px 0;
    }}
    code {{
      padding: 2px 5px;
      border-radius: 4px;
      background: var(--code-bg);
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.94em;
    }}
    pre {{
      overflow-x: auto;
      padding: 14px 16px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--code-bg);
      white-space: pre-wrap;
      word-break: break-word;
    }}
    pre code {{
      padding: 0;
      background: transparent;
    }}
    .muted {{
      color: var(--muted);
    }}
    @media print {{
      body {{ background: #fff; }}
      main {{ width: auto; margin: 0; padding: 0; border: 0; }}
    }}
  </style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


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


def _markdown_to_html(markdown_report: str) -> str:
    html_parts: list[str] = []
    list_type: str | None = None
    in_code = False
    code_lines: list[str] = []

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            html_parts.append(f"</{list_type}>")
            list_type = None

    for line in markdown_report.splitlines():
        if line.startswith("```") or line.startswith("````"):
            if in_code:
                html_parts.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                in_code = False
            else:
                close_list()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            close_list()
            continue

        if stripped.startswith("# "):
            close_list()
            html_parts.append(f"<h1>{_inline_markdown(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            close_list()
            html_parts.append(f"<h2>{_inline_markdown(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            close_list()
            html_parts.append(f"<h3>{_inline_markdown(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            if list_type != "ul":
                close_list()
                html_parts.append("<ul>")
                list_type = "ul"
            html_parts.append(f"<li>{_inline_markdown(stripped[2:])}</li>")
        elif _is_numbered_item(stripped):
            if list_type != "ol":
                close_list()
                html_parts.append("<ol>")
                list_type = "ol"
            html_parts.append(f"<li>{_inline_markdown(stripped.split('. ', 1)[1])}</li>")
        else:
            close_list()
            html_parts.append(f"<p>{_inline_markdown(stripped)}</p>")

    if in_code:
        html_parts.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
    close_list()
    return "\n".join(html_parts)


def _is_numbered_item(value: str) -> bool:
    number, separator, _ = value.partition(". ")
    return bool(separator) and number.isdecimal()


def _inline_markdown(value: str) -> str:
    parts = value.split("`")
    rendered: list[str] = []
    for index, part in enumerate(parts):
        if index % 2:
            rendered.append(f"<code>{escape(part)}</code>")
        else:
            rendered.append(escape(part))
    return "".join(rendered)
