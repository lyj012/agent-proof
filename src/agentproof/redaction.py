from __future__ import annotations

from pathlib import Path, PureWindowsPath
import re


SENSITIVE_VALUE = "[REDACTED]"
EMAIL_VALUE = "[EMAIL_REDACTED]"
LOCAL_PATH_VALUE = "[LOCAL_PATH_REDACTED]"
PRIVATE_KEY_VALUE = "[PRIVATE_KEY_REDACTED]"

_KEYWORDS = r"(api_key|apikey|token|secret|password|passwd)"
_JSON_OR_PAIR_RE = re.compile(
    rf"(?i)(?P<prefix>\"?{_KEYWORDS}\"?\s*(?:=|:)\s*)(?P<quote>[\"']?)(?P<value>[^\s\r\n,\"']+)(?P=quote)"
)
_AUTH_BEARER_RE = re.compile(r"(?i)(Authorization\s*:\s*Bearer\s+)([^\s\r\n]+)")
_AUTH_VALUE_RE = re.compile(
    r"(?i)(?P<prefix>\"?authorization\"?\s*(?:=|:)\s*)(?P<quote>[\"']?)(?!Bearer\b)(?P<value>[^\s\r\n,\"']+)(?P=quote)"
)
_COOKIE_RE = re.compile(r"(?i)(Cookie\s*:\s*)([^\r\n]+)")
_WINDOWS_PATH_RE = re.compile(r"(?i)\b[A-Z]:\\(?:[^\\\r\n\"'<>|]+\\)*[^\\\r\n\"'<>|]*?\.[A-Z0-9]{1,10}")
_POSIX_PATH_RE = re.compile(
    r"(?<!\w)/(?:Users|home|var|tmp|private|opt)/(?:[^\r\n\"'<>|]+/)*[^\r\n/\"'<>|]*?\.[A-Za-z0-9]{1,10}"
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
_GITHUB_TOKEN_RE = re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)


def redact_text(text: str, repo_path: str | Path | None = None) -> str:
    redacted = _PRIVATE_KEY_RE.sub(PRIVATE_KEY_VALUE, text)
    redacted = _OPENAI_KEY_RE.sub(SENSITIVE_VALUE, redacted)
    redacted = _GITHUB_TOKEN_RE.sub(SENSITIVE_VALUE, redacted)
    redacted = _JWT_RE.sub(SENSITIVE_VALUE, redacted)
    redacted = _AUTH_BEARER_RE.sub(rf"\1{SENSITIVE_VALUE}", redacted)
    redacted = _AUTH_VALUE_RE.sub(_redact_key_value, redacted)
    redacted = _COOKIE_RE.sub(rf"\1{SENSITIVE_VALUE}", redacted)
    redacted = _JSON_OR_PAIR_RE.sub(_redact_key_value, redacted)
    redacted = _WINDOWS_PATH_RE.sub(lambda match: _redact_windows_path(match.group(0), repo_path), redacted)
    redacted = _POSIX_PATH_RE.sub(lambda match: _redact_posix_path(match.group(0), repo_path), redacted)
    redacted = _EMAIL_RE.sub(EMAIL_VALUE, redacted)
    return redacted


def _redact_key_value(match: re.Match[str]) -> str:
    return f"{match.group('prefix')}{match.group('quote')}{SENSITIVE_VALUE}{match.group('quote')}"


def _redact_windows_path(value: str, repo_path: str | Path | None) -> str:
    path_text = value.rstrip(" .,;)")
    suffix = value[len(path_text) :]
    win_path = PureWindowsPath(path_text)

    if repo_path is not None:
        repo_win = PureWindowsPath(str(Path(repo_path).resolve()))
        try:
            relative = win_path.relative_to(repo_win)
            return str(relative) + suffix
        except ValueError:
            pass

    name = win_path.name
    if name:
        return str(PureWindowsPath(LOCAL_PATH_VALUE) / name) + suffix
    return LOCAL_PATH_VALUE + suffix


def _redact_posix_path(value: str, repo_path: str | Path | None) -> str:
    path_text = value.rstrip(" .,;)")
    suffix = value[len(path_text) :]
    path = Path(path_text)

    if repo_path is not None:
        try:
            relative = path.relative_to(Path(repo_path).resolve())
            return str(relative) + suffix
        except ValueError:
            pass

    if path.name:
        return f"{LOCAL_PATH_VALUE}/{path.name}{suffix}"
    return LOCAL_PATH_VALUE + suffix
