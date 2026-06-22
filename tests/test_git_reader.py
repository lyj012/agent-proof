import pytest

from agentproof.errors import AgentProofError
from agentproof.git_reader import read_latest_commit
from conftest import create_committed_repo, git


def test_read_latest_commit_reads_commit_metadata(tmp_path) -> None:
    repo = create_committed_repo(tmp_path / "repo")

    commit = read_latest_commit(repo)

    assert len(commit.hash) == 40
    assert commit.message == "update hello"
    assert commit.author == "Test User <test@example.com>"
    assert commit.date
    assert commit.changed_files == ["hello.txt"]
    assert commit.insertions == 1
    assert commit.deletions == 0
    assert "hello.txt" in commit.stat


def test_read_latest_commit_rejects_missing_repo(tmp_path) -> None:
    with pytest.raises(AgentProofError, match="does not exist"):
        read_latest_commit(tmp_path / "missing")


def test_read_latest_commit_rejects_non_git_directory(tmp_path) -> None:
    repo = tmp_path / "not-git"
    repo.mkdir()

    with pytest.raises(AgentProofError, match="Not a Git work tree"):
        read_latest_commit(repo)


def test_read_latest_commit_rejects_repo_without_commits(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", capture_output=True)

    with pytest.raises(AgentProofError, match="no commits"):
        read_latest_commit(repo)

