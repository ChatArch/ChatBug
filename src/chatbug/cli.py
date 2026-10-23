"""ChatBug command line interface."""

from __future__ import annotations

import json
import secrets
import sys
from typing import Any

import click
from chatstyle import add_tree_option

from chatbug import __version__
from chatbug.lab import DEFAULT_PHP_FPM_IMAGE, LabSpec, logs, run_lfi_proof, seed_marker, start, stop
from chatbug.php2shell import build_lab_session_payload, extract_command_output, http_request
from chatbug.php2shell import random_marker, safe_url_check


def emit(payload: dict[str, Any]) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


@click.group(name="chatbug", invoke_without_command=True, no_args_is_help=True)
@click.version_option(__version__, prog_name="chatbug")
@add_tree_option(renderer_options={"root_name": "chatbug"})
def main() -> None:
    """Owned website vulnerability validation."""


@main.group(name="php2shell")
def php2shell() -> None:
    """PHP2Shell web checks and data-free lab proof."""


@php2shell.group(name="web")
def web() -> None:
    """Checks for an ordinary owned website URL."""


@web.command(name="check")
@click.argument("url")
@click.option("--skip-multipart", is_flag=True, help="Do not send the benign multipart request.")
@click.option("--skip-gadget-scan", is_flag=True, help="Do not probe common include parameter shapes.")
def web_check(url: str, skip_multipart: bool, skip_gadget_scan: bool) -> None:
    """Check version exposure, parser reachability, and common include gadgets."""

    result = safe_url_check(
        url,
        include_multipart=not skip_multipart,
        include_gadgets=not skip_gadget_scan,
    )
    emit(result)
    sys.exit(0 if result["verdict"] == "vulnerable_version_exposed" else 3)


@php2shell.group(name="lab")
def lab_group() -> None:
    """Disposable, data-free lab workflows."""


@lab_group.command(name="local-list")
def lab_local_list() -> None:
    """Run a complete positive/negative example in an in-process local lab."""

    import chatbug.local_lab as local_lab
    from chatbug.local_lab import serve_local_lab

    sid = "localtest" + secrets.token_hex(8)
    marker = random_marker()
    headers, body = build_lab_session_payload(sid, "list-and-marker")
    synthetic_output = f"___START___\n/tmp\nchatbug-marker.txt\n{marker}\n___END___"
    with serve_local_lab() as local:
        post_status, _, _ = http_request(f"{local.url}/hello.php", method="POST", headers=headers, data=body)
        local_lab.SESSIONS[sid] = synthetic_output
        positive_status, _, positive_body = http_request(
            f"{local.url}/vuln.php?page=/tmp/sessions/sess_{sid}",
            headers={"Cookie": f"PHPSESSID={sid}"},
        )
        negative_status, _, negative_body = http_request(
            f"{local.url}/hello.php?page=/tmp/sessions/sess_{sid}",
            headers={"Cookie": f"PHPSESSID={sid}"},
        )
    command_output = extract_command_output(positive_body) or ""
    result = {
        "schema": "chatbug.php2shell.local_lab/v1",
        "accepted": marker in command_output and marker not in negative_body.decode(),
        "post_status": post_status,
        "positive_status": positive_status,
        "negative_status": negative_status,
        "positive_output": command_output,
        "negative_body": negative_body.decode(),
        "boundary": "in-process lab; no Docker, shell, production network, or private data",
    }
    emit(result)
    sys.exit(0 if result["accepted"] else 1)


@lab_group.command(name="docker-list")
@click.option("--ssh-host", required=True, help="SSH alias for the owned Docker host.")
@click.option(
    "--fpm-image",
    default=DEFAULT_PHP_FPM_IMAGE,
    show_default=True,
    help="Digest-pinned or exact vulnerable PHP-FPM image to validate in isolation.",
)
@click.option(
    "--proof",
    type=click.Choice(["list-tmp", "cat-marker", "list-and-marker"], case_sensitive=False),
    default="list-and-marker",
    show_default=True,
)
@click.option("--keep", is_flag=True, help="Leave the disposable lab running for manual inspection.")
def lab_docker_list(ssh_host: str, fpm_image: str, proof: str, keep: bool) -> None:
    """Prove list/cat inside a data-free PHP-FPM lab with an intentional include sink."""

    spec = LabSpec(ssh_host=ssh_host, keep=keep, fpm_image=fpm_image)
    marker = random_marker()
    sid = "lab" + secrets.token_hex(10)
    report: dict[str, Any] = {
        "schema": "chatbug.php2shell.docker_lab/v1",
        "project": spec.project,
        "network": spec.network,
        "proof": proof,
        "fpm_image": fpm_image,
        "boundary": "internal Docker network; synthetic data only; no published host port; production untouched",
        "marker": marker,
    }
    remote_dir: str | None = None
    try:
        report["start"] = start(spec)
        remote_dir = report["start"]["remote_dir"]
        assert isinstance(remote_dir, str)
        report["seed"] = seed_marker(spec, remote_dir, marker)
        report["result"] = run_lfi_proof(spec, remote_dir, sid, proof)
        positive_output = report["result"]["positive_output"]
        negative_output = report["result"]["negative_output"]
        marker_expected = proof in {"cat-marker", "list-and-marker"}
        positive_evidence = (
            marker in positive_output
            if marker_expected
            else "chatbug-marker.txt" in positive_output
        )
        report["accepted"] = (
            report["result"]["positive_status"] == 200
            and report["result"]["negative_status"] == 200
            and positive_evidence
            and marker not in negative_output
        )
        report["interpretation"] = "Runtime plus intentional lab-only include gadget proven."
    except Exception as exc:
        report["accepted"] = False
        report["error"] = str(exc)
        if remote_dir:
            report["logs"] = logs(spec, remote_dir)
        emit(report)
        sys.exit(1)
    finally:
        if not keep and remote_dir:
            report["cleanup"] = stop(spec, remote_dir)
    emit(report)
    sys.exit(0 if report.get("accepted") else 1)


if __name__ == "__main__":
    main()
