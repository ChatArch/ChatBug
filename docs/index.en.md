# ChatBug Docs

ChatBug is an authorized website vulnerability-validation package from the ChatArch series. Its first capability focuses on PHP2Shell: safe exposure checks for ordinary owned websites, plus a disposable data-free lab that reproduces the complete acceptance chain “runtime + LFI gadget → session upload-progress injection → `ls/cat` output”.

Site entry: <https://arch.gh.wzhecnu.cn/ChatBug/en/>

## Choose Documentation by Scenario

| Scenario | Document |
| --- | --- |
| View complete commands, options, and exit codes | [CLI Tree](cli-tree.md) |
| Understand capability status, evidence tiers, and safety boundaries | [Capability Map](capability-map.md) |
| Call checks or lab APIs from Python | [Python Interface Tree](interface-tree.md) |
| Run the local or PHP-FPM/Nginx isolated reproduction lab | [PHP2Shell Reproduction Lab](php2shell-lab.md) |

## Quick Start

```bash
python -m pip install ChatBug
chatbug --tree
chatbug php2shell lab local-list
```

`local-list` requires no Docker, root, network, or real shell. It validates the positive include sink and negative normal entry with an in-process HTTP lab.

## Core Conclusions

- `web check <URL>` is a non-destructive owned-website check. Version exposure, multipart reachability, and fixed gadget probes are reported as separate evidence tiers.
- `lab local-list` is a deterministic local teaching/CI example.
- `lab docker-list --ssh-host <host>` proves fixed `ls/cat` actions with an exact/digest-pinned PHP-FPM runtime in an internal-only Docker lab; it mounts no production data and publishes no port.
- ChatBug does not send OOM/UAF/crash payloads, provide arbitrary commands or reverse shells, or describe version exposure as RCE.

## Documentation Status

- **Implemented**: code, tests, and CLI paths exist.
- **Verified**: covered by local tests, CI, or a disposable isolated lab.
- **Not provided**: explicitly outside the safety boundary, such as production memory-corruption exploitation or an arbitrary-command framework.

## Local Development Preview

```bash
python -m pip install -e ".[dev,docs]"
python -m pytest -q
mkdocs serve
```

The Chinese entry is <https://arch.gh.wzhecnu.cn/ChatBug/>. Topic pages without English translations fall back through i18n to the default language.
