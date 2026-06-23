# AgentProof

AgentProof is a local Python CLI tool for generating Markdown delivery and acceptance reports for AI-assisted software development work.

## Current Status

AgentProof v0.1.0 is an initial closed-loop version. It can generate a local delivery report from task metadata, the latest Git commit, and a transcript file, but the product positioning and manager-facing experience are not final.

Known positioning issue: the current workflow is still developer-led. Non-technical managers should receive the generated HTML report, not operate the CLI directly. Later versions should improve the handoff flow, report language, and reviewer experience before treating this as a polished management product.

It reads three user-specified local inputs:

1. A developer-authored `task.json` file.
2. The latest commit from a local Git repository.
3. A user-provided AI-assisted development transcript text file.

AgentProof redacts common sensitive values and generates a fixed-structure report that a developer, customer, or project owner can review.

## Why AgentProof

AI-assisted development often leaves delivery evidence scattered across Git commits, chat transcripts, manual test notes, and developer memory.

AgentProof helps turn that evidence into one predictable report:

- what the task was;
- what Git commit was inspected;
- which files changed;
- what the diff summary says;
- what the developer declared about build and test results;
- what risks or known issues remain;
- what a human reviewer still needs to check.

AgentProof does not prove that the code is correct. It organizes evidence for human review.

## Workflow

```text
task.json + local Git latest commit + transcript.txt
        -> AgentProof redaction
        -> delivery-report.md
        -> human review and customer acceptance
```

## Features

- Local CLI command: `agentproof generate`.
- UTF-8 `task.json` validation.
- Latest local Git commit metadata.
- Changed file list from the latest commit.
- Diff summary from `git show --shortstat --format= HEAD` and `git show --stat --format= HEAD`.
- Transcript excerpt with a maximum length of 4000 characters.
- Redaction for common secrets, emails, local paths, bearer tokens, cookies, JWTs, and private key blocks.
- Fixed Markdown report structure.
- Optional browser-friendly HTML report.
- Optional auto-open after report generation.
- Clear evidence source labels.
- Build and test result labels showing they are developer-declared.

## Not Provided

AgentProof v0.1.0 does not provide:

- AI API calls;
- AI semantic summaries;
- automatic build execution;
- automatic test execution;
- automatic code review;
- multi-commit ranges;
- `base..head` diff mode;
- GitHub API, GitHub App, or PR comments;
- web UI;
- database storage;
- SaaS features;
- digital signatures or cryptographic evidence chains.

## Requirements

- Python 3.11 or newer.
- Git installed and available on `PATH`.
- A local Git repository with at least one commit.
- UTF-8 encoded task and transcript files.

AgentProof supports Windows and also runs on Linux/macOS.

## Installation

For local development:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

For local CLI usage without test dependencies:

```bash
python -m pip install -e .
```

Check the installed CLI:

```bash
agentproof --version
agentproof --help
```

## Quick Start

From the AgentProof repository root, generate a local Markdown report plus a browser-friendly HTML report:

```bash
agentproof generate \
  --repo . \
  --task-file examples/task.json \
  --transcript examples/transcript.txt \
  --output delivery-report.md \
  --html-output delivery-report.html \
  --open
```

On Windows PowerShell:

```powershell
agentproof generate `
  --repo . `
  --task-file examples\task.json `
  --transcript examples\transcript.txt `
  --output delivery-report.md `
  --html-output delivery-report.html `
  --open
```

`delivery-report.html` can be opened directly in a browser and is better suited for managers or non-technical reviewers. `delivery-report.md` remains the plain Markdown source report for archiving or developer review.

`--repo .` reads the latest commit from the current AgentProof repository. The Git evidence in the generated report therefore depends on your local checkout and current latest commit.

The committed `examples/delivery-report.md` file is a static example generated from an independent temporary demo Git repository. Its repository name, commit hash, and changed file list are not expected to match reports generated with `--repo .`.

## CLI Usage

Show top-level help:

```bash
agentproof --help
```

Show version:

```bash
agentproof --version
```

Show `generate` help:

```bash
agentproof generate --help
```

Generate a report:

```bash
agentproof generate \
  --repo <repo> \
  --task-file <task.json> \
  --transcript <transcript.txt> \
  --output <report.md> \
  --html-output <report.html> \
  --open
```

Arguments:

