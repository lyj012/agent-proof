from pathlib import Path


def read_transcript(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")
