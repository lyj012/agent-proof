# Changelog

## v0.1.0

Initial MVP release preparation.

Implemented:

- Local `agentproof` CLI with `generate` command.
- UTF-8 `task.json` validation.
- Latest local Git commit evidence reading.
- Transcript reading, redaction, and fixed-length excerpt generation.
- Fixed Markdown delivery report structure.
- Build and test result source labeling as developer-declared.
- Basic sensitive data redaction for common secrets, emails, local paths, tokens, JWTs, and private key blocks.
- Example input files and generated example report.
- Pytest coverage for task reading, redaction, transcript reading, Git reading, report generation, and CLI behavior.
- GitHub Actions CI for Python 3.11 and 3.12.

Current limitations:

- Reads only the latest local Git commit.
- Does not execute build commands.
- Does not execute test commands.
- Does not call AI APIs or generate semantic summaries.
- Does not prove the code is correct or the requirement is complete.
- Final delivery still requires human review.

