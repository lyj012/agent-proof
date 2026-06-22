from agentproof.redaction import EMAIL_VALUE, LOCAL_PATH_VALUE, PRIVATE_KEY_VALUE, SENSITIVE_VALUE, redact_text


def test_redacts_key_value_sensitive_fields() -> None:
    text = "\n".join(
        [
            "api_key=abc123",
            "apikey: abc123",
            "token=abc123",
            "secret=abc123",
            "password=abc123",
            "passwd=abc123",
        ]
    )

    redacted = redact_text(text)

    assert redacted.count(SENSITIVE_VALUE) == 6
    assert "abc123" not in redacted


def test_redacts_authorization_bearer_and_cookie() -> None:
    text = "Authorization: Bearer bearer-token\nCookie: session=abc"

    redacted = redact_text(text)

    assert "Authorization: Bearer [REDACTED]" in redacted
    assert "Cookie: [REDACTED]" in redacted
    assert "bearer-token" not in redacted
    assert "session=abc" not in redacted


def test_redacts_windows_local_path() -> None:
    redacted = redact_text(r"Open C:\Users\name\project secret\config.txt now")

    assert r"C:\Users\name\project secret\config.txt" not in redacted
    assert rf"{LOCAL_PATH_VALUE}\config.txt now" in redacted


def test_redacts_posix_local_path() -> None:
    redacted = redact_text("Open /Users/name/project secret/config.txt now")

    assert "/Users/name/project secret/config.txt" not in redacted
    assert f"{LOCAL_PATH_VALUE}/config.txt now" in redacted


def test_redacts_email_address() -> None:
    redacted = redact_text("Author: Test User <test.user@example.com>")

    assert "test.user@example.com" not in redacted
    assert "Test User" in redacted
    assert EMAIL_VALUE in redacted


def test_redacts_openai_style_key() -> None:
    secret = "sk-" + "a" * 32

    redacted = redact_text(f"key {secret}")

    assert secret not in redacted
    assert SENSITIVE_VALUE in redacted


def test_redacts_github_token() -> None:
    token = "ghp_" + "A" * 36

    redacted = redact_text(f"token {token}")

    assert token not in redacted
    assert SENSITIVE_VALUE in redacted


def test_redacts_jwt() -> None:
    jwt = "eyJ" + "a" * 16 + "." + "b" * 16 + "." + "c" * 16

    redacted = redact_text(f"jwt {jwt}")

    assert jwt not in redacted
    assert SENSITIVE_VALUE in redacted


def test_redacts_private_key_block() -> None:
    private_key = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----"

    redacted = redact_text(private_key)

    assert private_key not in redacted
    assert PRIVATE_KEY_VALUE in redacted


def test_does_not_redact_ordinary_text() -> None:
    text = "AgentProof reads local evidence and generates a Markdown report."

    assert redact_text(text) == text

