# PHP2Shell Isolated Reproduction Lab

This page gives ChatBug's complete runnable acceptance path and states exactly what it proves and what it does not. It uses the ordinary-website model rather than reserving a product-specific CLI for any one application.

> **Critical boundary:** the PHP2Shell CVEs are PHP runtime memory-safety issues. ChatBug does not send OOM, UAF, or crash payloads for CVE-2026-109618/109619 to either production or the lab. The full lab on this page validates a different deterministic chain: `session upload-progress + application include gadget`. Both may affect patch priority, but they cannot be substituted for or described as the same production-RCE conclusion.

## Choose the Right Evidence Tier

| Goal | Recommended command | What it can establish | What it cannot establish |
| --- | --- | --- | --- |
| Inventory only the runtime version | `web check <URL> --skip-multipart` | HTTP/version-banner exposure | Parser, gadget, or command execution |
| Confirm ordinary upload entry point | `web check <URL> --skip-gadget-scan` | Multipart parser reachability | LFI, PHP echo, or system command |
| Check a fixed session/include marker | `web check <URL>` | Controlled marker-path lead | Arbitrary command, user-data read, or memory-CVE exploitation |
| Regress request/response contract | `lab local-list` | Local positive/negative protocol contract | Real PHP or shell execution |
| Accept fixed command output | `lab docker-list` | Fixed `ls/cat` with runtime + lab-only gadget | Real application gadget or production-CVE exploitation |

## Lab-Only Chain Overview

The following chain is generated only by the temporary environment created by `docker-list`:

```text
multipart POST
  └─ PHP_SESSION_UPLOAD_PROGRESS writes a lab session file
      └─ filename carries PHP code for a fixed allowlisted proof
          └─ lab-only include($_GET['page']) includes the session file
              └─ fixed ls/cat output returns in the positive response
```

A real application must meet every condition for the same conclusion:

- without an application include/LFI sink, report only runtime/parser exposure;
- `docker exec ... php` is management-plane execution, not unauthenticated exploitation;
- an ordinary PHP page reading a file does not mean a remote attacker can execute a command.

## Local Contract Lab {#local-contract-lab}

```bash
python -m pip install ChatBug
chatbug php2shell lab local-list
```

The command starts a temporary HTTP server bound to `127.0.0.1:0` in the current process and runs positive and negative controls:

- a multipart request is recorded as synthetic session state;
- positive `vuln.php` returns synthetic `/tmp`, `chatbug-marker.txt`, and a random marker;
- negative `hello.php` returns only `Hello World`;
- context cleanup closes socket/thread resources and clears in-memory state.

Successful JSON shape:

```json
{
  "accepted": true,
  "positive_status": 200,
  "negative_status": 200,
  "positive_output": "/tmp\nchatbug-marker.txt\nCHATBUG_MARKER_EXAMPLE",
  "negative_body": "Hello World\n"
}
```

This is a deterministic contract/regression example. It starts no real PHP, Docker, or system shell. Use it in CI:

```bash
python -m pytest -q tests/test_php2shell.py
```

## Docker Runtime Lab {#docker-runtime-lab}

Run this on an owned Docker host:

```bash
chatbug php2shell lab docker-list \
  --ssh-host <owned-docker-host> \
  --fpm-image <exact-runtime-image-or-digest> \
  --proof list-and-marker
```

`--ssh-host` is required. The default `php:8.1.34-fpm-alpine` image validates the workflow; for parity with an assessed service, `--fpm-image` must name the exact PHP-FPM runtime digest.

Each run creates a unique directory under remote `<chatarch-home>/chatbug/labs/` and only generates:

- the selected PHP-FPM image, Nginx, and one-shot Python client;
- `hello.php`, which always returns `Hello World`;
- `vuln.php`, existing only in the lab, containing `include($_GET['page'])`;
- upload-progress/session settings;
- an internal-only Docker network;
- a random synthetic marker at `/tmp/chatbug-marker.txt`.

It mounts no production database, mail, attachment, user-directory, credential, log, or real session volume, and publishes no host port. By default it deletes the Compose project, network, and remote temporary directory; `--keep` is only for short SSH investigation.

## Fixed Proof Modes

`--proof` has no arbitrary shell parameter. It permits exactly:

| proof | Fixed lab action | Positive acceptance |
| --- | --- | --- |
| `list-tmp` | `ls -la /tmp` | The listing includes synthetic `chatbug-marker.txt` |
| `cat-marker` | `cat /tmp/chatbug-marker.txt` | Returns this run's random marker |
| `list-and-marker` | `ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt` | Returns listing, `MARKER`, and random marker |

The default `list-and-marker` is the most complete and auditable acceptance mode.

## Positive and Negative Acceptance

With `list-and-marker`, `result.positive_output` looks like the following. ChatBug removes its internal delimiters and retains only command output:

```text
total 24
...
-rw-r--r-- ... chatbug-marker.txt
-rw------- ... sess_lab...
MARKER
CHATBUG_MARKER_...
```

`result.negative_output` must be:

```text
Hello World
```

The exact positive condition varies by proof, but `accepted=true` always requires:

- HTTP 200 from multipart POST, positive include, and negative normal page;
- proof-specific positive evidence (`list-tmp` uses the marker filename; the other two use the random marker);
- no random marker in negative output;
- Compose project and remote directory cleanup unless `--keep` was selected.

Describe this result as “**selected runtime plus lab-only include gadget proven in isolation**,” never as “production PHP2Shell RCE reproduced.”

## Live Website Check

### Low-Impact Version/Entry-Point Check

```bash
chatbug php2shell web check https://owned-service.example/ --skip-gadget-scan
```

This reads version headers and sends an ordinary multipart parser check. It makes no session-include request and is appropriate for initial production inventory.

### Authorized Marker Probe

```bash
chatbug php2shell web check https://owned-service.example/
```

This mode additionally sends a fixed `<?php echo '<marker>'; ?>` filename and probes a small fixed set of session/include shapes. It executes no system command and reads no real user file, but an LFI can cause the controlled `echo` in the target PHP process. Use it only under explicit authorization and an appropriate logging/maintenance window.

| Field | Correct interpretation |
| --- | --- |
| `verdict=vulnerable_version_exposed` | Version banner is affected; confirm the real HTTP SAPI and plan remediation |
| `evidence_tier=tier_2_parser_reachable` | Ordinary multipart traffic reached parser path |
| `evidence_tier=tier_3_gadget_found` | Fixed marker returned through a candidate session/include path; manually review the application gadget |
| `rce_or_file_read_proven=true` | Compatibility field meaning controlled marker path, not arbitrary system command, real file read, or CVE memory-exploit success |

## Remediation After Reproduction

1. Inventory every PHP SAPI serving real HTTP traffic: FPM, mod_php, FrankenPHP, LiteSpeed, and so on. CLI versions are not Web-runtime evidence.
2. Upgrade to the official fixed release, then read back the running container digest, package version, or HTTP-SAPI version.
3. Audit and remove untrusted file-inclusion/path-construction sinks.
4. Tighten upload handling, session save paths, temporary-directory permissions, and error exposure.
5. After remediation, rerun low-impact `web check --skip-gadget-scan`, then rerun positive/negative acceptance in the same-image data-free lab.
6. If compromise is suspected, separately investigate access logs, abnormal sessions, webshells, child processes, and outbound connections. Vulnerability validation is not forensics.
