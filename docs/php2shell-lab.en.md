# PHP2Shell Reproduction Lab

This page explains how ChatBug safely reproduces the complete chain from PHP runtime risk plus an application LFI gadget to `ls/cat` output. The example uses the ordinary-website model; it does not reserve a product-specific CLI group for any one application.

## Evidence Boundary

PHP2Shell risk must be split into two layers:

1. **Runtime exposure**: the HTTP SAPI uses an unfixed PHP version, or the multipart/upload-progress precondition is reachable. This supports upgrade and triage but does not prove command execution.
2. **End-to-end gadget**: the application also exposes an attacker-controlled `include`/file-inclusion path that includes a session file and executes PHP code inside it. The lab's `ls/cat` result proves this layer.

ChatBug does not send the OOM/UAF/crash payloads for CVE-2026-109618/109619. The remote lab reproduces the deterministic traditional PHP session upload-progress plus LFI chain using an exact/digest-pinned PHP-FPM runtime matching the assessed service.

## Chain Overview

```text
Unauthenticated multipart POST
  └─ PHP_SESSION_UPLOAD_PROGRESS makes PHP write request metadata to a session file
      └─ The filename field carries <?php ... system(fixed command) ... ?>
          └─ The application exposes include($user_controlled_path)
              └─ It includes /tmp/sess_<PHPSESSID>
                  └─ The lab returns delimited ls/cat output
```

Missing any condition weakens the conclusion:

- without an application LFI sink, only runtime/parser exposure is proven;
- `docker exec ... php` is management-plane execution, not unauthenticated exploitation;
- an ordinary PHP page reading a file does not prove that a remote attacker can execute commands.

## 1. Minimal Runnable Local Example

```bash
python -m pip install ChatBug
chatbug php2shell lab local-list
```

The command:

- starts an in-process HTTP lab bound to a temporary `127.0.0.1` port;
- sends an upload-progress multipart request;
- requests the synthetic include sink;
- requests the normal `hello.php` negative control;
- closes the socket/thread and clears in-memory state on exit.

Successful result shape:

```json
{
  "accepted": true,
  "positive_status": 200,
  "negative_status": 200,
  "positive_output": "/tmp\nchatbug-marker.txt\nCHATBUG_MARKER_EXAMPLE",
  "negative_body": "Hello World\n"
}
```

Acceptance conditions:

- `accepted=true`;
- positive output contains `/tmp`, `chatbug-marker.txt`, and the random marker;
- negative output contains only `Hello World`.

The local lab does not start a system shell or real PHP; it is a deterministic teaching/regression chain inside the package. CI can run:

```bash
python -m pytest -q tests/test_php2shell.py
```

## 2. Full PHP-FPM/Nginx Isolated Lab

On an owned Docker host:

```bash
chatbug php2shell lab docker-list \
  --ssh-host <owned-docker-host> \
  [--fpm-image <digest-pinned-php-fpm-image>] \
  --proof list-and-marker
```

ChatBug creates a unique temporary directory under the remote `$HOME/.chatarch/chatbug/labs/` and generates:

- a exact PHP-FPM image;
- Nginx proxying to PHP-FPM;
- `hello.php`, which returns only `Hello World`;
- `vuln.php`, which exists only in the lab and contains `include($_GET['page'])`;
- upload-progress/session settings;
- an internal-only Docker network;
- a one-shot Python client container.

It does not mount production databases, mail data, attachments, user directories, credentials, logs, or real session directories, and it publishes no host port.

## 3. Fixed Proof Modes

`--proof` does not accept arbitrary shell commands:

```text
list-tmp         -> ls -la /tmp
cat-marker       -> cat /tmp/chatbug-marker.txt
list-and-marker  -> ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt
```

The default `list-and-marker` provides both a directory listing and unique file content, showing that:

- the command executed inside the lab container;
- the response read server-side `/tmp/chatbug-marker.txt`, not a reflected request value.

## 4. Positive and Negative Acceptance

On success, `result.positive_output` contains content like:

```text
___START___
total 24
drwxrwxrwt 1 root root 4096 ... .
...
-rw-r--r-- 1 root root 32 ... chatbug-marker.txt
-rw------- 1 www-data www-data ... sess_lab...
MARKER
CHATBUG_MARKER_...
___END___
```

`result.negative_output` must be:

```text
Hello World
```

`accepted=true` requires all of the following:

- POST returns 200;
- the positive include sink returns 200;
- the negative normal page returns 200;
- positive output contains this run's random marker;
- negative output does not contain the marker;
- the Compose project and remote temporary directory are removed successfully.

## 5. Ordinary Production Website Check

For a live service, run only the safe check:

```bash
chatbug php2shell web check https://owned-service.example/
```

Result fields:

| Field | Meaning |
| --- | --- |
| `verdict=vulnerable_version_exposed` | The version banner is affected; upgrade/confirm the actual SAPI |
| `evidence_tier=tier_2_parser_reachable` | An ordinary multipart request reaches the parsing path |
| `evidence_tier=tier_3_gadget_found` | A fixed probe returned an independent marker, evidence of an include gadget |
| `rce_or_file_read_proven=false` | File read or RCE is not proven |

The command neither runs `ls/cat` in production nor sends memory-corruption payloads.

## 6. Follow-Up Remediation

1. Inventory every PHP SAPI serving real HTTP traffic: FPM, mod_php, FrankenPHP, LiteSpeed, etc. CLI versions are not Web-runtime evidence.
2. Upgrade to the official fixed release and read back the new version header, package version, or container digest.
3. Search for and remove unauthorized file-inclusion/path-construction sinks.
4. Tighten upload handling, session save paths, temporary-directory permissions, and error exposure.
5. Re-run `web check` after upgrade and rerun the positive/negative data-free lab.
6. If compromise is suspected, inspect access logs, abnormal sessions, webshells, child processes, and outbound connections separately; vulnerability validation does not replace forensics.
