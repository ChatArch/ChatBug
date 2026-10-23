# ChatBug

ChatBug is a ChatArch package for authorized website vulnerability validation. Its current PHP2Shell workflow separates Web-runtime version exposure, ordinary multipart parser reachability, and application file-inclusion gadgets, then performs fixed `ls/cat` acceptance only in a disposable PHP-FPM lab with no production data.

It is not a general-purpose attack framework: it sends no OOM/UAF/crash payloads, reads no production mail/attachments/sessions, provides no reverse shell, and accepts no arbitrary remote command.

Documentation: <https://arch.gh.wzhecnu.cn/ChatBug/en/>

## Quick Start

First run a low-impact runtime check against a website you own or are explicitly authorized to assess:

```bash
python -m pip install ChatBug
chatbug php2shell web check https://owned-site.example/ --skip-gadget-scan
```

Then run the Docker-free local protocol/regression case:

```bash
chatbug php2shell lab local-list
```

For real PHP-FPM `ls/cat` acceptance, create an internal one-off lab on an owned SSH Docker host:

```bash
chatbug php2shell lab docker-list \
  --ssh-host <owned-docker-host> \
  --fpm-image <exact-runtime-image-or-digest> \
  --proof list-and-marker
```

The default `--fpm-image` is `php:8.1.34-fpm-alpine` for convenient reproduction. For exact runtime parity, pass the assessed service's pinned image digest; never attach or copy production volumes.

## Capabilities and Boundaries

| Command | Target | Request/execution scope | Evidence boundary |
| --- | --- | --- | --- |
| `web check <URL> --skip-gadget-scan` | Owned website | HEAD plus ordinary multipart parser request | Version/entry-point exposure, not RCE |
| `web check <URL>` | Owned website | Adds fixed session/include marker probe | Controlled PHP `echo` marker lead, not system-command proof |
| `lab local-list` | Local in-process HTTP lab | Synthetic positive/negative response | HTTP/payload contract regression; no PHP or shell |
| `lab docker-list` | Owned Docker host | Internal PHP-FPM/Nginx one-off lab | Fixed `ls/cat` succeeds only with runtime + lab-only include gadget |

`docker-list` demonstrates the deterministic PHP `session upload-progress + include` chain: the lab writes request metadata to a session file and a lab-only `include($_GET['page'])` sink includes it. This shows that a matching PHP-FPM runtime plus an explicitly present application gadget can reach fixed command output. It does not independently prove memory-corruption RCE for CVE-2026-109618/109619, nor that a real application has the same gadget.

## Live-Check Safety

`web check` is only for a target you own or are explicitly authorized to test. Its options have different effects:

- `--skip-multipart`: read HTTP/version headers only; send no multipart request.
- `--skip-gadget-scan`: retain the ordinary multipart parser check but do not request common session-file include shapes.
- No skip flags: sends a fixed PHP `echo` marker filename with no system command, then checks a small fixed set of candidate session/include paths for that marker.

The final probe does not call `system()`, send an OOM/UAF payload, or read a production marker/user file. If an LFI gadget exists, however, it can cause that controlled `echo` to execute in the target PHP process and create ordinary request/session logs. Run it only within authorized scope and an appropriate maintenance window; do not call it side-effect-free scanning.

`rce_or_file_read_proven=true` is a compatibility field name. In the current live check, it means only that an independent marker returned through a fixed candidate session/include path. It does **not** mean arbitrary system-command RCE, real user-file disclosure, or production PHP2Shell exploitation. Command-output acceptance is available only in the isolated `docker-list` lab.

## Evidence Tiers

ChatBug never upgrades weak evidence into a stronger conclusion:

1. **Version/config exposure**: runtime banner or configuration precondition.
2. **Parser reachability**: ordinary multipart traffic reaches the request path.
3. **Controlled marker**: a fixed session/include probe returns an independent marker.
4. **Isolated chain success**: a data-free lab returns fixed `ls/cat` output.
5. **Production memory-vulnerability exploitation**: never automated by ChatBug; requires separate risk authorization and dedicated research.

For production services containing user data, such as mail or documents, do not send memory-corruption, OOM, crash, or repeated exploit traffic. Validate the same image in a data-free lab first, then plan remediation and forensics separately.

## Install and Verify

```bash
python -m pip install ChatBug
chatbug --version
chatbug --tree
chatbug --tree-brief
chatbug php2shell lab local-list
```

Development:

```bash
python -m pip install -e ".[dev,docs]"
python -m pytest -q
mkdocs build --strict
```

## Documentation

- [CLI Tree](docs/cli-tree.en.md)
- [Capability Map](docs/capability-map.en.md)
- [Python Interface Tree](docs/interface-tree.en.md)
- [PHP2Shell Isolated Reproduction Lab](docs/php2shell-lab.en.md)

## Development

Read `DEVELOP.md` and `AGENTS.md` before extending the package. Any experiment beyond the fixed lab proofs must first be designed as an isolated, cleanable lab with positive and negative acceptance—not an arbitrary remote-command interface.
