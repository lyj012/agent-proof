from __future__ import annotations

from pathlib import Path, PureWindowsPath
import re


SENSITIVE_VALUE = "[REDACTED]"
LOCAL_PATH_VALUE = "[LOCAL_PATH_REDACTED]"

_KEYWORDS = r"(api_key|apikey|token|secret|password|passwd|authorization|cookie)"
_JSON_OR_PAIR_RE = re.compile(
    rf"(?i)(?P<prefix>\"?{_KEYWORDS}\"?\s*(?:=|:)\s*)(?P<quote>[\"']?)(?P<value>[^\r\n,\"']+)(?P=quote)"
)
_AUTH_BEARER_RE = re.compile(r"(?i)(Authorization\s*:\s*Bearer\s+)([^\s\r\n]+)")
_COOKIE_RE = re.compile(r"(?i)(Cookie\s*:\s*)([^\r\n]+)")
_WINDOWS_PATH_RE = re.compile(r"(?i)\b[A-Z]:\\(?:[^\\\r\n\"'<>|]+\\)*[^\\\r\n\"'<>|]*?\.[A-Z0-9]{1,10}")


def redact_text(text: str, repo_path: str | Path | None = None) -> str:
    redacted = _AUTH_BEARER_RE.sub(rf"\1{SENSITIVE_VALUE}", text)
    redacted = _COOKIE_RE.sub(rf"\1{SENSITIVE_VALUE}", redacted)
    redacted = _JSON_OR_PAIR_RE.sub(_redact_key_value, redacted)
    redacted = _WINDOWS_PATH_RE.sub(lambda match: _redact_windows_path(match.group(0), repo_path), redacted)
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
