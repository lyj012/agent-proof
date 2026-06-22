from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from agentproof.errors import AgentProofError


@dataclass(frozen=True)
class CommitInfo:
    hash: str
    message: str
    author: str
    date: str
    changed_files: list[str]
    shortstat: str
    stat: str
    insertions: int
    deletions: int


def read_latest_commit(repo: str | Path) -> CommitInfo:
    repo_path = Path(repo)
    if not repo_path.exists():
        raise AgentProofError(f"Repository path does not exist: {repo_path}")
    if not repo_path.is_dir():
        raise AgentProofError(f"Repository path is not a directory: {repo_path}")

    try:
        _run_git(repo_path, "rev-parse", "--is-inside-work-tree")
    except AgentProofError as exc:
        raise AgentProofError(f"Not a Git work tree: {repo_path}") from exc

    try:
        commit_hash = _run_git(repo_path, "rev-parse", "HEAD")
    except AgentProofError as exc:
        raise AgentProofError("Git repository has no commits.") from exc
    if not commit_hash:
        raise AgentProofError("Git repository has no commits.")

    message = _run_git(repo_path, "log", "-1", "--pretty=%B")
    author = _run_git(repo_path, "log", "-1", "--pretty=%an <%ae>")
    date = _run_git(repo_path, "log", "-1", "--pretty=%cI")
    changed_files_output = _run_git(repo_path, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "HEAD")
    shortstat = _run_git(repo_path, "show", "--shortstat", "--format=", "HEAD")
    stat = _run_git(repo_path, "show", "--stat", "--format=", "HEAD")
    insertions, deletions = _parse_shortstat(shortstat)

    return CommitInfo(
        hash=commit_hash,
        message=message,
        author=author,
        date=date,
        changed_files=[line for line in changed_files_output.splitlines() if line],
        shortstat=shortstat or "0 insertions, 0 deletions",
        stat=stat or "No file-level diff summary available.",
        insertions=insertions,
        deletions=deletions,
    )


def _run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise AgentProofError(message)
    return result.stdout.strip()


def _parse_shortstat(shortstat: str) -> tuple[int, int]:
    insertions = _parse_count(shortstat, r"(\d+)\s+insertion")
    deletions = _parse_count(shortstat, r"(\d+)\s+deletion")
    return insertions, deletions


def _parse_count(text: str, pattern: str) -> int:
    match = re.search(pattern, text)
    if match is None:
        return 0
    return int(match.group(1))
