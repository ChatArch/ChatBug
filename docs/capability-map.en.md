# Capability Map

ChatBug currently owns one narrow, acceptance-driven security capability: validating PHP2Shell risk for PHP websites under explicit authorization. It keeps version exposure separate from end-to-end command/file-read proof.

## First-Class Capabilities

<div class="grid cards" markdown>

- **Ordinary website checks**

    `chatbug php2shell web check <URL>` treats an ordinary owned website as a website; there is no Mail-specific CLI group. It checks PHP version exposure, multipart parser reachability, and fixed common LFI parameter shapes.

- **Local repeatable lab**

    `chatbug php2shell lab local-list` starts an in-process HTTP lab without Docker, root, or a system shell, demonstrating the session upload-progress plus include-gadget chain with positive and negative controls.

- **Full isolated runtime lab**

    `chatbug php2shell lab docker-list` creates an internal-only, one-off, data-free PHP-FPM/Nginx lab on an owned Docker host and accepts fixed `ls/cat` proof modes.

- **Importable Python API**

    The CLI stays thin. Version classification, HTTP checks, payload construction, and lab lifecycle are importable and independently tested.

</div>

## Capability Status

| Capability | Status | Evidence boundary |
| --- | --- | --- |
| PHP version-header parsing and fixed-release classification | Implemented and verified | Proves version/config exposure only, not exploitability |
| Ordinary multipart parser reachability check | Implemented and verified | Proves only that a request reaches the upload-progress path |
| Fixed common LFI marker probe | Implemented and verified | File read is proven only when an independent marker is returned server-side |
| Local LFI/session-injection lab | Implemented and verified | Deterministic teaching chain; no real shell or memory-corruption simulation |
| Remote same-runtime Docker lab | Implemented and verified | Proves fixed `ls/cat` when the vulnerable runtime has an intentionally added application LFI gadget |
| CVE-2026-109618/109619 memory-corruption RCE exploit | Not implemented | No OOM/UAF payload; requires separate authorization and dedicated exploitation research |
| Production exploitation test | Not provided by default | Production contains real data; use safe checks by default |
| Arbitrary-command framework / reverse shell | Not provided | `docker-list` accepts only three fixed proof values |

## How the Real-World Example Maps to the Product

A real PHP webmail risk assessment splits into two layers:

1. Treat the service as an ordinary PHP website for `web check`: identify the PHP version and multipart entry exposed by the actual HTTP SAPI. The service type does not justify a separate mail command.
2. When `ls/cat`-level acceptance is needed, run `docker-list` with `--fpm-image` set to the same-runtime image. The lab mounts a synthetic webroot and random marker; it never connects to real mailboxes, databases, or attachment volumes.

“Mail service” affects the runtime image selected for the lab; it does not change the generic CLI model.

## Safety Constraints

- Every remote check must target an owned or explicitly authorized service.
- Production checks default to no OOM, UAF, crash, brute-force repetition, or arbitrary command.
- The file-read marker is not placed in the validation URL, query, or traversal string, preventing input-reflection false positives.
- Both controls must pass: the include sink returns the marker, while the normal safe endpoint returns only `Hello World`.
- Docker labs use an internal network, unique Compose project, synthetic data, and automatic cleanup; `--keep` is for short manual inspection only.
- Reports must distinguish “runtime only” from “runtime + gadget”.

## Out of Scope

- Scanning the internet or unauthorized hosts.
- Reading real user mail, sessions, attachments, secrets, or production temporary files.
- Restarting, patching, taking offline, or reconfiguring production.
- Hiding a version banner and calling it patched; remediation must be verified by runtime version and released artifacts.
- Treating scanner output, `docker exec` management-plane execution, or ordinary PHP page execution as unauthenticated RCE.
