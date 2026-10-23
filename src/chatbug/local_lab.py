"""Deterministic local HTTP lab for runnable tests and documentation."""

from __future__ import annotations

import contextlib
import http.server
import re
import socketserver
import threading
from dataclasses import dataclass
from typing import Iterator

SESSIONS: dict[str, str] = {}


class LocalLabHandler(http.server.BaseHTTPRequestHandler):
    server_version = "ChatBugLocalLab/1.0"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Powered-By", "PHP/8.1.34")
        self.end_headers()
        self.wfile.write(body)

    @property
    def sid(self) -> str:
        cookie = self.headers.get("Cookie", "")
        start = cookie.find("PHPSESSID=")
        if start < 0:
            return ""
        return cookie[start + len("PHPSESSID=") :].split(";", 1)[0]

    def do_HEAD(self) -> None:  # noqa: N802
        self._send(200, b"")

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        sid = self.sid
        if path == "/hello.php":
            self._send(200, b"Hello World\n")
            return
        if path == "/vuln.php":
            body = SESSIONS.get(sid)
            if body is None:
                self._send(404, b"missing session\n")
            else:
                self._send(200, body.encode("latin-1", errors="replace"))
            return
        self._send(404, b"not found\n")

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        sid = self._form_sid(body) or self.sid
        if not sid:
            self._send(400, b"missing session\n")
            return
        SESSIONS[sid] = body.decode("latin-1", errors="replace")
        self._send(200, b"upload progress accepted\n")

    def _form_sid(self, body: bytes) -> str:
        marker = b'name="PHPSESSID"\r\n\r\n'
        start = body.find(marker)
        if start < 0:
            return ""
        return body[start + len(marker) :].split(b"\r\n", 1)[0].decode()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


@dataclass(frozen=True)
class LocalLab:
    port: int

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


@contextlib.contextmanager
def serve_local_lab() -> Iterator[LocalLab]:
    server = ThreadedHTTPServer(("127.0.0.1", 0), LocalLabHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield LocalLab(port=server.server_port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        SESSIONS.clear()
