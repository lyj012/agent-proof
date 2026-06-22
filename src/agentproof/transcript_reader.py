from dataclasses import dataclass
from pathlib import Path

from agentproof.errors import AgentProofError
from agentproof.redaction import redact_text


MAX_TRANSCRIPT_EXCERPT_CHARS = 4000


@dataclass(frozen=True)
class TranscriptInfo:
    filename: str
    excerpt: str
    truncated: bool


def read_transcript(path: str | Path, repo_path: str | Path | None = None) -> TranscriptInfo:
    transcript_path = Path(path)
    if not transcript_path.exists():
        raise AgentProofError(f"Transcript file does not exist: {transcript_path}")
    if not transcript_path.is_file():
        raise AgentProofError(f"Transcript path is not a file: {transcript_path}")

    try:
        content = transcript_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AgentProofError(f"Transcript file is not valid UTF-8: {transcript_path}") from exc

    redacted = redact_text(content, repo_path)
    truncated = len(redacted) > MAX_TRANSCRIPT_EXCERPT_CHARS
    excerpt = redacted[:MAX_TRANSCRIPT_EXCERPT_CHARS] if truncated else redacted
    return TranscriptInfo(filename=transcript_path.name, excerpt=excerpt, truncated=truncated)
