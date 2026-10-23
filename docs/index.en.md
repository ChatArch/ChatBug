# ChatBug Docs

ChatBug is a ChatArch package for authorized website vulnerability validation. It separates PHP2Shell risk into auditable evidence tiers: Web-runtime version/entry-point exposure, a controlled session/include marker, and fixed `ls/cat` acceptance performed only in a lab with no production data.

Site entry: <https://arch.gh.wzhecnu.cn/ChatBug/en/>

## Choose a Path

| Goal | Start here |
| --- | --- |
| Confirm runtime exposure without gadget requests | [CLI Tree: low-impact `web check`](cli-tree.md#chatbug-php2shell-web-check-url) |
| Understand marker-probe effects and evidence boundaries | [Capability Map](capability-map.md) |
| Run a local, runnable regression example | [PHP2Shell Lab: local contract lab](php2shell-lab.md#local-contract-lab) |
| Obtain `ls/cat` acceptance in a matching PHP-FPM runtime | [PHP2Shell Lab: Docker runtime lab](php2shell-lab.md#docker-runtime-lab) |
| Call checks or lab lifecycle APIs from Python | [Python Interface Tree](interface-tree.md) |

## Recommended Route

<div class="grid cards" markdown>

- **Start with a low-impact check**

    Run `web check --skip-gadget-scan` against an owned or authorized URL. It reports version and multipart-parser reachability without asserting command execution.

    [Read the check boundary](cli-tree.md#chatbug-php2shell-web-check-url)

- **Interpret marker results precisely**

    Default `web check` adds a fixed session/include marker probe. Marker return is a controlled PHP `echo` lead, not a system-command RCE conclusion.

    [Read the evidence tiers](capability-map.md#capability-status)

- **Use the local contract lab for regression**

    `local-list` starts no PHP, Docker, or shell. It locks the request/response and positive/negative-control contract.

    [Run the local example](php2shell-lab.md#local-contract-lab)

- **Accept command output only in the isolated Docker lab**

    `docker-list` uses an internal network, synthetic marker, fixed proof allowlist, and automatic cleanup. It is the only path that returns `ls/cat` output.

    [Run the Docker lab](php2shell-lab.md#docker-runtime-lab)

</div>

## Current Conclusions

- Version headers and parser reachability are patch-priority evidence, not production RCE.
- A session/include marker return needs authorization-aware review of the application and logs; it does not show arbitrary system-command execution.
- `docker-list` can prove fixed command output in a matching runtime with an intentionally added lab-only include gadget. It does not replace an audit for a real application gadget.
- ChatBug sends no OOM/UAF/crash payload, reads no production user data, and does not automate production memory-vulnerability exploitation.

## Local Development Preview

```bash
python -m pip install -e ".[dev,docs]"
python -m pytest -q
mkdocs build --strict
mkdocs serve
```

The Chinese entry is <https://arch.gh.wzhecnu.cn/ChatBug/>. Every core page has an English mirror; use the language selector at the top of a page to switch languages.
