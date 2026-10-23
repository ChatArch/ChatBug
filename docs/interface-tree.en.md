# Python Interface Tree

The ChatBug CLI is thin. HTTP evidence classification, marker construction, and lab lifecycle are importable, testable Python modules.

## Package Entry

```python
from chatbug import __version__
```

## Module Tree

```text
chatbug
├── cli.py              # Click arguments, JSON output, and exit codes
├── php2shell.py        # Web version/marker checks and fixed lab payload
├── local_lab.py        # In-process synthetic HTTP contract lab
└── lab.py              # Remote disposable Docker Compose lab lifecycle
```

## `chatbug.php2shell`

```python
from chatbug.php2shell import (
    build_lab_session_payload,
    build_safe_multipart_probe,
    classify_version,
    extract_command_output,
    http_request,
    parse_php_version,
    random_marker,
    safe_url_check,
    scan_common_lfi,
)
```

| API | Purpose | Safety/evidence boundary |
| --- | --- | --- |
| `http_request(...)` | Dependency-free HTTP primitive | Does not follow redirects; reads at most 64 KiB |
| `parse_php_version(headers)` | Parse PHP version from `Server` / `X-Powered-By` | Response headers only |
| `classify_version(version)` | Classify vulnerable/fixed/unknown | Does not infer patch status from a hidden version |
| `random_marker()` | Generate random non-sensitive marker | Marker never appears in validation URL/query/traversal |
| `build_safe_multipart_probe(marker)` | Build upload-progress multipart request | No OOM/UAF/system command; filename contains a fixed PHP `echo` marker that runs only through an LFI include |
| `scan_common_lfi(url, sid, marker)` | Probe a small fixed set of session/include shapes | No arbitrary path input; marker return is a candidate-gadget lead |
| `safe_url_check(url, ...)` | Aggregate version/parser/marker evidence | Never describes a version or marker path as system-command RCE |
| `build_lab_session_payload(sid, proof)` | Build fixed proof payload for isolated lab | `proof` permits exactly three allowlisted modes |
| `extract_command_output(body)` | Extract delimited lab command output | Parses synthetic lab delimiters only |

Typical low-impact website check:

```python
from chatbug.php2shell import safe_url_check

result = safe_url_check(
    "https://owned-site.example/",
    include_multipart=True,
    include_gadgets=False,
)
assert result["schema"] == "chatbug.php2shell.web_check/v1"
assert result["evidence_tier"] == "tier_2_parser_reachable"
```

Before enabling `include_gadgets=True`, confirm target authorization and a suitable maintenance window. `rce_or_file_read_proven` is a compatibility field; in the current implementation, `True` only means that a controlled marker returned through a candidate session/include path, not arbitrary system-command execution or real user-file disclosure.

## `chatbug.local_lab`

```python
from chatbug.local_lab import serve_local_lab
```

`serve_local_lab()` is a context manager that starts a temporary HTTP service on `127.0.0.1:0`:

- `hello.php` always returns `Hello World`;
- `vuln.php` is an in-process include-sink simulation only;
- context exit closes the socket/thread and clears in-memory session state.

It starts no PHP, Docker, or system shell, making it suitable for unit tests and minimal contract examples.

## `chatbug.lab`

```python
from chatbug.lab import LabSpec, logs, run_lfi_proof, seed_marker, start, stop
```

| API | Purpose |
| --- | --- |
| `LabSpec(ssh_host=..., fpm_image=...)` | Describe an owned Docker host and exact PHP-FPM runtime |
| `start(spec)` | Write synthetic Compose/webroot and start internal lab |
| `seed_marker(spec, remote_dir, marker)` | Write random synthetic marker under lab `/tmp` |
| `run_lfi_proof(spec, remote_dir, sid, proof)` | Run fixed positive/negative proof from one-shot internal client |
| `logs(spec, remote_dir)` | Return bounded lab logs for diagnostics |
| `stop(spec, remote_dir)` | Remove Compose project, network, and remote temporary directory |

These APIs generate only synthetic files and accept no production path, production volume, or arbitrary remote command. The CLI calls cleanup from `finally`; only explicit `--keep` retains the lab briefly.

## Output Contracts

### Website check

```text
chatbug.php2shell.web_check/v1
```

Key fields: `verdict`, `evidence_tier`, `rce_or_file_read_proven`, `findings`, `multipart`, and `gadget_scan`. Interpret `rce_or_file_read_proven` using the compatibility semantics above.

### Local contract lab

```text
chatbug.php2shell.local_lab/v1
```

Key fields: `accepted`, `post_status`, `positive_status`, `negative_status`, `positive_output`, and `negative_body`.

### Docker runtime lab

```text
chatbug.php2shell.docker_lab/v1
```

Key fields: `accepted`, `fpm_image`, `proof`, `marker`, `seed`, `result.positive_output`, `result.negative_output`, and `cleanup`.
