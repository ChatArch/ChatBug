# CLI Tree

`ChatBug` is an authorized vulnerability-validation CLI. The tree below is maintained from the real registered Click surface; before release, run `chatbug --tree` to verify the documented contract.

## Real Command Tree

```text
chatbug
├── --help                                                                 # Show this message and exit.
├── --version                                                              # Show the version and exit.
├── --tree                                                                 # Print the registered CLI tree and exit.
├── --tree-brief                                                           # Print the registered CLI tree without parameter signatures and exit.
└── php2shell                                                              # PHP2Shell web checks and data-free lab proof.
    ├── lab                                                                # Disposable, data-free lab workflows.
    │   ├── docker-list --ssh-host TEXT --fpm-image TEXT --proof [list-tmp|cat-marker|list-and-marker] [--keep]  # Prove list/cat inside a data-free PHP-FPM lab with an intentional include sink.
    │   └── local-list                                                     # Run a complete positive/negative example in an in-process local lab.
    └── web                                                                # Checks for an ordinary owned website URL.
        └── check <URL> [--skip-multipart] [--skip-gadget-scan]            # Check version exposure, parser reachability, and common include gadgets.
```

## Commands

### `chatbug php2shell web check <URL>`

Runs non-destructive checks against a website that you own or are explicitly authorized to test:

1. reads the PHP version from `Server` / `X-Powered-By` and classifies it against fixed releases;
2. sends an ordinary multipart POST to prove upload-parser reachability;
3. probes a small fixed set of common `page/file/include/path` parameter shapes for an independent marker;
4. emits JSON without sending OOM/UAF/crash payloads or executing system commands on the target.

Exit codes:

- `0`: the version banner indicates an affected range;
- `3`: checks completed, but an affected version was not proven or the version banner is hidden;
- other non-zero codes: request or local execution errors.

Options:

- `--skip-multipart`: perform only version/HTTP checks;
- `--skip-gadget-scan`: skip common include-gadget probes and keep only version and parser-reachability evidence.

### `chatbug php2shell lab local-list`

Starts a temporary in-process HTTP lab and runs both positive and negative controls:

- positive: the synthetic LFI include sink reads session upload-progress content and returns `/tmp`, `chatbug-marker.txt`, and a random marker;
- negative: normal `hello.php`, even with the same path parameter, returns only `Hello World`;
- no Docker, root, network, or real shell is required. This command is suitable for CI, documentation, and first reproduction.

### `chatbug php2shell lab docker-list --ssh-host <host> [--fpm-image <image>]`

Creates a one-off full-runtime lab on an owned SSH host with Docker:

- exact PHP-FPM image plus Nginx;
- internal Docker network with no published host port;
- temporary webroot containing only `Hello World` and a lab-only `include($_GET['page'])`;
- only synthetic files are mounted; no production database, mail, user directory, credentials, logs, or attachments are attached;
- the Compose project, network, and remote temporary directory are removed automatically.

`--proof` is a fixed allowlist and never accepts arbitrary commands:

| proof | Fixed lab action | Acceptance |
| --- | --- | --- |
| `list-tmp` | `ls -la /tmp` | Returns the lab temporary-directory listing |
| `cat-marker` | `cat /tmp/chatbug-marker.txt` | Returns a random synthetic marker |
| `list-and-marker` | `ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt` | Returns the listing, `MARKER`, and random marker |

`--keep` is only for manual inspection. A retained lab still has no public/host-published port.

## Evidence Interpretation

- Version exposure sets remediation priority but is not RCE.
- Multipart HTTP 200 only proves parser reachability.
- `local-list` proves the deterministic LFI/session-injection teaching chain inside the package.
- `docker-list` proves that, on the same PHP-FPM runtime with an intentionally added lab gadget, file inclusion can reach fixed `ls/cat` actions.
- Without a separate application LFI gadget, a memory-corruption CVE must not be described as “production RCE reproduced”.
