from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class CommitInfo:
    hash: str
    subject: str
    author: str
    date: str
    changed_files: list[str]
    diff: str


def read_latest_commit(repo: str | Path) -> CommitInfo:
    repo_path = Path(repo)
    _run_git(repo_path, "rev-parse", "--is-inside-work-tree")

    commit_hash = _run_git(repo_path, "rev-parse", "HEAD")
    subject = _run_git(repo_path, "log", "-1", "--pretty=%s")
    author = _run_git(repo_path, "log", "-1", "--pretty=%an <%ae>")
    date = _run_git(repo_path, "log", "-1", "--pretty=%cI")
    changed_files_output = _run_git(repo_path, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "HEAD")
    diff = _run_git(repo_path, "show", "--format=", "--no-ext-diff", "--find-renames", "HEAD")

    return CommitInfo(
        hash=commit_hash,
        subject=subject,
        author=author,
        date=date,
        changed_files=[line for line in changed_files_output.splitlines() if line],
        diff=diff,
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
        raise RuntimeError(message)
    return result.stdout.strip()
