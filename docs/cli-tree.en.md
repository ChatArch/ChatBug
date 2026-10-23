# CLI Tree

The tree below comes from ChatBug 0.1.0's registered Click surface. After installation, use `chatbug --tree` to read back the installed contract; this page describes implemented commands only.

## Registered Command Tree

```text
chatbug
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
└── php2shell  # PHP2Shell web checks and data-free lab proof.
    ├── lab  # Disposable, data-free lab workflows.
    │   ├── docker-list [--ssh-host SSH-HOST] [--fpm-image FPM-IMAGE] [--proof PROOF] [--keep]  # Prove list/cat inside a data-free PHP-FPM lab with an intentional include sink.
    │   └── local-list  # Run a complete positive/negative example in an in-process local lab.
    └── web  # Checks for an ordinary owned website URL.
        └── check <URL> [--skip-multipart] [--skip-gadget-scan]  # Check version exposure, parser reachability, and common include gadgets.
```

## `chatbug php2shell web check <URL>` {#chatbug-php2shell-web-check-url}

Run this only against a website you own or are explicitly authorized to test. It emits JSON, sends no OOM/UAF/crash payload, and does not invoke a system command on the target.

| Invocation | Actual requests | Evidence boundary |
| --- | --- | --- |
| `web check <URL> --skip-multipart` | HEAD/version headers only | HTTP/version visibility only |
| `web check <URL> --skip-gadget-scan` | HEAD plus ordinary multipart | Parser reachability; no session-include request |
| `web check <URL>` | Above requests plus a fixed session/include marker probe | Controlled PHP `echo` marker lead, not a `system()`/RCE proof |

The default marker probe sends only a fixed `<?php echo '<random marker>'; ?>` filename, then checks a small fixed set of `page`, `file`, `include`, and `path` shapes against candidate session locations. It requests no real user file and contains no `system()` call. If the application has an LFI gadget, it can still execute that controlled `echo` in the target PHP process and create ordinary request/session logs.

Use the no-skip form only within authorized scope and an appropriate maintenance window. For low-impact inventory, prefer `--skip-gadget-scan`.

Exit codes:

- `0`: the version banner indicates an affected range;
- `3`: the check completed, but an affected version was not proven or the version header is hidden;
- other non-zero values: local argument or request-processing error.

Important fields:

- `verdict=vulnerable_version_exposed`: version exposure, not production RCE;
- `evidence_tier=tier_2_parser_reachable`: ordinary multipart traffic reached the parser path;
- `evidence_tier=tier_3_gadget_found`: the fixed marker returned through a candidate include path;
- `rce_or_file_read_proven=true`: a compatibility field name; it currently means only that the controlled marker path worked, not arbitrary command execution, user-data reading, or memory-vulnerability exploitation.

## `chatbug php2shell lab local-list`

The local contract lab is for CI, documentation, and regression:

- binds a temporary `127.0.0.1` HTTP endpoint in the current process;
- simulates the upload-progress/session and lab-only include-sink positive response;
- uses ordinary `hello.php` as the negative control;
- emits synthetic `/tmp`, `chatbug-marker.txt`, and random-marker output;
- closes the socket/thread and clears in-memory state on exit.

It starts no PHP, Docker, or system shell, so it is not evidence of real PHP command execution. Use the Docker lab for actual PHP-FPM acceptance.

## `chatbug php2shell lab docker-list` {#chatbug-php2shell-lab-docker-list}

This command requires `--ssh-host` and is only for an owned Docker host. It creates a unique Compose project, internal Docker network, and temporary synthetic webroot. It publishes no host port and mounts no production database, mail, attachment, user-directory, credential, or log volume.

```bash
chatbug php2shell lab docker-list \
  --ssh-host <owned-docker-host> \
  --fpm-image <exact-runtime-image-or-digest> \
  --proof list-and-marker
```

- The default image is `php:8.1.34-fpm-alpine` for workflow validation.
- For parity with an assessed service, pass its exact PHP-FPM image digest.
- `--keep` retains the temporary lab for SSH inspection; otherwise containers, network, and remote temporary directory are removed.

`--proof` is a fixed allowlist and never accepts arbitrary commands:

| proof | Fixed lab action | Positive acceptance |
| --- | --- | --- |
| `list-tmp` | `ls -la /tmp` | Lists the synthetic `chatbug-marker.txt` in the temporary directory |
| `cat-marker` | `cat /tmp/chatbug-marker.txt` | Returns this run's random marker |
| `list-and-marker` | `ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt` | Returns listing, `MARKER`, and random marker |

`docker-list` returns `accepted=true` only when positive/negative HTTP statuses are 200, the proof-specific positive evidence appears, the negative `hello.php` response contains no marker, and default cleanup completes. It proves that the selected PHP-FPM runtime plus an intentionally added lab include gadget reaches fixed command output; it does not show that a real application or a PHP2Shell memory vulnerability was exploited.

## Choose a Command

| Goal | Recommended command |
| --- | --- |
| Confirm version exposure only | `web check <URL> --skip-multipart` |
| Confirm ordinary multipart entry point | `web check <URL> --skip-gadget-scan` |
| Check a fixed marker/include lead within authorized scope | `web check <URL>` |
| Run a stable Docker-free regression | `lab local-list` |
| Accept fixed PHP-FPM-lab `ls/cat` output | `lab docker-list --ssh-host ... --proof list-and-marker` |
