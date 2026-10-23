# ChatBug

ChatBug is an authorized website vulnerability-validation package from the ChatArch series. Its first capability focuses on **PHP2Shell**: run non-destructive version/entry-point checks against an ordinary website you own, then reproduce the complete chain “vulnerable runtime + LFI include gadget → session upload-progress injection → `ls/cat` output” in a disposable, data-free lab.

It is not a general-purpose attack framework: it does not send OOM/UAF crash payloads, execute commands against production, provide reverse shells, or accept arbitrary remote command arguments.

Documentation: <https://arch.gh.wzhecnu.cn/ChatBug/en/>

## Use Cases

- Determine whether an owned PHP website exposes an affected runtime version.
- Confirm upload parser reachability with an ordinary multipart request.
- Probe a small fixed set of common include parameter shapes with a controlled marker.
- Run repeatable `ls -la /tmp` / `cat /tmp/chatbug-marker.txt` acceptance in an in-process or one-off remote Docker lab.
- Emit auditable JSON that separates version exposure, parser reachability, isolated chain success, and unproven production exploitation.

## Safety Boundary

| Command | Target | Executes commands? | Touches production data? |
| --- | --- | --- | --- |
| `chatbug php2shell web check <URL>` | An ordinary owned website URL | No | No; HEAD, benign multipart, and fixed gadget probes only |
| `chatbug php2shell lab local-list` | Temporary local in-process HTTP lab | No system shell | No; synthetic data only |
| `chatbug php2shell lab docker-list` | Remote one-off internal Docker lab | Fixed allowlisted lab commands only | No; no production volumes, no published port, synthetic marker |

`docker-list` demonstrates the traditional, deterministic PHP `include` chain: `PHP_SESSION_UPLOAD_PROGRESS` writes attacker-controlled data to a session file, and a lab-only `include($_GET['page'])` sink includes that file. It proves that a vulnerable PHP-FPM runtime plus an application LFI gadget can reach `ls/cat`; it does **not**, by itself, prove memory-corruption RCE for CVE-2026-109618/109619.

## Install

```bash
python -m pip install ChatBug
chatbug --version
chatbug --tree
```

Development:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Quick Reproducible Test Case

No Docker, root, or network is required:

```bash
chatbug php2shell lab local-list
```

A successful JSON result contains:

- `accepted: true`
- `positive_status: 200`
- `negative_status: 200`
- `positive_output` containing `/tmp`, `chatbug-marker.txt`, and a random marker
- `negative_body` containing only `Hello World`, showing that the normal safe endpoint does not execute the session file as PHP

The same path is covered by tests:

```bash
python -m pytest -q tests/test_php2shell.py
```

## Full Isolated Reproduction: PHP-FPM + Nginx

You need an owned SSH host with Docker. The command:

1. uses a exact PHP-FPM image as the runtime;
2. generates a temporary webroot containing only `Hello World` and a lab-only `include` sink;
3. creates an internal Docker network and publishes no host port;
4. writes a random synthetic marker to the lab container's `/tmp/chatbug-marker.txt`;
5. sends a session upload-progress request from a one-shot client on the same internal network;
6. returns `ls/cat` output through the lab-only LFI sink in the positive request;
7. returns only `Hello World` from normal `hello.php` in the negative request;
8. removes containers, network, and the remote temporary directory.

```bash
chatbug php2shell lab docker-list \
  --ssh-host <your-ssh-host> \
  [--fpm-image <digest-pinned-php-fpm-image>] \
  --proof list-and-marker
```

`--proof` is restricted to three fixed modes:

- `list-tmp`: run lab-only `ls -la /tmp`;
- `cat-marker`: read the lab-only synthetic marker file;
- `list-and-marker`: list the directory and read the marker (default).

The accepted positive output contains the lab `/tmp` listing, `sess_<id>`, `MARKER`, and the random marker; the negative output must remain `Hello World`.

## Check an Ordinary Owned Website

```bash
chatbug php2shell web check https://example-owned-site.example/
```

Output interpretation:

- `verdict=vulnerable_version_exposed`: the version banner is in the affected range; this is exposure, not RCE;
- `evidence_tier=tier_2_parser_reachable`: an ordinary multipart parser is reachable;
- `evidence_tier=tier_3_gadget_found`: a fixed probe returned an independent marker server-side;
- `rce_or_file_read_proven=true`: accepted only when marker return cannot be explained by request reflection and comes from a server-side session-file include.

Skip the heavier gadget scan if needed:

```bash
chatbug php2shell web check https://example-owned-site.example/ --skip-gadget-scan
```

## Evidence Tiers

ChatBug never upgrades weak evidence into a strong conclusion:

1. version/config exposure;
2. primitive or precondition reachability;
3. marker/command-output acceptance in a disposable lab;
4. production validation under separate explicit risk authorization;
5. third-party compromise indicators.

For production services that handle real user data, such as mail or documents, do not send memory-corruption, OOM, crash, or repeated exploit traffic. Use a same-image, data-free lab first.

## Documentation

- [CLI Tree](docs/cli-tree.md)
- [Capability Map](docs/capability-map.md)
- [Python Interface Tree](docs/interface-tree.md)
- [PHP2Shell Reproduction Lab](docs/php2shell-lab.md)

## Development

Read `DEVELOP.md` and `AGENTS.md` before extending the package. New production checks must remain non-destructive. Capabilities beyond the fixed lab commands should be implemented as isolated, cleanable labs rather than arbitrary remote-command interfaces.
