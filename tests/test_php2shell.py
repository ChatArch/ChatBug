from click.testing import CliRunner

from chatbug.cli import main
from chatbug.php2shell import (
    build_lab_session_payload,
    build_safe_multipart_probe,
    classify_version,
    extract_command_output,
)


def test_classify_version_flags_eol_php_8_1():
    assert classify_version((8, 1, 34))["status"] == "vulnerable"
    assert classify_version((8, 2, 35))["status"] == "fixed"
    assert classify_version((8, 2, 34))["status"] == "vulnerable"


def test_safe_multipart_probe_uses_upload_progress():
    marker = "CHATBUG_MARKER_TEST"
    headers, body, sid = build_safe_multipart_probe(marker)
    text = body.decode("latin-1")
    assert sid.startswith("chatbug")
    assert "PHP_SESSION_UPLOAD_PROGRESS" in text
    assert marker in text
    assert "multipart/form-data" in headers["Content-Type"]


def test_lab_payload_is_allowlisted_and_marks_delimiters():
    headers, body = build_lab_session_payload("sid123", "list-and-marker")
    text = body.decode("latin-1")
    assert "ls -la /tmp" in text
    assert "cat /tmp/chatbug-marker.txt" in text
    assert "___START___" in text and "___END___" in text
    assert headers["Cookie"] == "PHPSESSID=sid123"


def test_extract_command_output():
    assert extract_command_output(b"x___START___\n/tmp/a\n___END___y") == "/tmp/a"


def test_local_lab_cli_acceptance():
    result = CliRunner().invoke(main, ["php2shell", "lab", "local-list"])
    assert result.exit_code == 0, result.output
    assert '"accepted": true' in result.output
    assert "chatbug-marker.txt" in result.output
    assert "Hello World" in result.output
