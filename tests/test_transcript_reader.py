import pytest

from agentproof.errors import AgentProofError
from agentproof.transcript_reader import MAX_TRANSCRIPT_EXCERPT_CHARS, read_transcript


def test_read_transcript_reads_utf8_text(tmp_path) -> None:
    transcript_file = tmp_path / "transcript.txt"
    transcript_file.write_text("Implemented change.", encoding="utf-8")

    transcript = read_transcript(transcript_file)

    assert transcript.filename == "transcript.txt"
    assert transcript.excerpt == "Implemented change."
    assert transcript.truncated is False


def test_read_transcript_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(AgentProofError, match="does not exist"):
        read_transcript(tmp_path / "missing.txt")


def test_read_transcript_rejects_non_utf8_file(tmp_path) -> None:
    transcript_file = tmp_path / "transcript.txt"
    transcript_file.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(AgentProofError, match="UTF-8"):
        read_transcript(transcript_file)


def test_read_transcript_truncates_long_text(tmp_path) -> None:
    transcript_file = tmp_path / "transcript.txt"
    transcript_file.write_text("a" * (MAX_TRANSCRIPT_EXCERPT_CHARS + 10), encoding="utf-8")

    transcript = read_transcript(transcript_file)

    assert transcript.truncated is True
    assert len(transcript.excerpt) == MAX_TRANSCRIPT_EXCERPT_CHARS


def test_read_transcript_redacts_content(tmp_path) -> None:
    transcript_file = tmp_path / "transcript.txt"
    transcript_file.write_text("api_key=abc123\ncontact test@example.com", encoding="utf-8")

    transcript = read_transcript(transcript_file)

    assert "abc123" not in transcript.excerpt
    assert "test@example.com" not in transcript.excerpt
    assert "[REDACTED]" in transcript.excerpt
    assert "[EMAIL_REDACTED]" in transcript.excerpt

