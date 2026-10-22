<div align="center">
    <a href="https://pypi.python.org/pypi/ChatBug">
        <img src="https://img.shields.io/pypi/v/ChatBug.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatBug/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatBug/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://arch.gh.wzhecnu.cn/ChatBug/">
        <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatBug

ChatBug is a reserved ChatArch Python package. It currently exposes only version, help, and CLI-tree commands; it does not yet implement vulnerability scanning, PHP2Shell validation, or production-service operations.


Documentation entry: <https://arch.gh.wzhecnu.cn/ChatBug/en/>

Choose documentation by scenario:

| Scenario | Document |
| --- | --- |
| Install the package, run the CLI, and confirm it works | `docs/cli-tree.en.md` |
| Check first-class capabilities and current boundaries | `docs/capability-map.en.md` |
| Call package behavior directly from Python | `docs/interface-tree.md` |

## Quick Start

```bash
pip install -e ".[dev]"
chatbug --help
chatbug --version
chatbug --tree
chatbug --tree-brief
python -m pytest -q
python -m build
```

## CLI Contract

This template depends on `chatstyle>=0.2.0,<0.3.0` and `chatenv>=0.2.11,<0.3.0`. New commands should prefer:

- `add_tree_option()` for shared `--tree` / `--tree-brief` flags and `render_click_tree()` to render registered Click metadata.
- `CommandSchema` / `CommandField` for inputs.
- `add_interactive_option()` for the shared `-i/-I` switch.
- `resolve_command_inputs()` for missing args, defaults, TTY behavior, and validation.
- ChatBug has no configuration fields or ChatEnv provider yet. Add integration when configuration behavior is defined.

## Layout

- `src/`: package source code
- `tests/code-tests/`: code tests and migrated historical tests
- `tests/cli-tests/`: real CLI tests, doc-first
- `tests/mock-cli-tests/`: mock/fake CLI tests, doc-first
- `docs/`: long-lived project docs built by mkdocs

## Development Notes

See `DEVELOP.md` and `AGENTS.md` before expanding the scaffold.