- `--repo`: required local Git repository path.
- `--task-file`: required UTF-8 JSON task file.
- `--transcript`: required UTF-8 text or Markdown transcript file.
- `--output`: optional Markdown output path. Defaults to `delivery-report.md`.
- `--html-output`: optional HTML output path for browser-friendly viewing.
- `--open`: optional flag to open the generated report with the system default application. If `--html-output` is provided, AgentProof opens the HTML report.

## task.json Fields

Recommended structure:

```json
{
  "task_name": "Add settings export command",
  "requirement": "Add a small CLI command that exports user settings to a Markdown file.",
  "build_result": "passed",
  "test_result": "passed",
  "risks": ["Manual review is still required."],
  "known_issues": ["No automated build execution in v0.1.0."],
  "acceptance_steps": ["Open the generated report."],
  "manual_review": ["Confirmed modified files belong to this task."]
}
```

Required fields:

- `task_name`: non-empty string.
- `requirement`: non-empty string.
- `build_result`: one of `not_run`, `passed`, `failed`, `unknown`.
- `test_result`: one of `not_run`, `passed`, `failed`, `unknown`.

Optional array fields:

- `risks`
- `known_issues`
- `acceptance_steps`
- `manual_review`

Optional arrays must contain strings. Empty strings are ignored. Unknown fields are allowed but ignored.

## Transcript Files

The transcript is a user-specified UTF-8 text or Markdown file.

AgentProof does not scan Codex, Claude Code, editor, or system history directories. It reads only the file passed to `--transcript`.

The report includes a deterministic excerpt:

- read the transcript;
- redact sensitive values;
- truncate to 4000 characters;
- show `Transcript truncated: yes` or `Transcript truncated: no`.

The transcript excerpt is not an AI-generated summary.

## Output Report Structure

Generated reports use this fixed structure:

```text
# 交付报告
## 1. 交付概览
## 2. 原始需求
## 3. Git 证据
## 4. 修改文件
## 5. Diff 摘要
## 6. AI 辅助开发记录摘要
## 7. 构建结果
## 8. 测试结果
## 9. 风险与遗留问题
## 10. 人工审核清单
## 11. 客户验收步骤
## 12. 证据限制说明
## 13. 报告元信息
```

## Privacy and Redaction

AgentProof runs completely locally.

AgentProof does not call OpenAI, Claude, or any other AI API. It does not upload files, commits, transcripts, or reports.

AgentProof applies best-effort local redaction for:

- `api_key`, `apikey`, `token`, `secret`, `password`, `passwd`;
- `Authorization: Bearer ...`;
- `Cookie: ...`;
- email addresses;
- Windows local absolute paths;
- Linux/macOS local absolute paths;
- OpenAI-style keys;
- GitHub personal access token shapes;
- JWT-like tokens;
- PEM private key blocks.

Redaction is not a security audit. Review the generated report before sharing it.

## Complete Example

Install locally:

```bash
python -m pip install -e ".[dev]"
```

Generate a local demonstration report:

```bash
agentproof generate \
  --repo . \
  --task-file examples/task.json \
  --transcript examples/transcript.txt \
  --output delivery-report.md
```

Run tests:

```bash
pytest -q
```

The example files are:

- `examples/task.json`
- `examples/transcript.txt`
- `examples/delivery-report.md`

The transcript intentionally contains fake tokens, a fake email address, fake local paths, and a fake private key block to demonstrate redaction.

`examples/delivery-report.md` is checked in as a static output sample. It was generated from a temporary demo Git repository whose latest commit changed `settings_export.py`. The command above is for exercising the CLI in your current checkout and may produce different Git repository, commit, and file evidence.

## Project Limits

AgentProof v0.1.0 has deliberate limits:

- It reads only the latest Git commit.
- It does not read uncommitted changes.
- It does not read a commit range.
- It does not call GitHub APIs.
- It does not execute build commands.
- It does not execute test commands.
- Build and test results come from developer declarations in `task.json`.
- The generated report cannot prove the code is absolutely correct.
- Final delivery and acceptance still require human review.

## Roadmap

Possible future versions may add:

- selecting a specific commit;
- reading a commit range;
- importing build or test output files;
- richer transcript formats;
- optional report variants;
- stricter schema validation.

These are not part of v0.1.0.

## License

AgentProof is released under the MIT License. See [LICENSE](LICENSE).
