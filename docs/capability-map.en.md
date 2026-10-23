# Capability Map

ChatBug owns one narrow, auditable capability: assessing PHP2Shell risk for PHP websites under explicit authorization. It keeps runtime exposure, controlled marker leads, isolated lab command acceptance, and production memory-vulnerability exploitation separate.

## First-Class Capabilities

<div class="grid cards" markdown>

- **Ordinary website runtime checks**

    `chatbug php2shell web check <URL>` starts from an ordinary Web URL rather than a product-specific webmail/CMS CLI group. It reads PHP version exposure, verifies multipart parsing, and can optionally run a fixed session/include marker probe.

- **Local contract lab**

    `chatbug php2shell lab local-list` uses an in-process HTTP server to lock the positive/negative protocol contract. It starts no PHP, Docker, or shell.

- **Full-runtime Docker lab**

    `chatbug php2shell lab docker-list` creates an internal-only, disposable PHP-FPM/Nginx environment with no production data on an owned Docker host. It is the only location where fixed `ls/cat` proof actions run.

- **Importable Python API**

    The CLI only handles arguments and JSON output. Version classification, HTTP requests, marker structure, lab files, and cleanup lifecycle are independently importable and testable.

</div>

## Capability Status

| Capability | Status | Evidence boundary |
| --- | --- | --- |
| PHP version-header parsing and fixed-release classification | Implemented and verified | Proves version/config exposure, not exploitability |
| Ordinary multipart parser check | Implemented and verified | Proves a request reaches the upload-parser path, not file inclusion or command execution |
| Fixed session/include marker probe | Implemented and verified | Marker return is a candidate-path lead requiring review; it does not prove arbitrary system command or user-file disclosure |
| Local LFI/session contract lab | Implemented and verified | Synthetic teaching/regression chain; no real PHP, shell, or memory-corruption payload |
| Remote PHP-FPM Docker lab | Implemented and verified | Proves fixed `ls/cat` output only with a selected runtime plus intentionally added lab-only include gadget |
| CVE-2026-109618/109619 memory-corruption RCE | Not provided | No OOM/UAF payload; requires separate risk authorization and dedicated research |
| Production memory-vulnerability exploitation | Not provided by default | Live services with real data receive low-impact checks only; no automatic exploitation |
| Arbitrary-command framework / reverse shell | Not provided | `docker-list` accepts exactly three fixed proof values |

## How a Real Service Maps to the Product

A real PHP webmail risk assessment is still two independent questions:

1. Treat it as an ordinary PHP website for `web check`, identifying the version and entry point exposed by the actual HTTP SAPI; service type does not warrant a Mail-specific CLI.
2. When `ls/cat`-level acceptance is needed, run `docker-list` with `--fpm-image` set to a matching runtime in a data-free Docker lab. The lab mounts only a synthetic webroot and random marker, never real mailboxes, databases, attachments, or user directories.

“Mail service” affects the lab image selection and risk level; it does not change the generic CLI model.

## Safety Constraints

- Every remote check must target an owned or explicitly authorized service.
- Production checks send no OOM, UAF, crash payload, brute-force repetition, or arbitrary system command.
- `web check` without `--skip-gadget-scan` can trigger a controlled PHP `echo` marker where an LFI exists; confirm authorization and an appropriate logging/maintenance window first.
- The marker never appears in the validation URL, query, or traversal string, preventing input-reflection false positives.
- Docker labs use an internal network, unique Compose project, synthetic data, and automatic cleanup; `--keep` is for short manual inspection only.
- Reports must distinguish “runtime only,” “controlled marker path,” and “runtime + lab gadget.”

## Out of Scope

- Internet-wide or unauthorized scanning.
- Reading real user mail, sessions, attachments, secrets, or production temporary files.
- Restarting, patching, taking offline, or reconfiguring production.
- Hiding a version banner and calling a service patched; remediation must be proven by the actual runtime version and released artifacts.
- Misreporting scanner output, `docker exec` management-plane operation, ordinary PHP page execution, or marker reflection as unauthenticated RCE.
